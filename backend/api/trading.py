from fastapi import APIRouter
from services.trading_service import buy_stock, sell_stock

router = APIRouter()

@router.post("/buy")
def buy(price: float, quantity: int):
    return buy_stock(price, quantity)

@router.post("/sell")
def sell(price: float, quantity: int):
    return sell_stock(price, quantity)