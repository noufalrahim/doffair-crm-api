import asyncio
import os
import sys

# Add the current directory to sys.path to import local modules
sys.path.append(os.getcwd())

from core.database import get_engine
from admin.models.admin import Admin
from admin.utils.password import hash_password

async def create_admin():
    engine = get_engine()
    
    # User requested specific role login
    email = "doctor@doffair.com"
    password = "doctor@doffair.com"
    role = "Doctor"
    
    # Check if admin already exists
    existing = await engine.find_one(Admin, Admin.email == email)
    if existing:
        print(f"Admin with email {email} already exists. Updating role and password...")
        existing.password_hash = hash_password(password)
        existing.role = role
        await engine.save(existing)
        print("Updated successfully.")
    else:
        new_admin = Admin(
            name="Doctor User",
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_super_admin=False
        )
        await engine.save(new_admin)
        print(f"Doctor Admin created successfully with email: {email}")

if __name__ == "__main__":
    asyncio.run(create_admin())
