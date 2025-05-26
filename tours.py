import requests
import psycopg2
from datetime import datetime, timedelta
from itertools import product
import sys

DB_CONFIG = {
    "dbname": "pg_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_all(conn, query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def insert_tour(conn, tour, params):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO hotels (id, name, resort_id, hotel_category_id, rating, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (
                tour["hotelId"],
                tour["hotelName"],
                tour["resortId"],
                tour["hotelCategory"],
                float(tour["hotelRating"] or 0),
                f"https:{tour['hotelPreview']}"
            ))

            cur.execute("""
                INSERT INTO tours (
                    id, country_id, departure_city_id, resort_id, hotel_id, hotel_category_id,
                    hotel_rating, meal_type_id, nights, checkin_date, publish_date, price,
                    available_until, booking_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (
                tour["tourIdentity"],
                params["country_id"],
                params["departure_city_id"],
                tour["resortId"],
                tour["hotelId"],
                tour["hotelCategory"],
                float(tour["hotelRating"] or 0),
                tour["mealId"],
                tour["nights"],
                tour["checkinDate"],
                tour["publishedAt"].split()[0],
                float(tour["price"]),
                tour["expired"].split()[0],
                tour["tourPageUrl"]
            ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\n[!] DB Insert Error: {e}")

def build_url(params, checkin_from, checkin_to):
    base = "https://api-gateway.travelata.ru/statistic/cheapestTours?"
    query = {
        "countries[]": params["country_id"],
        "departureCity": params["departure_city_id"],
        "nightRange[from]": params["night_from"],
        "nightRange[to]": params["night_to"],
        "touristGroup[adults]": params["adults"],
        "touristGroup[kids]": params["kids"],
        "touristGroup[infants]": params["infants"],
        "checkInDateRange[from]": checkin_from,
        "checkInDateRange[to]": checkin_to
    }
    return base + "&".join(f"{k}={v}" for k, v in query.items())

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    inserted_total = 0

    countries = fetch_all(conn, "SELECT id FROM countries WHERE popular > 0")
    cities = fetch_all(conn, "SELECT id FROM cities WHERE id < 3")

    today = datetime.today()
    checkin_periods = [(today + timedelta(days=i), today + timedelta(days=i+7)) for i in range(30)]

    combos = product(
        countries,
        cities,
        [(1,0,0), (1,0,1), (1,0,2), (1,1,0), (1,1,1), (1,2,0), (1,2,1), (1,2,2),
         (2,0,0), (2,0,1), (2,0,2), (2,1,0), (2,1,1), (2,1,2), (2,2,0), (2,2,1), (2,2,2)],
        [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (2, 3), (2, 4), (2, 5),
         (2, 6), (2, 7), (3, 4), (3, 5), (3, 6), (3, 7)]
    )

    for (country,), (city,), (adults, kids, infants), (night_from, night_to) in combos:
        for checkin_start, checkin_end in checkin_periods:
            params = {
                "country_id": country,
                "departure_city_id": city,
                "adults": adults,
                "kids": kids,
                "infants": infants,
                "night_from": night_from,
                "night_to": night_to
            }

            sys.stdout.write(
                f"\r[*] Processing: country={country}, city={city}, "
                f"nights=({night_from}-{night_to}), adults={adults}, kids={kids}, infants={infants}, "
                f"checkin=({checkin_start.date()} to {checkin_end.date()})  inserted already {inserted_total}"
            )
            sys.stdout.flush()

            try:
                url = build_url(params, checkin_start.date(), checkin_end.date())
                resp = requests.get(url, headers=HEADERS, timeout=20)
                data = resp.json()
                if data.get("success") and data.get("data"):
                    for tour in data["data"]:
                        insert_tour(conn, tour, params)
                        inserted_total += 1
                        if inserted_total >= 1000:
                            print(f"\n[✓] Reached 1000 inserted tours. Exiting.")
                            conn.close()
                            sys.exit(0)
                    print(f"\n[+] Inserted total: {inserted_total} — from: {url}")
            except Exception as e:
                print(f"\n[!] Error fetching: {url} — {e}")

    conn.close()

if __name__ == "__main__":
    main()
