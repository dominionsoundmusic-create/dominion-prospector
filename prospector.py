#!/usr/bin/env python3
"""
Dominion AI Prospector — Daily Multi-Search
Fixed: uses hardcoded city coordinates instead of geocoding API
Runs 4 searches per day = 80 leads/day into GHL
"""

import requests, json, time, datetime, os

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'AIzaSyAQj2J72P12CSfPb4eQmfBLEXjeEdBAE5E')
GHL_API_KEY           = os.environ.get('GHL_API_KEY', 'pit-ce021c57-bbf2-495f-9a19-8830d8c59c2b')
GHL_LOCATION_ID       = os.environ.get('GHL_LOCATION_ID', 'T2jYdY6yKrpGB5DjiWqp')
GHL_BASE              = "https://services.leadconnectorhq.com"
RESULTS_PER_SEARCH    = 20
SEARCHES_PER_DAY      = 4

# ============================================================
# HARDCODED CITY COORDINATES — no geocoding API needed
# ============================================================
CITY_COORDS = {
    "Dallas, Texas":           (32.7767, -96.7970),
    "Houston, Texas":          (29.7604, -95.3698),
    "Austin, Texas":           (30.2672, -97.7431),
    "San Antonio, Texas":      (29.4241, -98.4936),
    "Fort Worth, Texas":       (32.7555, -97.3308),
    "Plano, Texas":            (33.0198, -96.6989),
    "Arlington, Texas":        (32.7357, -97.1081),
    "Lubbock, Texas":          (33.5779, -101.8552),
    "El Paso, Texas":          (31.7619, -106.4850),
    "Corpus Christi, Texas":   (27.8006, -97.3964),
    "Waco, Texas":             (31.5493, -97.1467),
    "Tyler, Texas":            (32.3513, -95.3011),
    "Beaumont, Texas":         (30.0802, -94.1266),
    "Longview, Texas":         (32.5007, -94.7405),
    "Lufkin, Texas":           (31.3382, -94.7291),
    "Nacogdoches, Texas":      (31.6035, -94.6557),
    "Wichita Falls, Texas":    (33.9137, -98.4934),
    "Abilene, Texas":          (32.4488, -99.7331),
    "Midland, Texas":          (31.9973, -102.0779),
    "Odessa, Texas":           (31.8457, -102.3676),
    "Amarillo, Texas":         (35.2220, -101.8313),
    "Laredo, Texas":           (27.5036, -99.5075),
    "McAllen, Texas":          (26.2034, -98.2300),
    "Brownsville, Texas":      (25.9017, -97.4975),
    "Killeen, Texas":          (31.1171, -97.7278),
    "Round Rock, Texas":       (30.5083, -97.6789),
    "Denton, Texas":           (33.2148, -97.1331),
    "Lewisville, Texas":       (33.0462, -96.9942),
    "McKinney, Texas":         (33.1972, -96.6397),
    "Frisco, Texas":           (33.1507, -96.8236),
    "Atlanta, Georgia":        (33.7490, -84.3880),
    "Charlotte, North Carolina": (35.2271, -80.8431),
    "Nashville, Tennessee":    (36.1627, -86.7816),
    "Phoenix, Arizona":        (33.4484, -112.0740),
    "Denver, Colorado":        (39.7392, -104.9903),
    "Las Vegas, Nevada":       (36.1699, -115.1398),
    "Oklahoma City, Oklahoma": (35.4676, -97.5164),
    "Tulsa, Oklahoma":         (36.1540, -95.9928),
    "Memphis, Tennessee":      (35.1495, -90.0490),
    "Louisville, Kentucky":    (38.2527, -85.7585),
    "Birmingham, Alabama":     (33.5186, -86.8104),
    "Jackson, Mississippi":    (32.2988, -90.1848),
    "Little Rock, Arkansas":   (34.7465, -92.2896),
    "Baton Rouge, Louisiana":  (30.4515, -91.1871),
    "New Orleans, Louisiana":  (29.9511, -90.0715),
    "Shreveport, Louisiana":   (32.5252, -93.7502),
    "Columbia, South Carolina": (34.0007, -81.0348),
    "Greenville, South Carolina": (34.8526, -82.3940),
    "Knoxville, Tennessee":    (35.9606, -83.9207),
    "Chattanooga, Tennessee":  (35.0456, -85.3097),
}

NICHES = [
    "HVAC companies",
    "plumbing companies",
    "roofing contractors",
    "electricians",
    "auto repair shops",
    "law firms",
    "dental offices",
    "restaurants",
    "real estate agents",
    "landscaping companies",
    "pest control companies",
    "cleaning services",
    "insurance agents",
    "accounting firms",
    "chiropractic offices",
    "hair salons",
    "veterinary clinics",
    "home remodeling contractors",
    "painting contractors",
    "pool service companies",
]

CITIES = list(CITY_COORDS.keys())

