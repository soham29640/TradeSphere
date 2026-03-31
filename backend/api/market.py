from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def market():
    return {
        "sentiment": "positive",
        "trend": "bullish"
    }