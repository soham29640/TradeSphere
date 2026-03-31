from fastapi import APIRouter
from services.price_service import predict_price

router = APIRouter()

@router.get("/")
def get_prediction(ticker: str = "AAPL"):
    result = predict_price(ticker)
    return result