import requests

url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"
response = requests.get(url)

print("Status Code:", response.status_code)
print("Response (first 200 chars):", response.text[:200])