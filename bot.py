import os
import time
import hmac
import hashlib
import requests

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ADV_NO = os.getenv("ADV_NO")

FLOOR_PRICE = 2310.0
PRICE_STEP = 1.0

def get_lowest_p2p_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "CDF",
        "merchantCheck": False,
        "page": 1,
        "rows": 10,
        "tradeType": "BUY"
    }
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        ads = res.get("data", [])
        if ads:
            return float(ads[0]["adv"]["price"])
    except Exception as e:
        print(f"Erreur lecture marché : {e}")
    return None

def update_ad_price(new_price):
    if not API_KEY or not SECRET_KEY or not ADV_NO:
        print("Erreur : Clés manquantes dans Termius !")
        return

    # Endpoint d'update C2C officiel
    url = "https://api.binance.com/sapi/v1/c2c/ads/update"
    timestamp = int(time.time() * 1000)
    formatted_price = f"{new_price:.2f}"
    
    # Paramètres de la requête
    params = {
        "advNo": ADV_NO,
        "price": formatted_price,
        "timestamp": timestamp
    }
    
    # Signature HMAC SHA256
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Envoi direct dans les query params (URL)
    final_url = f"{url}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}

    try:
        response = requests.post(final_url, headers=headers)
        print(f"Code HTTP : {response.status_code}")
        print(f"Réponse Binance : {response.text}")
    except Exception as e:
        print(f"Erreur réseau : {e}")

def main():
    print("--- Bot P2P Binance (Onglet Buy) ---")
    market_min = get_lowest_p2p_price()
    
    if market_min:
        target_price = max(market_min - PRICE_STEP, FLOOR_PRICE)
        print(f"1er vendeur actuel : {market_min} CDF")
        print(f"Votre nouveau prix ciblé : {target_price:.2f} CDF")
        
        update_ad_price(target_price)
    else:
        print("Impossible d'obtenir les prix du marché.")

if __name__ == "__main__":
    main()