def get_todays_searches():
    day = datetime.datetime.now().timetuple().tm_yday
    searches = []
    for i in range(SEARCHES_PER_DAY):
        niche_idx = (day * 4 + i * 7) % len(NICHES)
        city_idx  = (day * 3 + i * 11) % len(CITIES)
        city = CITIES[city_idx]
        lat, lng = CITY_COORDS[city]
        searches.append({
            "query": NICHES[niche_idx],
            "location": city,
            "lat": lat,
            "lng": lng,
            "tag": f"prospected-{NICHES[niche_idx].replace(' ','-').lower()}"
        })
    return searches

def search_places(query, location, lat, lng, max_results=20):
    """Search using lat/lng directly — no geocoding needed"""
    all_results = []
    next_page_token = None
    
    while len(all_results) < max_results:
        params = {
            "query": f"{query} near {location}",
            "location": f"{lat},{lng}",
            "radius": "50000",
            "key": GOOGLE_PLACES_API_KEY,
        }
        if next_page_token:
            params = {"pagetoken": next_page_token, "key": GOOGLE_PLACES_API_KEY}
            time.sleep(2)
        
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params
        ).json()
        
        results = resp.get('results', [])
        all_results.extend(results)
        next_page_token = resp.get('next_page_token')
        
        if not next_page_token or len(all_results) >= max_results:
            break
    
    return all_results[:max_results]

def get_place_details(place_id):
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={
            "place_id": place_id,
            "fields": "name,formatted_phone_number,website,formatted_address,rating,user_ratings_total",
            "key": GOOGLE_PLACES_API_KEY,
        }
    ).json()
    return resp.get('result', {})

def create_ghl_contact(business, tag, query, location):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    name    = business.get('name', 'Unknown')
    phone   = business.get('formatted_phone_number', '')
    website = business.get('website', '')
    address = business.get('formatted_address', '')
    rating  = business.get('rating', '')
    reviews = business.get('user_ratings_total', 0)

    phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    if phone_clean and not phone_clean.startswith('+'):
        phone_clean = '+1' + phone_clean

    pitch_web    = "NO WEBSITE — pitch Web Design Pro ($497 free demo)" if not website else "Has website — check quality"
    pitch_review = "LOW RATING — pitch Review Pro ($197/mo)" if rating and float(str(rating)) < 4.5 else "Good rating — offer Review Pro to maintain"

    note = f"""👑 DOMINION AI PROSPECTOR

Business: {name}
Search: {query} in {location}
Rating: {rating}/5 ({reviews} reviews)
Phone: {phone or 'None'}
Website: {website or 'NONE'}
Address: {address}

PITCH:
{pitch_web}
{pitch_review}
📞 AI Voice Agent Pros ($297/mo)
🤖 Dominion AI Agency ($497/mo)"""

    payload = {
        "locationId": GHL_LOCATION_ID,
        "firstName": name,
        "name": name,
        "phone": phone_clean or None,
        "website": website or None,
        "address1": address,
        "tags": [tag, "auto-prospected", query.replace(' ','-').lower()],
        "source": "Dominion AI Prospector",
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        resp = requests.post(f"{GHL_BASE}/contacts/", headers=headers, json=payload)
        if resp.status_code in [200, 201]:
            contact_id = resp.json().get('contact', {}).get('id')
            if contact_id:
                requests.post(
                    f"{GHL_BASE}/contacts/{contact_id}/notes",
                    headers=headers,
                    json={"body": note}
                )
            return contact_id, True
        return None, False
    except Exception as e:
        print(f"GHL error: {e}")
        return None, False

def run():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"\n{'='*60}")
    print(f"👑 DOMINION AI PROSPECTOR — {today}")
    print(f"{'='*60}")

    searches = get_todays_searches()
    total_added = 0

    for i, search in enumerate(searches):
        query    = search['query']
        location = search['location']
        lat      = search['lat']
        lng      = search['lng']
        tag      = search['tag']

        print(f"\n[Search {i+1}/{SEARCHES_PER_DAY}] {query} in {location}")
        print(f"  Coords: {lat}, {lng}")

        places = search_places(query, location, lat, lng, RESULTS_PER_SEARCH)
        print(f"  Found {len(places)} businesses")

        added = 0
        for place in places:
            name = place.get('name', 'Unknown')
            place_id = place.get('place_id')
            details = get_place_details(place_id)
            time.sleep(0.1)

            contact_id, created = create_ghl_contact(details, tag, query, location)
            if created:
                added += 1
                print(f"  ✅ {name}")
            else:
                print(f"  ⚠️  {name} (skipped)")

        total_added += added
        print(f"  Added: {added} leads")
        if i < len(searches) - 1:
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"👑 DONE — {total_added} new leads added to GHL")
    print(f"Monthly pace: ~{total_added * 30} leads/month")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run()
