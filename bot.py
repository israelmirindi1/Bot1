import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# Lecture sécurisée des clés via Render
API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
BASE_URL = "https://api.binance.com"

AD_ID = "VOTRE_ID_ANNONCE_P2P"    # Remplacez par votre ID d'annonce
ASSET = "USDT"                     
FIAT = "CDF"                       
TRADE_TYPE = "SELL"                

PRICE_STEP = 1.0                   # -1 CDF
MIN_PRICE_LIMIT = 2200.0           # Prix plancher de sécurité

def get_signature(query_string):
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def get_lowest_market_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "asset": ASSET,
        "fiat": FIAT,
        "tradeType": TRADE_TYPE,
        "page": 1,
        "rows": 10,
        "payTypes": []
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    if data.get("data"):
        for item in data["data"]:
            adv = item["adv"]
            if adv["advNo"] != AD_ID:
                return float(adv["price"])
    return None

def update_ad_price(new_price):
    endpoint = "/sapi/v1/c2c/ads/update"
    timestamp = int(time.time() * 1000)
    
    params = {
        "advNo": AD_ID,
        "price": str(new_price),
        "timestamp": timestamp
    }
    
    query_string = urlencode(params)
    signature = get_signature(query_string)
    
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    headers = {"X-MBXAPIKEY": API_KEY}
    
    response = requests.post(url, headers=headers)
    return response.json()

def run_bot():
    print(f"Bot P2P démarré [{ASSET}/{FIAT}]")
    while True:
        try:
            lowest_price = get_lowest_market_price()
            if lowest_price:
                target_price = lowest_price - PRICE_STEP
                if target_price < MIN_PRICE_LIMIT:
                    target_price = MIN_PRICE_LIMIT
                
                print(f"Prix marché: {lowest_price} CDF | Nouveau prix: {target_price} CDF")
                result = update_ad_price(target_price)
                print("Statut:", result)
        except Exception as e:
            print(f"Erreur: {e}")
        time.sleep(15)

if __name__ == "__main__":
    run_bot()
