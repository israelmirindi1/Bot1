import os
import time
import requests

# Clés d'API Binance
API_KEY = os.getenv("akIYsqqUKHMMvL9EIgFIfQdxE0ZHkrVThIrFjgfBlqAcYyAuUhwXnu202ipj8AOE")
SECRET_KEY = os.getenv("BuVnrnwCp5IERa7Yobrotr09NOfvz2z0JWKDWRJBsDE31GhV28aKbRSFwUpl1sL0")

# Configuration de la stratégie
FLOOR_PRICE = 2310.0  # Prix plancher minimum (en CDF)
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
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        ads = data.get("data", [])
        
        if ads:
            # Récupère le prix le plus bas actuellement sur le marché
            return float(ads[0]["adv"]["price"])
    except Exception as e:
        print(f"Erreur lors de la récupération des prix: {e}")
    return None

def calculate_target_price(market_min):
    # Calcul du prix ajusté (-1 CDF)
    ideal_price = market_min - PRICE_STEP
    
    # Sécurité : Appliquer la limite minimale de 2310 CDF
    if ideal_price < FLOOR_PRICE:
        print(f"Prix calculé ({ideal_price} CDF) sous la limite ! Blocage au plancher de {FLOOR_PRICE} CDF.")
        return FLOOR_PRICE
    
    return ideal_price

def main():
    print("--- Bot P2P Binance Démarré ---")
    print(f"Limite minimale configurée : {FLOOR_PRICE} CDF\n")
    
    market_min = get_lowest_sell_price()
    
    if market_min:
        target_price = calculate_target_price(market_min)
        print(f"Prix concurrent le plus bas : {market_min} CDF")
        print(f"Nouveau prix pour votre annonce : {target_price} CDF")
        
        # Ici : Ajouter la fonction de mise à jour de l'annonce via l'API Binance
    else:
        print("Impossible d'obtenir le prix du marché.")

if __name__ == "__main__":
    main()
