from fastapi import APIRouter
from services.volatility_service import get_volatility

router = APIRouter()

@router.get("/")
def volatility():
    return get_volatility()