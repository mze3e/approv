"""Form specification endpoint - the key thin-client endpoint."""

import json
import os

import yaml
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user, get_db
from approv.db import DatabaseManager
from approv.form_spec import FormSpecBuilder
from approv.models import FormSpec, UserContext
from approv.validation import ValidationService

router = APIRouter()


@router.get("/{instance_id}", response_model=FormSpec)
def get_form_spec(
    instance_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Returns the complete form specification for a workflow instance.
    Includes field types, current values, disabled flags, validation rules, and available actions.
    This is everything the Streamlit client needs to render the form.
    """
    instance = db.execute_read_one(
        """SELECT wi.*, wd.form_yaml
           FROM workflow_instances wi
           JOIN workflow_definitions wd ON wi.wf_def_id = wd.wf_def_id
           WHERE wi.instance_id = ?""",
        (instance_id,),
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    form_config = yaml.safe_load(instance["form_yaml"])
    form_data = json.loads(instance["form_data"])

    # Load validation service
    config_dir = os.environ.get("APPROV_CONFIG_DIR", "config")
    validation_path = os.path.join(config_dir, "type_validation.yaml")
    validation_service = None
    if os.path.exists(validation_path):
        validation_service = ValidationService(config_path=validation_path)

    builder = FormSpecBuilder(form_config, validation_service)
    spec = builder.build_spec(
        form_data=form_data,
        user_roles=current_user.roles,
        current_status=instance["current_status"],
        instance_id=instance_id,
    )

    return spec
