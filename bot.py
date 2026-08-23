import os
import time
import hmac
import hashlib
from urllib.parse import urlencode

import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("API_KEY") or os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("BINANCE_SECRET_KEY")
ADV_NO = os.getenv("ADV_NO")

FLOOR_PRICE = 2310.0
PRICE_STEP = 1.0

MARKET_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
UPDATE_URL = "https://api.binance.com/sapi/v1/c2c/agent/ads/update"

HEADERS = {
    "X-MBX-APIKEY": API_KEY or "",
    "User-Agent": "binance-wallet/1.0.0 (Bot)",
    "Content-Type": "application/json",
}


# ============================================================
# SIGNATURE SAPI
# IMPORTANT: DO NOT SORT PARAMETERS.
# ============================================================

def sign_params(params):
    query_string = urlencode(params)

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return query_string, signature


# ============================================================
# RECHERCHE DU MEILLEUR PRIX CONCURRENT
#
# TON annonce est SELL USDT/CDF.
# Dans la recherche publique Binance, les annonces concurrentes
# visibles par l'acheteur sont obtenues avec tradeType=BUY.
# ============================================================

def get_best_competitor_price():
    payload = {
        "asset": "USDT",
        "fiat": "CDF",
        "merchantCheck": False,
        "page": 1,
        "rows": 20,
        "tradeType": "BUY",
    }

    try:
        response = requests.post(
            MARKET_URL,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()
        result = response.json()

        ads = result.get("data", [])

        prices = []

        for ad in ads:
            try:
                adv = ad["adv"]
                adv_no = str(adv.get("advNo", ""))

                # Ne pas comparer notre propre annonce à elle-même.
                if ADV_NO and adv_no == str(ADV_NO):
                    continue

                # Ne garder que les annonces USDT/CDF.
                if adv.get("asset") != "USDT":
                    continue

                if adv.get("fiatUnit") != "CDF":
                    continue

                price = float(adv["price"])

                if price > 0:
                    prices.append(price)

            except (KeyError, TypeError, ValueError):
                continue

        if not prices:
            return None

        return min(prices)

    except requests.RequestException as e:
        print(f"Erreur réseau marché P2P : {e}")
        return None

    except Exception as e:
        print(f"Erreur lecture marché : {e}")
        return None


# ============================================================
# LECTURE DE NOTRE ANNONCE
# ============================================================

def get_my_ad():
    timestamp = int(time.time() * 1000)

    params = {
        "advNo": ADV_NO,
        "timestamp": timestamp,
        "recvWindow": 60000,
    }

    query_string, signature = sign_params(params)

    url = (
        "https://api.binance.com"
        "/sapi/v1/c2c/agent/ads/getDetailByNo"
        f"?{query_string}&signature={signature}"
    )

    try:
        response = requests.post(
            url,
            headers=HEADERS,
            timeout=15,
        )

        print(f"Lecture annonce - HTTP : {response.status_code}")

        data = response.json()

        if response.status_code != 200:
            print(f"Réponse Binance : {response.text}")
            return None

        if data.get("success") is not True:
            print(f"Réponse Binance : {response.text}")
            return None

        return data.get("data")

    except Exception as e:
        print(f"Erreur lecture de l'annonce : {e}")
        return None


# ============================================================
# MODIFICATION DU PRIX
# ============================================================

def update_ad_price(new_price):
    if not API_KEY:
        print("❌ API_KEY manquante.")
        return False

    if not SECRET_KEY:
        print("❌ SECRET_KEY manquante.")
        return False

    if not ADV_NO:
        print("❌ ADV_NO manquant.")
        return False

    # IMPORTANT:
    # Les paramètres restent dans cet ordre.
    # Ne jamais utiliser sorted(params.items()).
    params = {
        "advNo": ADV_NO,
        "price": f"{new_price:.2f}",
        "timestamp": int(time.time() * 1000),
        "recvWindow": 60000,
    }

    query_string, signature = sign_params(params)

    final_url = (
        f"{UPDATE_URL}?{query_string}"
        f"&signature={signature}"
    )

    try:
        response = requests.post(
            final_url,
            headers=HEADERS,
            timeout=15,
        )

        print(f"Modification - HTTP : {response.status_code}")
        print(f"Réponse Binance : {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()

                if result.get("success") is True:
                    print("✅ Prix de l'annonce mis à jour.")
                    return True

            except ValueError:
                pass

        if response.status_code == 401:
            print()
            print("❌ Binance refuse encore la modification.")
            print("La lecture de l'annonce fonctionne, mais l'opération")
            print("d'écriture P2P est refusée.")
            print()

        return False

    except requests.RequestException as e:
        print(f"❌ Erreur réseau pendant la modification : {e}")
        return False


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    print("==============================================")
    print(" Bot Binance P2P - USDT/CDF - SELL")
    print("==============================================")

    if not API_KEY or not SECRET_KEY or not ADV_NO:
        print("❌ Variables manquantes.")
        print("Vérifie API_KEY, SECRET_KEY et ADV_NO.")
        return

    # Vérification de notre annonce.
    my_ad = get_my_ad()

    if not my_ad:
        print("❌ Impossible de lire ton annonce.")
        return

    my_price = float(my_ad.get("price", 0))
    trade_type = my_ad.get("tradeType")
    asset = my_ad.get("asset")
    fiat = my_ad.get("fiatUnit")
    status = my_ad.get("advStatus")

    print(f"Ton annonce : {trade_type} {asset}/{fiat}")
    print(f"Ton prix    : {my_price:.2f} CDF")
    print(f"Statut      : {status}")

    if trade_type != "SELL":
        print("❌ Cette version est prévue pour une annonce SELL.")
        return

    # Recherche du meilleur concurrent.
    market_price = get_best_competitor_price()

    if market_price is None:
        print("❌ Aucun prix concurrent exploitable trouvé.")
        return

    target_price = max(
        market_price - PRICE_STEP,
        FLOOR_PRICE,
    )

    print(f"Meilleur concurrent : {market_price:.2f} CDF")
    print(f"Prix ciblé          : {target_price:.2f} CDF")
    print(f"Prix minimum        : {FLOOR_PRICE:.2f} CDF")

    # Rien à modifier si nous sommes déjà au meilleur prix.
    if abs(target_price - my_price) < 0.000001:
        print("ℹ️ Ton annonce est déjà au prix ciblé.")
        return

    # Évite une modification inutile si le prix calculé est supérieur
    # au prix actuel : on ne remonte pas automatiquement le prix.
    if target_price >= my_price:
        print("ℹ️ Le prix ciblé n'est pas inférieur à ton prix actuel.")
        print("Aucune modification effectuée.")
        return

    print(f"🔄 Modification : {my_price:.2f} → {target_price:.2f} CDF")

    update_ad_price(target_price)


if __name__ == "__main__":
    main()
