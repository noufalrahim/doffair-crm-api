from odmantic import AIOEngine
from fastapi import HTTPException, status

from admin.models.admin import Admin
from admin.utils.password import verify_password
from core.security import create_access_token
from core.enums import Role


async def authenticate_admin(
    engine: AIOEngine,
    email: str,
    password: str,
) -> str:
    admin = await engine.find_one(Admin, Admin.email == email)

    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(
        subject=str(admin.id),
        role=Role.ADMIN,
    )

    return token
