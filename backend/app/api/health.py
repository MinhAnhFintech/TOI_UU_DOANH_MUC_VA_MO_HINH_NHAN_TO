from fastapi import APIRouter
from app.schemas.common import APIResponse

router = APIRouter()

@router.get("", response_model=APIResponse)
def health_check():
    return APIResponse(data={"status": "ok", "version": "0.1.0"})
