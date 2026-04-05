"""
Workflow engine - decoupled from any UI framework.

Manages workflow state machine execution, audit trail, and permission checking.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from approv.models import AuditEntry, WorkflowState
from approv.steps import STEP_REGISTRY

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(
        self,
        workflow_config: dict,
        form_config: dict,
        form_data: dict,
        audit_trail: list[dict],
        current_status: str = "start",
    ):
        self.config = workflow_config
        self.form_config = form_config
        self.form_data = form_data
        self.audit_trail = audit_trail
        self.current_status = current_status

    def audit(self, action: str, user: str, role: str = "", description: str = ""):
        entry = {
            "status": self.current_status,
            "action": action,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "role": role,
        }
        self.audit_trail.append(entry)

    def initiate(self, user: str, role: str = "") -> WorkflowState:
        self.current_status = "start"
        self.audit("Workflow Initiated", user, role)
        return self._build_state(0)

    def cancel(self, user: str, role: str = "") -> WorkflowState:
        self.current_status = "stop"
        self.audit("Workflow Cancelled", user, role)
        return self._build_state(0)

    def process_action(
        self,
        user_role: str,
        user_id: int,
        username: str,
        form_data: dict,
        action: str,
    ) -> WorkflowState:
        """
        Process a user action on the workflow.
        Merges submitted form_data, logs comments, then advances the state machine.
        Returns updated WorkflowState.
        """
        # Merge submitted values into current form data
        self.form_data.update(form_data)
        self.form_data["action"] = action

        # Log comments if any
        comments = self.form_data.get("comments", "")
        if comments:
            self.audit("Commented", username, user_role, comments)
            self.form_data["comments"] = ""

        # Run the state machine loop
        while True:
            step_config = self.config["workflow"][self.current_status]

            # Permission check for user-action steps
            if step_config.get("require_user_action", False):
                if not self._check_permission(step_config, user_role):
                    raise PermissionError(
                        f"Role '{user_role}' does not have permission for step '{self.current_status}'"
                    )

            # Instantiate and execute step
            step_class_name = step_config["class"]
            step_cls = STEP_REGISTRY.get(step_class_name)
            if not step_cls:
                raise ValueError(f"Unknown step class: {step_class_name}")

            step = step_cls(step_config)
            next_status, decision = step.process(self.form_data)
            self.current_status = next_status if next_status else "stop"
            self.audit(decision, username, user_role)
            self.form_data["status"] = self.current_status

            if self.current_status == "stop":
                break

            # If next step doesn't require user action, auto-advance
            next_step = self.config["workflow"].get(self.current_status, {})
            if next_step.get("require_user_action", False):
                break

        return self._build_state(0)

    def get_next_assigned_role(self) -> str | None:
        """Determine which role needs to act on the current step."""
        if self.current_status == "stop":
            return None
        step_config = self.config["workflow"].get(self.current_status, {})
        roles = step_config.get("role", [])
        if roles:
            return roles[0]  # Primary assigned role
        # Check user field for backward compat
        users = step_config.get("user", [])
        if users:
            return users[0] if users[0] else None
        return None

    def _check_permission(self, step_config: dict, user_role: str) -> bool:
        roles = step_config.get("role", [])
        if roles and user_role not in roles:
            return False
        return True

    def _build_state(self, instance_id: int) -> WorkflowState:
        return WorkflowState(
            instance_id=instance_id,
            current_status=self.current_status,
            form_data=self.form_data,
            audit_trail=[
                AuditEntry(
                    status=e["status"],
                    action=e["action"],
                    description=e.get("description", ""),
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    user=e["user"],
                    role=e.get("role", ""),
                )
                for e in self.audit_trail
            ],
        )
