from odmantic import AIOEngine
from fastapi import HTTPException, status

from admin.models.admin import Admin
from admin.utils.password import verify_password
from core.security import create_access_token
from core.enums import Role


from typing import Tuple

async def authenticate_admin(
    engine: AIOEngine,
    email: str,
    password: str,
) -> Tuple[str, Admin]:
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

    return token, admin


async def register_admin(
    engine: AIOEngine,
    name: str,
    email: str,
    password: str,
    is_super_admin: bool = False,
) -> Tuple[str, Admin]:
    existing_admin = await engine.find_one(Admin, Admin.email == email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists",
        )

    from admin.utils.password import hash_password

    admin = Admin(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_super_admin=is_super_admin,
    )

    await engine.save(admin)

    token = create_access_token(
        subject=str(admin.id),
        role=Role.ADMIN,
    )

    return token, admin
