#!/usr/bin/env python3
"""
Dominion AI Prospector — Daily Multi-Search
Uses Google Places API (New) — places.googleapis.com/v1/places:searchText
"""

import requests, json, time, datetime, os

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'AIzaSyAQj2J72P12CSfPb4eQmfBLEXjeEdBAE5E')
GHL_API_KEY           = os.environ.get('GHL_API_KEY', 'pit-ce021c57-bbf2-495f-9a19-8830d8c59c2b')
GHL_LOCATION_ID       = os.environ.get('GHL_LOCATION_ID', 'T2jYdY6yKrpGB5DjiWqp')
GHL_BASE              = "https://services.leadconnectorhq.com"
RESULTS_PER_SEARCH    = 20
SEARCHES_PER_DAY      = 4

CITY_COORDS = {
    "Dallas, Texas":             (32.7767, -96.7970),
    "Houston, Texas":            (29.7604, -95.3698),
    "Austin, Texas":             (30.2672, -97.7431),
    "San Antonio, Texas":        (29.4241, -98.4936),
    "Fort Worth, Texas":         (32.7555, -97.3308),
    "Plano, Texas":              (33.0198, -96.6989),
    "Arlington, Texas":          (32.7357, -97.1081),
    "Lubbock, Texas":            (33.5779, -101.8552),
    "El Paso, Texas":            (31.7619, -106.4850),
    "Corpus Christi, Texas":     (27.8006, -97.3964),
    "Waco, Texas":               (31.5493, -97.1467),
    "Tyler, Texas":              (32.3513, -95.3011),
    "Beaumont, Texas":           (30.0802, -94.1266),
    "Longview, Texas":           (32.5007, -94.7405),
    "Lufkin, Texas":             (31.3382, -94.7291),
    "Nacogdoches, Texas":        (31.6035, -94.6557),
    "Wichita Falls, Texas":      (33.9137, -98.4934),
    "Abilene, Texas":            (32.4488, -99.7331),
    "Midland, Texas":            (31.9973, -102.0779),
    "Odessa, Texas":             (31.8457, -102.3676),
    "Amarillo, Texas":           (35.2220, -101.8313),
    "Laredo, Texas":             (27.5036, -99.5075),
    "McAllen, Texas":            (26.2034, -98.2300),
    "Brownsville, Texas":        (25.9017, -97.4975),
    "Killeen, Texas":            (31.1171, -97.7278),
    "Round Rock, Texas":         (30.5083, -97.6789),
    "Denton, Texas":             (33.2148, -97.1331),
    "Lewisville, Texas":         (33.0462, -96.9942),
    "McKinney, Texas":           (33.1972, -96.6397),
    "Frisco, Texas":             (33.1507, -96.8236),
    "Atlanta, Georgia":          (33.7490, -84.3880),
    "Charlotte, North Carolina": (35.2271, -80.8431),
    "Nashville, Tennessee":      (36.1627, -86.7816),
    "Phoenix, Arizona":          (33.4484, -112.0740),
    "Denver, Colorado":          (39.7392, -104.9903),
    "Las Vegas, Nevada":         (36.1699, -115.1398),
    "Oklahoma City, Oklahoma":   (35.4676, -97.5164),
    "Tulsa, Oklahoma":           (36.1540, -95.9928),
    "Memphis, Tennessee":        (35.1495, -90.0490),
    "Louisville, Kentucky":      (38.2527, -85.7585),
    "Birmingham, Alabama":       (33.5186, -86.8104),
    "Jackson, Mississippi":      (32.2988, -90.1848),
    "Little Rock, Arkansas":     (34.7465, -92.2896),
    "Baton Rouge, Louisiana":    (30.4515, -91.1871),
    "New Orleans, Louisiana":    (29.9511, -90.0715),
    "Shreveport, Louisiana":     (32.5252, -93.7502),
    "Columbia, South Carolina":  (34.0007, -81.0348),
    "Greenville, South Carolina":(34.8526, -82.3940),
    "Knoxville, Tennessee":      (35.9606, -83.9207),
    "Chattanooga, Tennessee":    (35.0456, -85.3097),
}

NICHES = [
    "HVAC companies", "plumbing companies", "roofing contractors",
    "electricians", "auto repair shops", "law firms", "dental offices",
    "restaurants", "real estate agents", "landscaping companies",
    "pest control companies", "cleaning services", "insurance agents",
    "accounting firms", "hair salons", "veterinary clinics",
    "home remodeling contractors", "painting contractors",
    "pool service companies", "HVAC repair",
]

CITIES = list(CITY_COORDS.keys())

