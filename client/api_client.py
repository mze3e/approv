"""HTTP client wrapper for the ApproV API."""

import requests
from typing import Any


class ApprovClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        resp = requests.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_data: dict | None = None) -> dict:
        resp = requests.post(f"{self.base_url}{path}", headers=self._headers(), json=json_data)
        if resp.status_code == 422:
            data = resp.json()
            if "detail" in data and isinstance(data["detail"], dict) and "validation_errors" in data["detail"]:
                raise ValidationError(data["detail"]["validation_errors"])
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, json_data: dict | None = None) -> dict:
        resp = requests.put(f"{self.base_url}{path}", headers=self._headers(), json=json_data)
        resp.raise_for_status()
        return resp.json()

    # --- Auth ---

    def login(self, username: str, password: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    def get_me(self) -> dict:
        return self._get("/auth/me")

    # --- Workflows ---

    def start_workflow(self, wf_def_id: int) -> dict:
        return self._post("/workflows/", {"wf_def_id": wf_def_id})

    def get_workflow(self, instance_id: int) -> dict:
        return self._get(f"/workflows/{instance_id}")

    def submit_action(self, instance_id: int, action: str, field_values: dict) -> dict:
        return self._post(
            f"/workflows/{instance_id}/action",
            {"action": action, "field_values": field_values},
        )

    def get_audit_trail(self, instance_id: int) -> list:
        return self._get(f"/workflows/{instance_id}/audit")

    # --- Forms ---

    def get_form_spec(self, instance_id: int) -> dict:
        return self._get(f"/forms/{instance_id}")

    # --- Tasks ---

    def get_pending_tasks(self) -> list:
        return self._get("/tasks/pending")

    def get_past_workflows(self, limit: int = 50, offset: int = 0) -> list:
        return self._get("/tasks/history", params={"limit": limit, "offset": offset})

    def get_all_tasks(self, limit: int = 50, offset: int = 0) -> list:
        return self._get("/tasks/all", params={"limit": limit, "offset": offset})

    # --- Admin: Workflow Definitions ---

    def get_workflow_definitions(self) -> list:
        return self._get("/admin/workflow-definitions")

    def get_workflow_definition(self, wf_def_id: int) -> dict:
        return self._get(f"/admin/workflow-definitions/{wf_def_id}")

    def create_workflow_definition(self, data: dict) -> dict:
        return self._post("/admin/workflow-definitions", data)

    def update_workflow_definition(self, wf_def_id: int, data: dict) -> dict:
        return self._put(f"/admin/workflow-definitions/{wf_def_id}", data)

    # --- Admin: Users ---

    def get_users(self) -> list:
        return self._get("/admin/users")

    def create_user(self, data: dict) -> dict:
        return self._post("/admin/users", data)

    def update_user(self, user_id: int, data: dict) -> dict:
        return self._put(f"/admin/users/{user_id}", data)

    # --- Admin: Roles ---

    def get_roles(self) -> list:
        return self._get("/admin/roles")

    def create_role(self, data: dict) -> dict:
        return self._post("/admin/roles", data)

    # --- Admin: Database ---

    def backup_db(self) -> dict:
        return self._post("/admin/db/backup")

    def export_db(self) -> bytes:
        resp = requests.get(f"{self.base_url}/admin/db/export", headers=self._headers())
        resp.raise_for_status()
        return resp.content

    def import_db(self, file_bytes: bytes) -> dict:
        resp = requests.post(
            f"{self.base_url}/admin/db/import",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            files={"file": ("approv.db", file_bytes, "application/octet-stream")},
        )
        resp.raise_for_status()
        return resp.json()

    def list_backups(self) -> list:
        return self._get("/admin/db/backups")


class ValidationError(Exception):
    """Raised when server-side validation fails."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(f"Validation errors: {errors}")
