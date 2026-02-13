from odmantic import AIOEngine
from fastapi import HTTPException, status
from admin.models.admin import Admin
from admin.schemas.admin import AdminCreateRequest
from admin.utils.password import hash_password

async def add_new_admin(
    engine: AIOEngine,
    payload: AdminCreateRequest,
) -> Admin:
    # Check if admin already exists
    existing_admin = await engine.find_one(Admin, Admin.email == payload.email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists",
        )

    admin = Admin(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_super_admin=payload.is_super_admin,
    )

    await engine.save(admin)
    return admin

async def get_admin_by_id(
    engine: AIOEngine,
    admin_id: str,
) -> Admin:
    from bson import ObjectId
    try:
        oid = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin id format",
        )
    
    admin = await engine.find_one(Admin, Admin.id == oid)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    return admin