def get_todays_searches():
    day = datetime.datetime.now().timetuple().tm_yday
    searches = []
    for i in range(SEARCHES_PER_DAY):
        niche = NICHES[(day * 4 + i * 7) % len(NICHES)]
        city  = CITIES[(day * 3 + i * 11) % len(CITIES)]
        lat, lng = CITY_COORDS[city]
        searches.append({
            "query": niche,
            "location": city,
            "lat": lat,
            "lng": lng,
            "tag": f"prospected-{niche.replace(' ','-')}"
        })
    return searches

def search_places_new(query, lat, lng, location, max_results=20):
    """Use Places API (New) — places.googleapis.com/v1/places:searchText"""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.id"
    }
    body = {
        "textQuery": f"{query} in {location}",
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": 40000.0
            }
        },
        "maxResultCount": min(max_results, 20)
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        print(f"  API status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            places = data.get("places", [])
            print(f"  Raw results: {len(places)}")
            return places
        else:
            print(f"  API error: {resp.text[:200]}")
            return []
    except Exception as e:
        print(f"  Request error: {e}")
        return []

def create_ghl_contact(place, tag, query, location):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

    # Places API New uses different field names
    name    = place.get("displayName", {}).get("text", "Unknown") if isinstance(place.get("displayName"), dict) else place.get("displayName", "Unknown")
    phone   = place.get("nationalPhoneNumber", "")
    website = place.get("websiteUri", "")
    address = place.get("formattedAddress", "")
    rating  = place.get("rating", "N/A")
    reviews = place.get("userRatingCount", 0)

    phone_clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if phone_clean and not phone_clean.startswith("+"):
        phone_clean = "+1" + phone_clean

    pitch = "NO WEBSITE — pitch Web Design Pro ($497 free demo)" if not website else "Has website — check quality, offer CRM/AI"
    if rating != "N/A" and float(str(rating)) < 4.5:
        pitch += " | LOW RATING — pitch Review Pro ($197/mo)"

    note = f"""👑 DOMINION PROSPECTOR

Business: {name}
Search: {query} in {location}
Rating: {rating}/5 ({reviews} reviews)
Phone: {phone or "None"}
Website: {website or "NONE"}
Address: {address}

PITCH: {pitch}
📞 AI Voice Agent Pros ($297/mo)
🤖 Dominion AI Agency ($497/mo)
🌐 Web Design Pro ($497)"""

    payload = {
        "locationId": GHL_LOCATION_ID,
        "firstName": name,
        "name": name,
        "tags": [tag, "auto-prospected", query.replace(' ','-').lower()],
        "source": "Dominion Prospector",
    }
    if phone_clean:  payload["phone"] = phone_clean
    if website:      payload["website"] = website
    if address:      payload["address1"] = address

    try:
        # Retry up to 3 times with backoff on 429
        for attempt in range(3):
            resp = requests.post(f"{GHL_BASE}/contacts/", headers=headers, json=payload, timeout=10)
            if resp.status_code in [200, 201]:
                contact_id = resp.json().get("contact", {}).get("id")
                if contact_id:
                    time.sleep(0.5)
                    requests.post(
                        f"{GHL_BASE}/contacts/{contact_id}/notes",
                        headers=headers,
                        json={"body": note},
                        timeout=10
                    )
                return contact_id, True
            elif resp.status_code == 429:
                wait = (attempt + 1) * 3
                print(f"  GHL rate limit — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  GHL {resp.status_code}: {resp.text[:100]}")
                return None, False
        return None, False
    except Exception as e:
        print(f"  GHL error: {e}")
        return None, False

def run():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"DOMINION PROSPECTOR — {today}")
    print(f"API Key: {'YES' if GOOGLE_PLACES_API_KEY else 'NO'}")
    print(f"Using: Places API (New)")
    print(f"{'='*60}")

    searches = get_todays_searches()
    total = 0

    for i, s in enumerate(searches):
        print(f"\n[{i+1}/{SEARCHES_PER_DAY}] {s['query']} in {s['location']}")
        places = search_places_new(s["query"], s["lat"], s["lng"], s["location"], RESULTS_PER_SEARCH)
        print(f"  Found: {len(places)}")

        added = 0
        for place in places:
            cid, ok = create_ghl_contact(place, s["tag"], s["query"], s["location"])
            if ok:
                name = place.get("displayName", {}).get("text", "?") if isinstance(place.get("displayName"), dict) else "?"
                print(f"  + {name}")
                added += 1
            time.sleep(1)

        total += added
        print(f"  Added: {added}")
        if i < len(searches) - 1:
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"DONE — {total} leads added to GHL today")
    print(f"Monthly pace: ~{total * 30}/month")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run()
