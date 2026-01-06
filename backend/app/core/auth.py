from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings


settings = get_settings()
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


async def verify_api_key(api_key: str = Security(dependency=api_key_header)) -> str:
    if not api_key:
        raise HTTPException(
            detail="API key required",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if api_key != settings.api_key:
        raise HTTPException(
            detail="Invalid API key",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return api_key
