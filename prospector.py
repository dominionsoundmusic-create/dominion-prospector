#!/usr/bin/env python3
"""
Dominion AI Prospector — Daily Multi-Search
Runs 4 searches per day across rotating niches and cities
= 80 leads/day, ~2,400/month
Stays within Google Places $200 free credit (well under limit)
Pushes all leads directly to GHL CRM with notes and tasks
"""

import requests, json, time, os, datetime

# ============================================================
# CONFIG
# ============================================================
GOOGLE_PLACES_API_KEY = "AIzaSyAQj2J72P12CSfPb4eQmfBLEXjeEdBAE5E"
GHL_API_KEY           = "pit-88ed5c87-1cdc-4eef-a7e0-42e6aaa7b855"
GHL_LOCATION_ID       = "T2jYdY6yKrpGB5DjiWqp"
GHL_BASE              = "https://services.leadconnectorhq.com"
RESULTS_PER_SEARCH    = 20   # Max per search before pagination costs more
SEARCHES_PER_DAY      = 4    # 4 x 20 = 80 leads/day, ~$5-6/month well under $200 free

# ============================================================
# ROTATING SEARCH QUEUE
# Cycles through niches + cities every day
# Never repeats the same combo back to back
# ============================================================

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

CITIES = [
    "Dallas, Texas",
    "Houston, Texas",
    "Austin, Texas",
    "San Antonio, Texas",
    "Fort Worth, Texas",
    "Plano, Texas",
    "Arlington, Texas",
    "Frisco, Texas",
    "McKinney, Texas",
    "Lubbock, Texas",
    "El Paso, Texas",
    "Corpus Christi, Texas",
    "Waco, Texas",
    "Tyler, Texas",
    "Beaumont, Texas",
    "Longview, Texas",
    "Lufkin, Texas",
    "Nacogdoches, Texas",
    "Wichita Falls, Texas",
    "Abilene, Texas",
    "Midland, Texas",
    "Odessa, Texas",
    "Amarillo, Texas",
    "Laredo, Texas",
    "McAllen, Texas",
    "Brownsville, Texas",
    "Killeen, Texas",
    "Round Rock, Texas",
    "Denton, Texas",
    "Lewisville, Texas",
    "Atlanta, Georgia",
    "Charlotte, North Carolina",
    "Nashville, Tennessee",
    "Phoenix, Arizona",
    "Denver, Colorado",
    "Las Vegas, Nevada",
    "Oklahoma City, Oklahoma",
    "Tulsa, Oklahoma",
    "Memphis, Tennessee",
    "Louisville, Kentucky",
    "Birmingham, Alabama",
    "Jackson, Mississippi",
    "Little Rock, Arkansas",
    "Baton Rouge, Louisiana",
    "New Orleans, Louisiana",
    "Shreveport, Louisiana",
    "Columbia, South Carolina",
    "Greenville, South Carolina",
    "Knoxville, Tennessee",
    "Chattanooga, Tennessee",
]

def get_todays_searches():
    """Pick 4 unique niche+city combos based on today's date so it rotates daily"""
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    searches = []
    for i in range(SEARCHES_PER_DAY):
        niche_idx = (day_of_year * 4 + i * 7) % len(NICHES)
        city_idx  = (day_of_year * 3 + i * 11) % len(CITIES)
        searches.append({
            "query": NICHES[niche_idx],
            "location": CITIES[city_idx],
            "tag": f"prospected-{NICHES[niche_idx].replace(' ','-').lower()}-{CITIES[city_idx].split(',')[0].replace(' ','-').lower()}"
        })
    return searches

# ============================================================
# GOOGLE PLACES FUNCTIONS
# ============================================================

def geocode(location):
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": location, "key": GOOGLE_PLACES_API_KEY}
    ).json()
    if resp.get('results'):
        loc = resp['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None

def search_places(query, location, max_results=20):
    lat, lng = geocode(location)
    if not lat:
        print(f"  ❌ Could not geocode {location}")
        return []
    all_results = []
    next_page_token = None
    while len(all_results) < max_results:
        params = {
            "query": f"{query} in {location}",
            "key": GOOGLE_PLACES_API_KEY,
        }
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params
        ).json()
        all_results.extend(resp.get('results', []))
        next_page_token = resp.get('next_page_token')
        if not next_page_token or len(all_results) >= max_results:
            break
    return all_results[:max_results]

