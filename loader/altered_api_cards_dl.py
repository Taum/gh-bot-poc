import requests
import time
import os
import json
import concurrent.futures
from ratelimit import limits, sleep_and_retry
from itertools import product
import math
import sys

url = "https://api.altered.gg/cards"
locales = ["en-us", "fr-fr", "de-de", "es-es", "it-it"]
main_locale = locales[0]

card_sets = ["BISE"]
mainCosts = [3]
factions = ["AX", "BR", "LY", "MU", "OR", "YZ"]
rarities = ["UNIQUE"]

max_cards_to_process = 5

# Rate limits for Altered.gg API calls
rate_limits = {
    "calls": 3,
    "period": 5
}

root_dir = sys.argv[1]

cards_folder = os.path.join(root_dir, "cards_data")
index_file = os.path.join(cards_folder, "index.json")
os.makedirs(cards_folder, exist_ok=True)

if os.path.exists(index_file):
    with open(index_file, "r", encoding="utf-8") as f:
        saved_ids = set(json.load(f))
else:
    saved_ids = set()

all_card_ids = set()


# Fetches from the API with rate limiting
@sleep_and_retry
@limits(**rate_limits)
def rate_limited_get(url, params = None):
    return requests.get(url, params=params)

def fetch_cards_for_combination(card_set, mainCost, faction, rarity):
    current_page = 1
    total_items = None
    combo_card_ids = []

    while True:
        params = {
            "cardSet[]": card_set,
            "cardType[]": ["CHARACTER"],
            "factions[]": faction,
            "mainCost[]": mainCost,
            "rarity[]": rarity,
            "locale": main_locale,
            "itemsPerPage": 36,
        }

        if current_page > 1:
            params["page"] = current_page
        else:
            params.pop("page", None)

        response = rate_limited_get(url, params=params)
        if response.status_code != 200:
            print(f"Error fetching page {current_page} for combo {card_set}, {mainCost}, {faction}, {rarity}: {response.status_code}")
            break

        data = response.json()

        if total_items is None:
            total_items = data.get("hydra:totalItems", 0)
            print(f"🔍 Total items for combo {card_set}, {mainCost}, {faction}, {rarity}: {total_items}")

            max_pages = math.ceil(max_cards_to_process / 36)

        members = data.get("hydra:member", [])
        if not members:
            break

        for card in members:
            ref = card.get("reference") or card.get("id")
            if ref:
                combo_card_ids.append(ref)

        print(f"Page {current_page} fetched for combo {card_set}, {mainCost}, {faction}, {rarity} ({len(members)} cards)")

        if len(combo_card_ids) >= max_cards_to_process:
            print(f"Reached max_cards_to_process ({max_cards_to_process}) for this combo, stopping.")
            break

        if current_page >= max_pages:
            print(f"Reached max pages ({max_pages}) for this combo, stopping.")
            break

        current_page += 1
        time.sleep(1)

    return combo_card_ids[:max_cards_to_process]

def fetch_locale(card_id, loc):
    loc_url = f"{url}/{card_id}?locale={loc}"
    resp = rate_limited_get(loc_url)
    if resp.status_code == 200:
        print(f"🌍 {card_id} : {loc} fetched")
        return loc, resp.json()
    else:
        print(f"❌ Error {loc} for {card_id}: {resp.status_code}")
        return loc, None

def path_for_card_id(card_id):
    # part: 0   1    2 3  4  5 6
    #       ALT_CORE_B_AX_04_U_1234
    # output: CORE/AX/04/ALT_CORE_B_AX_04_U_1234.json
    #         CORE/AX/04/ALT_CORE_B_AX_04_C.json
    parts = card_id.split("_")
    if len(parts) == 6 or len(parts) == 7:
        path = os.path.join(parts[1], parts[3], parts[4])
    else:
        raise ValueError(f"Invalid card_id: {card_id}")
    return path

def dict_recursive_diff(dict1, dict2):
    """
    Recursively compares two dictionaries and return a dictionary with only 
    the keys and values of dict2 that have a different value from dict1.
    """
    diff = {}
    for key in dict2:
        if key not in dict1:
            diff[key] = dict2[key]
        elif isinstance(dict2[key], dict) and isinstance(dict1[key], dict):
            sub_diff = dict_recursive_diff(dict1[key], dict2[key])
            if len(sub_diff) > 0:
                diff[key] = sub_diff
        elif dict2[key] != dict1[key]:
            diff[key] = dict2[key]
    return diff


for card_set, mainCost, faction, rarity in product(card_sets, mainCosts, factions, rarities):
    card_ids = fetch_cards_for_combination(card_set, mainCost, faction, rarity)
    all_card_ids.update(card_ids)

print(f"Total unique cards fetched: {len(all_card_ids)}")

new_cards_processed = 0

for card_id in all_card_ids:
    if new_cards_processed >= max_cards_to_process:
        print(f"⏹️ Reached max cards to process: {max_cards_to_process}")
        break

    path = path_for_card_id(card_id)
    os.makedirs(os.path.join(root_dir, path), exist_ok=True)
    file_path = os.path.join(root_dir, path, f"{card_id}.json")

    if os.path.exists(file_path):
        print(f"⏭ Already loaded: {card_id} @ {file_path}")
        continue

    new_cards_processed += 1

    print(f"🔍 Fetching {card_id} -> {path}")
    
    _, card_data = fetch_locale(card_id, main_locale)
    card_data["translations"] = {}

    locales_to_fetch = locales[1:]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_locale, card_id, loc) for loc in locales_to_fetch]
        results = []
        error_occurred = False
        for future in concurrent.futures.as_completed(futures):
            loc, data_loc = future.result()
            if data_loc is None:
                print(f"❌ Fetch error for {card_id} locale {loc}, skipping this card.")
                error_occurred = True
                break
            results.append((loc, data_loc))

        if error_occurred:
            continue

        for loc, data_loc in results:
            translated_keys = dict_recursive_diff(card_data, data_loc)
            card_data["translations"][loc] = translated_keys

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2, sort_keys=True)

    saved_ids.add(card_id)
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(sorted(saved_ids), f, ensure_ascii=False, indent=2)

    print(f"✅ Finished for {card_id}")
    # time.sleep(1)

print("\n✅ Fetch complete with translations and indexing.")