from fastapi import FastAPI
from api import prediction, volatility, pattern, trading, market

app = FastAPI(title="TradeSphere API")

# include routers
app.include_router(prediction.router, prefix="/predict")
app.include_router(volatility.router, prefix="/volatility")
app.include_router(pattern.router, prefix="/pattern")
app.include_router(trading.router, prefix="/trade")
app.include_router(market.router, prefix="/market")

@app.get("/")
def home():
    return {"message": "TradeSphere Backend Running"}