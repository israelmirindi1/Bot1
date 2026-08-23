import os
import time
import hmac
import hashlib
import requests

# Variables d'environnement
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ADV_NO = os.getenv("ADV_NO")

FLOOR_PRICE = 2310.0  # Limite minimale (CDF)
PRICE_STEP = 1.0      # Écart de -1 CDF pour passer devant

def get_lowest_p2p_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "CDF",
        "merchantCheck": False,
        "page": 1,
        "rows": 10,
        "tradeType": "BUY"  # Filtre exact pour la liste de l'onglet "Buy"
    }
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        ads = res.get("data", [])
        if ads:
            # Récupère le prix du tout premier vendeur (ex: 2327.8 CDF sur la photo)
            return float(ads[0]["adv"]["price"])
    except Exception as e:
        print(f"Erreur lecture marché : {e}")
    return None

def update_ad_price(new_price):
    if not API_KEY or not SECRET_KEY or not ADV_NO:
        print("Erreur : API_KEY, SECRET_KEY ou ADV_NO manquants dans Termius.")
        return

    url = "https://api.binance.com/sapi/v1/c2c/ads/update"
    timestamp = int(time.time() * 1000)
    
    params = {
        "advNo": ADV_NO,
        "price": str(new_price),
        "timestamp": timestamp
    }
    
    # Signature de la requête
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    params["signature"] = signature

    headers = {"X-MBX-APIKEY": API_KEY}

    try:
        response = requests.post(url, headers=headers, params=params)
        print(f"Réponse Binance : {response.text}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour : {e}")

def main():
    print("--- Bot P2P Binance (Onglet Buy) ---")
    market_min = get_lowest_p2p_price()
    
    if market_min:
        # Calcule le prix pour passer juste au-dessus/en-dessous (ex: 2327.8 - 1 = 2326.8)
        target_price = max(market_min - PRICE_STEP, FLOOR_PRICE)
        print(f"1er vendeur actuel : {market_min} CDF")
        print(f"Votre nouveau prix ciblé : {target_price} CDF")
        
        update_ad_price(target_price)
    else:
        print("Impossible d'obtenir les prix du marché.")

if __name__ == "__main__":
    main()
