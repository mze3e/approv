"""API request/response Pydantic schemas."""

from pydantic import BaseModel
from typing import Any, Optional


# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    user_id: int
    username: str
    email: str | None = None
    roles: list[str]
    permissions: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# --- Workflows ---

class WorkflowCreateRequest(BaseModel):
    wf_def_id: int


class ActionRequest(BaseModel):
    action: str
    field_values: dict[str, Any]


class WorkflowInstanceResponse(BaseModel):
    instance_id: int
    wf_def_name: str | None = None
    current_status: str
    form_data: dict[str, Any]
    audit_trail: list[dict[str, Any]]
    assigned_role: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


# --- Tasks ---

class TaskItem(BaseModel):
    instance_id: int
    wf_def_name: str
    current_status: str
    assigned_role: str | None = None
    started_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


# --- Admin ---

class WorkflowDefinitionResponse(BaseModel):
    wf_def_id: int
    name: str
    description: str | None = None
    is_active: bool = True


class WorkflowDefinitionDetail(BaseModel):
    wf_def_id: int
    name: str
    description: str | None = None
    workflow_yaml: str
    form_yaml: str
    seed_data_json: str | None = None
    is_active: bool = True


class WorkflowDefinitionCreateRequest(BaseModel):
    name: str
    description: str | None = None
    workflow_yaml: str
    form_yaml: str
    seed_data_json: str | None = None


class WorkflowDefinitionUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    workflow_yaml: str | None = None
    form_yaml: str | None = None
    seed_data_json: str | None = None
    is_active: bool | None = None


class UserCreateRequest(BaseModel):
    username: str
    email: str | None = None
    phone: str | None = None
    password: str
    role_ids: list[int] = []


class UserUpdateRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None
    password: str | None = None


class RoleCreateRequest(BaseModel):
    role_name: str
    description: str | None = None
    permission_ids: list[int] = []


class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    description: str | None = None
    permissions: list[str] = []


class S3RestoreRequest(BaseModel):
    bucket: str
    key: str
