"""Workflow instance endpoints."""

import json

import yaml
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user, get_db
from api.schemas import ActionRequest, WorkflowCreateRequest, WorkflowInstanceResponse
from approv.db import DatabaseManager
from approv.engine import WorkflowEngine
from approv.form_spec import FormSpecBuilder
from approv.models import UserContext
from approv.validation import ValidationService

router = APIRouter()


def _load_instance(db: DatabaseManager, instance_id: int) -> dict:
    """Load workflow instance and its definition."""
    instance = db.execute_read_one(
        """SELECT wi.*, wd.name as wf_def_name, wd.workflow_yaml, wd.form_yaml, wd.seed_data_json
           FROM workflow_instances wi
           JOIN workflow_definitions wd ON wi.wf_def_id = wd.wf_def_id
           WHERE wi.instance_id = ?""",
        (instance_id,),
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    return instance


def _load_audit_trail(db: DatabaseManager, instance_id: int) -> list[dict]:
    return db.execute_read(
        """SELECT status, action, description, created_at as timestamp,
                  COALESCE((SELECT username FROM users WHERE user_id = at.user_id), 'system') as user,
                  role_name as role
           FROM audit_trail at WHERE instance_id = ? ORDER BY audit_id""",
        (instance_id,),
    )


@router.post("/", response_model=WorkflowInstanceResponse)
def start_workflow(
    req: WorkflowCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    # Load workflow definition
    wf_def = db.execute_read_one(
        "SELECT * FROM workflow_definitions WHERE wf_def_id = ? AND is_active = 1",
        (req.wf_def_id,),
    )
    if not wf_def:
        raise HTTPException(status_code=404, detail="Workflow definition not found")

    workflow_config = yaml.safe_load(wf_def["workflow_yaml"])
    form_config = yaml.safe_load(wf_def["form_yaml"])
    seed_data = json.loads(wf_def["seed_data_json"]) if wf_def["seed_data_json"] else {}

    # Create instance
    instance_id = db.execute_write(
        """INSERT INTO workflow_instances (wf_def_id, current_status, form_data, started_by, assigned_role)
           VALUES (?, 'start', ?, ?, ?)""",
        (req.wf_def_id, json.dumps(seed_data), current_user.user_id, None),
    )

    # Run engine to initiate and auto-advance through non-user-action steps
    engine = WorkflowEngine(workflow_config, form_config, seed_data, [], "start")
    engine.initiate(current_user.username, current_user.roles[0] if current_user.roles else "")

    # Auto-advance through steps that don't require user action
    while True:
        step_config = workflow_config["workflow"].get(engine.current_status, {})
        if step_config.get("require_user_action", False) or engine.current_status == "stop":
            break
        from approv.steps import STEP_REGISTRY
        step_cls = STEP_REGISTRY.get(step_config["class"])
        if not step_cls:
            break
        step = step_cls(step_config)
        next_status, decision = step.process(engine.form_data)
        engine.current_status = next_status if next_status else "stop"
        engine.audit(decision, current_user.username, current_user.roles[0] if current_user.roles else "")
        engine.form_data["status"] = engine.current_status

    # Determine assigned role
    assigned_role = engine.get_next_assigned_role()
    completed_at = "datetime('now')" if engine.current_status == "stop" else None

    # Persist
    db.execute_write(
        """UPDATE workflow_instances
           SET current_status = ?, form_data = ?, assigned_role = ?, updated_at = datetime('now'),
               completed_at = CASE WHEN ? = 'stop' THEN datetime('now') ELSE NULL END
           WHERE instance_id = ?""",
        (engine.current_status, json.dumps(engine.form_data), assigned_role, engine.current_status, instance_id),
    )

    # Save audit trail
    for entry in engine.audit_trail:
        db.execute_write(
            "INSERT INTO audit_trail (instance_id, status, action, description, user_id, role_name) VALUES (?, ?, ?, ?, ?, ?)",
            (instance_id, entry["status"], entry["action"], entry.get("description", ""), current_user.user_id, entry.get("role", "")),
        )

    return WorkflowInstanceResponse(
        instance_id=instance_id,
        wf_def_name=wf_def["name"],
        current_status=engine.current_status,
        form_data=engine.form_data,
        audit_trail=engine.audit_trail,
        assigned_role=assigned_role,
    )


@router.get("/{instance_id}", response_model=WorkflowInstanceResponse)
def get_workflow(
    instance_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    instance = _load_instance(db, instance_id)
    audit = _load_audit_trail(db, instance_id)

    return WorkflowInstanceResponse(
        instance_id=instance["instance_id"],
        wf_def_name=instance["wf_def_name"],
        current_status=instance["current_status"],
        form_data=json.loads(instance["form_data"]),
        audit_trail=audit,
        assigned_role=instance.get("assigned_role"),
        created_at=instance.get("created_at"),
        completed_at=instance.get("completed_at"),
    )


@router.post("/{instance_id}/action", response_model=WorkflowInstanceResponse)
def submit_action(
    instance_id: int,
    req: ActionRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    instance = _load_instance(db, instance_id)

    if instance.get("completed_at"):
        raise HTTPException(status_code=400, detail="Workflow is already completed")

    workflow_config = yaml.safe_load(instance["workflow_yaml"])
    form_config = yaml.safe_load(instance["form_yaml"])
    form_data = json.loads(instance["form_data"])
    audit = _load_audit_trail(db, instance_id)

    # Server-side validation
    import os
    config_dir = os.environ.get("APPROV_CONFIG_DIR", "config")
    validation_config_path = os.path.join(config_dir, "type_validation.yaml")
    validation_service = None
    if os.path.exists(validation_config_path):
        validation_service = ValidationService(config_path=validation_config_path)

    if validation_service:
        spec_builder = FormSpecBuilder(form_config, validation_service)
        field_rules = spec_builder.get_field_validation_rules()
        errors = validation_service.validate_form(req.field_values, field_rules)
        if errors:
            raise HTTPException(status_code=422, detail={"validation_errors": errors})

    # Run engine
    user_role = current_user.roles[0] if current_user.roles else ""
    engine = WorkflowEngine(
        workflow_config, form_config, form_data, audit, instance["current_status"]
    )

    try:
        state = engine.process_action(
            user_role=user_role,
            user_id=current_user.user_id,
            username=current_user.username,
            form_data=req.field_values,
            action=req.action,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Determine assigned role for next step
    assigned_role = engine.get_next_assigned_role()

    # Persist updated state
    db.execute_write(
        """UPDATE workflow_instances
           SET current_status = ?, form_data = ?, assigned_role = ?, updated_at = datetime('now'),
               completed_at = CASE WHEN ? = 'stop' THEN datetime('now') ELSE NULL END
           WHERE instance_id = ?""",
        (state.current_status, json.dumps(state.form_data), assigned_role, state.current_status, instance_id),
    )

    # Save new audit entries (only entries beyond what was already in DB)
    existing_count = len(audit)
    for entry in engine.audit_trail[existing_count:]:
        db.execute_write(
            "INSERT INTO audit_trail (instance_id, status, action, description, user_id, role_name) VALUES (?, ?, ?, ?, ?, ?)",
            (instance_id, entry["status"], entry["action"], entry.get("description", ""), current_user.user_id, entry.get("role", "")),
        )

    full_audit = _load_audit_trail(db, instance_id)

    return WorkflowInstanceResponse(
        instance_id=instance_id,
        wf_def_name=instance["wf_def_name"],
        current_status=state.current_status,
        form_data=state.form_data,
        audit_trail=full_audit,
        assigned_role=assigned_role,
    )


@router.get("/{instance_id}/audit")
def get_audit_trail(
    instance_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    # Verify instance exists
    instance = db.execute_read_one(
        "SELECT instance_id FROM workflow_instances WHERE instance_id = ?",
        (instance_id,),
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    return _load_audit_trail(db, instance_id)
