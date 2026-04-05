"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import create_access_token, verify_password
from api.dependencies import get_current_user, get_db
from api.schemas import LoginRequest, LoginResponse, UserInfo
from approv.db import DatabaseManager
from approv.models import UserContext

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: DatabaseManager = Depends(get_db)):
    user = db.execute_read_one(
        "SELECT user_id, username, email, password_hash, is_active FROM users WHERE username = ?",
        (req.username,),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Get user roles
    roles = db.execute_read(
        """SELECT r.role_name FROM roles r
           JOIN user_roles ur ON r.role_id = ur.role_id
           WHERE ur.user_id = ?""",
        (user["user_id"],),
    )
    role_names = [r["role_name"] for r in roles]

    token = create_access_token(user["user_id"], user["username"], role_names)

    return LoginResponse(
        access_token=token,
        user=UserInfo(
            user_id=user["user_id"],
            username=user["username"],
            email=user.get("email"),
            roles=role_names,
        ),
    )


@router.get("/me", response_model=UserInfo)
def get_me(
    current_user: UserContext = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    user = db.execute_read_one(
        "SELECT user_id, username, email FROM users WHERE user_id = ?",
        (current_user.user_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get permissions via roles
    permissions = db.execute_read(
        """SELECT DISTINCT p.permission_name FROM permissions p
           JOIN role_permissions rp ON p.permission_id = rp.permission_id
           JOIN user_roles ur ON rp.role_id = ur.role_id
           WHERE ur.user_id = ?""",
        (current_user.user_id,),
    )

    return UserInfo(
        user_id=user["user_id"],
        username=user["username"],
        email=user.get("email"),
        roles=current_user.roles,
        permissions=[p["permission_name"] for p in permissions],
    )
