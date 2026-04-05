"""Task views - pending items and workflow history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user, get_db
from api.schemas import TaskItem
from approv.db import DatabaseManager
from approv.models import UserContext

router = APIRouter()


@router.get("/pending", response_model=list[TaskItem])
def get_pending_tasks(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get workflow instances that require action from the current user's roles."""
    if not current_user.roles:
        return []

    placeholders = ",".join("?" for _ in current_user.roles)
    rows = db.execute_read(
        f"""SELECT wi.instance_id, wd.name as wf_def_name, wi.current_status,
                   wi.assigned_role, u.username as started_by,
                   wi.created_at, wi.updated_at
            FROM workflow_instances wi
            JOIN workflow_definitions wd ON wi.wf_def_id = wd.wf_def_id
            JOIN users u ON wi.started_by = u.user_id
            WHERE wi.assigned_role IN ({placeholders})
              AND wi.completed_at IS NULL
            ORDER BY wi.updated_at DESC""",
        tuple(current_user.roles),
    )

    return [TaskItem(**row) for row in rows]


@router.get("/history", response_model=list[TaskItem])
def get_past_workflows(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get completed workflows the user participated in or started."""
    rows = db.execute_read(
        """SELECT DISTINCT wi.instance_id, wd.name as wf_def_name, wi.current_status,
                  wi.assigned_role, u.username as started_by,
                  wi.created_at, wi.updated_at, wi.completed_at
           FROM workflow_instances wi
           JOIN workflow_definitions wd ON wi.wf_def_id = wd.wf_def_id
           JOIN users u ON wi.started_by = u.user_id
           LEFT JOIN audit_trail at ON wi.instance_id = at.instance_id AND at.user_id = ?
           WHERE (wi.started_by = ? OR at.user_id = ?)
           ORDER BY wi.updated_at DESC
           LIMIT ? OFFSET ?""",
        (current_user.user_id, current_user.user_id, current_user.user_id, limit, offset),
    )

    return [TaskItem(**row) for row in rows]


@router.get("/all", response_model=list[TaskItem])
def get_all_tasks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Admin: get all active workflow instances."""
    rows = db.execute_read(
        """SELECT wi.instance_id, wd.name as wf_def_name, wi.current_status,
                  wi.assigned_role, u.username as started_by,
                  wi.created_at, wi.updated_at, wi.completed_at
           FROM workflow_instances wi
           JOIN workflow_definitions wd ON wi.wf_def_id = wd.wf_def_id
           JOIN users u ON wi.started_by = u.user_id
           ORDER BY wi.updated_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    )

    return [TaskItem(**row) for row in rows]
