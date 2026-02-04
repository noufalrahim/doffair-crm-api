from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings
from core.enums import Role, VendorRole

security_scheme = HTTPBearer()


# ---------------------------------------------------------
# Token Creation
# ---------------------------------------------------------

def create_access_token(
    *,
    subject: str,
    role: Role,
    vendor_id: Optional[str] = None,
    vendor_role: Optional[VendorRole] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token.
    """

    now = datetime.utcnow()

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "iat": int(now.timestamp()),
    }

    # Vendor-specific claims
    if role == Role.VENDOR:
        if not vendor_id or not vendor_role:
            raise ValueError("vendor_id and vendor_role required for vendor tokens")

        payload["vendor_id"] = vendor_id
        payload["vendor_role"] = vendor_role.value

    expire = now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = int(expire.timestamp())

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ---------------------------------------------------------
# Token Decoding
# ---------------------------------------------------------

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ---------------------------------------------------------
# Current User Resolver
# ---------------------------------------------------------

def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Extracts and validates JWT payload.
    """
    return decode_token(credentials.credentials)


# ---------------------------------------------------------
# Role Guards
# ---------------------------------------------------------

def require_admin(token: Dict[str, Any] = Depends(get_current_token)) -> Dict[str, Any]:
    if token.get("role") != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return token


def require_user(token: Dict[str, Any] = Depends(get_current_token)) -> Dict[str, Any]:
    if token.get("role") != Role.USER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required",
        )
    return token


def require_vendor(
    allowed_roles: Optional[list[VendorRole]] = None,
):
    def _guard(token: Dict[str, Any] = Depends(get_current_token)) -> Dict[str, Any]:
        if token.get("role") != Role.VENDOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vendor access required",
            )

        if allowed_roles:
            vendor_role = token.get("vendor_role")
            if vendor_role not in [r.value for r in allowed_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient vendor permissions",
                )

        return token

    return _guard


def get_current_vendor(token: Dict[str, Any] = Depends(get_current_token)) -> Dict[str, Any]:
    """Get current vendor from token - simple vendor auth"""
    if token.get("role") != Role.VENDOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor access required",
        )
    return token
