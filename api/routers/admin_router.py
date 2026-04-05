"""Admin endpoints: workflow definitions, user/role CRUD, DB backup/export/import."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response

from api.auth import hash_password
from api.dependencies import get_current_user, get_db
from api.schemas import (
    RoleCreateRequest,
    RoleResponse,
    S3RestoreRequest,
    UserCreateRequest,
    UserInfo,
    UserUpdateRequest,
    WorkflowDefinitionCreateRequest,
    WorkflowDefinitionDetail,
    WorkflowDefinitionResponse,
    WorkflowDefinitionUpdateRequest,
)
from approv.db import DatabaseManager
from approv.models import UserContext

router = APIRouter()


# --- Workflow Definitions ---


@router.get("/workflow-definitions", response_model=list[WorkflowDefinitionResponse])
def list_workflow_definitions(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    rows = db.execute_read("SELECT wf_def_id, name, description, is_active FROM workflow_definitions ORDER BY wf_def_id")
    return [WorkflowDefinitionResponse(**row) for row in rows]


@router.get("/workflow-definitions/{wf_def_id}", response_model=WorkflowDefinitionDetail)
def get_workflow_definition(
    wf_def_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    row = db.execute_read_one("SELECT * FROM workflow_definitions WHERE wf_def_id = ?", (wf_def_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return WorkflowDefinitionDetail(**row)


@router.post("/workflow-definitions", response_model=WorkflowDefinitionResponse)
def create_workflow_definition(
    req: WorkflowDefinitionCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    wf_def_id = db.execute_write(
        "INSERT INTO workflow_definitions (name, description, workflow_yaml, form_yaml, seed_data_json) VALUES (?, ?, ?, ?, ?)",
        (req.name, req.description, req.workflow_yaml, req.form_yaml, req.seed_data_json),
    )
    return WorkflowDefinitionResponse(wf_def_id=wf_def_id, name=req.name, description=req.description)


@router.put("/workflow-definitions/{wf_def_id}", response_model=WorkflowDefinitionResponse)
def update_workflow_definition(
    wf_def_id: int,
    req: WorkflowDefinitionUpdateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    existing = db.execute_read_one("SELECT * FROM workflow_definitions WHERE wf_def_id = ?", (wf_def_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow definition not found")

    updates = []
    params = []
    for field in ["name", "description", "workflow_yaml", "form_yaml", "seed_data_json"]:
        val = getattr(req, field, None)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if req.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if req.is_active else 0)

    if updates:
        updates.append("updated_at = datetime('now')")
        params.append(wf_def_id)
        db.execute_write(f"UPDATE workflow_definitions SET {', '.join(updates)} WHERE wf_def_id = ?", tuple(params))

    updated = db.execute_read_one("SELECT wf_def_id, name, description, is_active FROM workflow_definitions WHERE wf_def_id = ?", (wf_def_id,))
    return WorkflowDefinitionResponse(**updated)


# --- Users ---


@router.get("/users", response_model=list[UserInfo])
def list_users(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    users = db.execute_read("SELECT user_id, username, email FROM users WHERE is_active = 1 ORDER BY user_id")
    result = []
    for u in users:
        roles = db.execute_read(
            "SELECT r.role_name FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?",
            (u["user_id"],),
        )
        result.append(UserInfo(
            user_id=u["user_id"],
            username=u["username"],
            email=u.get("email"),
            roles=[r["role_name"] for r in roles],
        ))
    return result


@router.post("/users", response_model=UserInfo)
def create_user(
    req: UserCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    password_hash = hash_password(req.password)
    user_id = db.execute_write(
        "INSERT INTO users (username, email, phone, password_hash) VALUES (?, ?, ?, ?)",
        (req.username, req.email, req.phone, password_hash),
    )

    # Assign roles
    for role_id in req.role_ids:
        db.execute_write("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))

    roles = db.execute_read(
        "SELECT r.role_name FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?",
        (user_id,),
    )
    return UserInfo(user_id=user_id, username=req.username, email=req.email, roles=[r["role_name"] for r in roles])


@router.put("/users/{user_id}", response_model=UserInfo)
def update_user(
    user_id: int,
    req: UserUpdateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    existing = db.execute_read_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    updates = []
    params = []
    if req.email is not None:
        updates.append("email = ?")
        params.append(req.email)
    if req.phone is not None:
        updates.append("phone = ?")
        params.append(req.phone)
    if req.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if req.is_active else 0)
    if req.password is not None:
        updates.append("password_hash = ?")
        params.append(hash_password(req.password))

    if updates:
        updates.append("updated_at = datetime('now')")
        params.append(user_id)
        db.execute_write(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params))

    # Update roles if specified
    if req.role_ids is not None:
        db.execute_write("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        for role_id in req.role_ids:
            db.execute_write("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))

    user = db.execute_read_one("SELECT user_id, username, email FROM users WHERE user_id = ?", (user_id,))
    roles = db.execute_read(
        "SELECT r.role_name FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?",
        (user_id,),
    )
    return UserInfo(user_id=user["user_id"], username=user["username"], email=user.get("email"), roles=[r["role_name"] for r in roles])


# --- Roles ---


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    roles = db.execute_read("SELECT role_id, role_name, description FROM roles WHERE is_active = 1 ORDER BY role_id")
    result = []
    for r in roles:
        perms = db.execute_read(
            "SELECT p.permission_name FROM permissions p JOIN role_permissions rp ON p.permission_id = rp.permission_id WHERE rp.role_id = ?",
            (r["role_id"],),
        )
        result.append(RoleResponse(
            role_id=r["role_id"],
            role_name=r["role_name"],
            description=r.get("description"),
            permissions=[p["permission_name"] for p in perms],
        ))
    return result


@router.post("/roles", response_model=RoleResponse)
def create_role(
    req: RoleCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    role_id = db.execute_write(
        "INSERT INTO roles (role_name, description) VALUES (?, ?)",
        (req.role_name, req.description),
    )
    for perm_id in req.permission_ids:
        db.execute_write("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (role_id, perm_id))

    perms = db.execute_read(
        "SELECT p.permission_name FROM permissions p JOIN role_permissions rp ON p.permission_id = rp.permission_id WHERE rp.role_id = ?",
        (role_id,),
    )
    return RoleResponse(role_id=role_id, role_name=req.role_name, description=req.description, permissions=[p["permission_name"] for p in perms])


# --- Database Backup / Export / Import ---


@router.post("/db/backup")
def backup_to_s3(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    bucket = os.environ.get("APPROV_S3_BUCKET")
    if not bucket:
        raise HTTPException(status_code=400, detail="APPROV_S3_BUCKET not configured")
    key = db.backup_to_s3(bucket)
    return {"message": "Backup completed", "key": key}


@router.get("/db/export")
def export_database(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    data = db.export_db()
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=approv_export.db"},
    )


@router.post("/db/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    contents = await file.read()
    db.import_db(contents)
    return {"message": "Database imported successfully"}


@router.post("/db/restore")
def restore_from_s3(
    req: S3RestoreRequest,
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    db.restore_from_s3(req.bucket, req.key)
    return {"message": f"Database restored from {req.key}"}


@router.get("/db/backups")
def list_s3_backups(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    bucket = os.environ.get("APPROV_S3_BUCKET")
    if not bucket:
        raise HTTPException(status_code=400, detail="APPROV_S3_BUCKET not configured")
    return db.list_s3_backups(bucket)
