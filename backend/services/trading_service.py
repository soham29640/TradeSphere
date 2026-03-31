portfolio = {
    "cash": 100000,
    "holdings": 0
}

def buy_stock(price, quantity):
    cost = price * quantity
    if portfolio["cash"] >= cost:
        portfolio["cash"] -= cost
        portfolio["holdings"] += quantity
        return {"status": "bought"}
    return {"status": "failed"}

def sell_stock(price, quantity):
    if portfolio["holdings"] >= quantity:
        portfolio["cash"] += price * quantity
        portfolio["holdings"] -= quantity
        return {"status": "sold"}
    return {"status": "failed"}