def get_place_details(place_id):
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={
            "place_id": place_id,
            "fields": "name,formatted_phone_number,website,formatted_address,rating,user_ratings_total,business_status",
            "key": GOOGLE_PLACES_API_KEY,
        }
    ).json()
    return resp.get('result', {})

# ============================================================
# GHL FUNCTIONS
# ============================================================

def create_ghl_contact(business, tag, query, location):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    name    = business.get('name', 'Unknown Business')
    phone   = business.get('formatted_phone_number', '')
    website = business.get('website', '')
    address = business.get('formatted_address', '')
    rating  = business.get('rating', '')
    reviews = business.get('user_ratings_total', 0)

    phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    if phone_clean and not phone_clean.startswith('+'):
        phone_clean = '+1' + phone_clean

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
            return resp.json().get('contact', {}).get('id'), True
        return None, False
    except:
        return None, False

def add_note(contact_id, business, query, location):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    name    = business.get('name', '')
    rating  = business.get('rating', 'N/A')
    reviews = business.get('user_ratings_total', 0)
    website = business.get('website', '')
    phone   = business.get('formatted_phone_number', 'No phone')
    address = business.get('formatted_address', '')

    pitch_web    = "❌ NO WEBSITE — Lead with Web Design Pro ($497 free demo)" if not website else "✅ Has website — check quality, may need redesign"
    pitch_review = "⭐ LOW RATING — Lead with Review Pro ($197/mo)" if rating != 'N/A' and float(rating) < 4.5 else "⭐ Good rating — offer Review Pro to maintain it"

    note = f"""👑 DOMINION AI PROSPECTOR — AUTO-PROSPECTED LEAD

Business: {name}
Search: {query} in {location}
Google Rating: {rating}/5 ({reviews} reviews)
Phone: {phone}
Website: {website if website else 'NONE'}
Address: {address}

PITCH STRATEGY:
{pitch_web}
{pitch_review}
📞 AI Voice Agent Pros ($297/mo) — answers every call 24/7
🤖 Dominion AI Agency ($497/mo) — full automation stack

NEXT STEPS:
- Sarah follows up via SMS once A2P approved
- If no website, offer free demo at DominionWebDesignPro.com
- If low rating, show them our review automation demo"""

    try:
        requests.post(
            f"{GHL_BASE}/contacts/{contact_id}/notes",
            headers=headers,
            json={"body": note, "userId": GHL_LOCATION_ID}
        )
    except:
        pass

def create_task(contact_id, business_name):
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    due = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=9, minute=0, second=0)
    try:
        requests.post(
            f"{GHL_BASE}/contacts/{contact_id}/tasks",
            headers=headers,
            json={
                "title": f"Follow up — {business_name}",
                "body": "Auto-prospected. See note for pitch strategy.",
                "assignedTo": GHL_LOCATION_ID,
                "dueDate": due.isoformat() + "Z",
                "completed": False
            }
        )
    except:
        pass

# ============================================================
# MAIN
# ============================================================

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
        tag      = search['tag']

        print(f"\n[Search {i+1}/{SEARCHES_PER_DAY}] {query} in {location}")

        places = search_places(query, location, RESULTS_PER_SEARCH)
        print(f"  Found {len(places)} businesses")

        search_added = 0
        for place in places:
            name     = place.get('name', 'Unknown')
            place_id = place.get('place_id')
            details  = get_place_details(place_id)
            time.sleep(0.1)

            contact_id, created = create_ghl_contact(details, tag, query, location)
            if created and contact_id:
                add_note(contact_id, details, query, location)
                create_task(contact_id, name)
                search_added += 1
                print(f"  ✅ {name}")
            else:
                print(f"  ⚠️  {name} (skipped — may already exist)")

        total_added += search_added
        print(f"  Added {search_added} leads from this search")

        # Pause between searches to be safe on rate limits
        if i < len(searches) - 1:
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"👑 DONE — {total_added} new leads added to GHL today")
    print(f"📅 Searches run: {SEARCHES_PER_DAY} x {RESULTS_PER_SEARCH} = up to {SEARCHES_PER_DAY * RESULTS_PER_SEARCH} leads")
    print(f"📆 Monthly pace: ~{total_added * 30} leads/month")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run()
