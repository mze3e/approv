from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class AuditEntry(BaseModel):
    status: str
    action: str
    description: str = ""
    timestamp: datetime
    user: str
    role: str = ""


class WorkflowState(BaseModel):
    instance_id: int
    current_status: str
    form_data: dict[str, Any]
    audit_trail: list[AuditEntry]


class FormFieldSpec(BaseModel):
    name: str
    title: str
    type: str
    value: Any = None
    disabled: bool = False
    options: list[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    default: Any = None
    validation: dict[str, str] | None = None  # {regex, description}


class FormSpec(BaseModel):
    instance_id: int
    status: str
    fields: list[FormFieldSpec]
    actions: list[dict[str, str]]  # [{key: "submit", title: "Submit"}, ...]


class FormSubmission(BaseModel):
    instance_id: int
    action: str
    field_values: dict[str, Any]


class UserContext(BaseModel):
    user_id: int
    username: str
    roles: list[str]
    permissions: list[str] = []
