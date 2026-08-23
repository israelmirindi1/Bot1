import os
import time
import hmac
import hashlib
import requests

# Récupération des clés depuis les variables définies dans Termius
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ADV_NO = os.getenv("ADV_NO")

FLOOR_PRICE = 2310.0  # Prix plancher minimum (CDF)
PRICE_STEP = 1.0      # Écart à soustraire (-1 CDF)

def get_lowest_sell_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "CDF",
        "merchantCheck": False,
        "page": 1,
        "rows": 10,
        "tradeType": "SELL"
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
        print("Erreur : Clés API ou ADV_NO manquants dans l'environnement !")
        return

    url = "https://api.binance.com/sapi/v1/c2c/ads/update"
    timestamp = int(time.time() * 1000)
    
    # Paramètres de la requête de mise à jour Binance
    params = {
        "advNo": ADV_NO,
        "price": str(new_price),
        "timestamp": timestamp
    }
    
    # Création de la signature HMAC-SHA256
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    try:
        response = requests.post(url, headers=headers, params=params)
        print(f"Statut mise à jour : {response.status_code}")
        print(f"Réponse Binance : {response.text}")
    except Exception as e:
        print(f"Erreur envoi modification : {e}")

def main():
    print("--- Démarrage du Bot P2P Binance ---")
    market_min = get_lowest_sell_price()
    
    if market_min:
        target_price = max(market_min - PRICE_STEP, FLOOR_PRICE)
        print(f"Prix concurrent le plus bas : {market_min} CDF")
        print(f"Ajustement de votre annonce à : {target_price} CDF")
        
        # Envoi de la mise à jour à Binance
        update_ad_price(target_price)
    else:
        print("Impossible de récupérer les prix du marché.")

if __name__ == "__main__":
    main()
