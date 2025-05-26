# #https://support.travelpayouts.com/hc/ru/articles/360022674591-API-%D0%BE%D1%82-Travelata

# # Параметры запроса
# # countries[] — id страны тура (можно получить с помощью запроса Список стран). Поддерживается только одна страна в запросе. При передаче нескольких стран будет сгенерирована ошибка;
# # departureCity — id города вылета (можно найти в файле Справочник городов вылета для API.xlsx);
# # nightRange[from] — минимальное количество ночей;
# # nightRange[to] — максимальное количество ночей;
# # resorts[] — массив уникальных идентификаторов курортов;
# # meals[] — массив уникальных идентификаторов типов питания;
# # touristGroup[adults] — количество взрослых;
# # touristGroup[kids] — количество детей (от 2 до 11 лет);
# # touristGroup[infants] — количество младенцев (до 2 лет);
# # hotelCategories[] — категория отеля (используется для фильтрации по категории отелей);
# # ratingMin — минимально допустимый рейтинг отеля. Дополняет ограничения по параметру hotelCategories;
# # ratingMax — максимально допустимый рейтинг отеля. Дополняет ограничения по параметру hotelCategories;
# # checkInDateRange[to], checkInDateRange[from] — период от и до дат заселения в отель.
# # Важно: Запрос на поиск туров возможен в интервале 30 дней (период между checkInDateRange[from] и checkInDateRange[to]).

# # Запрос
# https://api-gateway.travelata.ru/statistic/cheapestTours
# ?countries[]=92
# &departureCity=2
# &nightRange[from]=5
# &nightRange[to]=7
# &resorts[]=2175
# &touristGroup[adults]=2
# &touristGroup[kids]=0
# &touristGroup[infants]=0
# &hotelCategories[]=4
# &checkInDateRange[from]=2025-06-01
# &checkInDateRange[to]=2025-06-15

import requests
import psycopg2
from psycopg2 import sql
import pandas as pd

DB_CONFIG = {
    "dbname": "pg_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

HOTEL_CATEGORIES_API_URL = "http://api-gateway.travelata.ru/directory/hotelCategories"
MEAL_TYPES_API_URL = "https://api-gateway.travelata.ru/directory/meals"
COUNTRIES_API_URL = "https://api-gateway.travelata.ru/directory/countries"
RESORTS_API_URL = "https://api-gateway.travelata.ru/directory/resorts"

def insert_cities_from_excel(excel_path):
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        df = df.rename(columns={
            'Gate_DepartureCity_ID': 'id',
            'Gate_DepartureCity_Name': 'name'
        })

        # Удаляем строки с пустыми значениями ID или name
        df = df.dropna(subset=['id', 'name'])

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO cities (id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
                """, (int(row['id']), row['name']))
            except Exception as e:
                print(f"Ошибка при добавлении города {row['name']}: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()
        print(f"Успешно добавлено {len(df)} городов из Excel.")

    except Exception as e:
        print("Ошибка при чтении файла или работе с базой данных:", e)


def fetch_data(api_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            return data.get("data", [])
        else:
            print("Ошибка API:", data.get("message", "Unknown error"))
            return []
    except requests.exceptions.RequestException as e:
        print("Ошибка запроса:", e)
        return []

def insert_into_db(table_name, data):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for item in data:
            try:
                if table_name == "countries":
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (id, name, popular)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, popular = EXCLUDED.popular;
                        """).format(sql.Identifier(table_name)),
                        (item["id"], item["name"], item.get("popular", 0))
                    )

                elif table_name == "resorts":
                    # Проверяем наличие country_id в таблице countries
                    cur.execute("SELECT 1 FROM countries WHERE id = %s", (item["countryId"],))
                    if cur.fetchone() is None:
                        print(f"Пропущено {item['name']} — страна с id={item['countryId']} не найдена.")
                        continue

                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (id, name, country_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, country_id = EXCLUDED.country_id;
                        """).format(sql.Identifier(table_name)),
                        (item["id"], item["name"], item["countryId"])
                    )

                else:
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (id, name)
                            VALUES (%s, %s)
                            ON CONFLICT (id) DO NOTHING;
                        """).format(sql.Identifier(table_name)),
                        (item["id"], item["name"])
                    )

            except Exception as e:
                print(f"Ошибка при добавлении {item['name']} в {table_name}: {e}")
                continue  # продолжать, а не break

        conn.commit()
        cur.close()
        print(f"Данные успешно загружены в таблицу {table_name}.")

    except Exception as e:
        print("Ошибка при работе с базой данных:", e)

    finally:
        if conn:
            conn.close()

def fetch_and_insert_hotels():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Получаем все курорты из БД
        cur.execute("SELECT id FROM resorts;")
        resort_ids = [row[0] for row in cur.fetchall()]

        headers = {"User-Agent": "Mozilla/5.0"}

        for resort_id in resort_ids:
            url = f"https://api-gateway.travelata.ru/directory/resortHotels?resortId={resort_id}"
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if not data.get("success"):
                    print(f"[{resort_id}] Ошибка API: {data.get('message', 'Unknown error')}")
                    continue

                hotels = data.get("data", [])
                for hotel in hotels:
                    try:
                        cur.execute("""
                            INSERT INTO hotels (id, name, resort_id, hotel_category_id, rating, image_url)
                            VALUES (%s, %s, %s, %s, NULL, NULL)
                            ON CONFLICT (id) DO UPDATE
                            SET name = EXCLUDED.name,
                                resort_id = EXCLUDED.resort_id,
                                hotel_category_id = EXCLUDED.hotel_category_id;
                        """, (
                            hotel["id"],
                            hotel["name"],
                            hotel["resortId"],
                            hotel["hotelCategoryId"]
                        ))
                    except Exception as e:
                        print(f"Ошибка вставки отеля {hotel['name']} (id={hotel['id']}): {e}")
                        continue

                print(f"[{resort_id}] Загружено отелей: {len(hotels)}")

            except requests.RequestException as e:
                print(f"[{resort_id}] Ошибка запроса: {e}")
                continue

        conn.commit()
        cur.close()
        print("Все отели успешно загружены в базу данных.")

    except Exception as e:
        print("Ошибка при работе с базой данных:", e)
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    print("Получение категорий отелей...")
    hotel_categories = fetch_data(HOTEL_CATEGORIES_API_URL)
    if hotel_categories:
        print(f"Найдено {len(hotel_categories)} категорий. Добавление в базу данных...")
        insert_into_db("hotel_categories", hotel_categories)
    else:
        print("Нет данных для добавления.")
    
    print("\nПолучение типов питания...")
    meal_types = fetch_data(MEAL_TYPES_API_URL)
    if meal_types:
        print(f"Найдено {len(meal_types)} типов питания. Добавление в базу данных...")
        insert_into_db("meal_types", meal_types)
    else:
        print("Нет данных для добавления.")

    print("\nПолучение стран назначения...")
    countries = fetch_data(COUNTRIES_API_URL)
    if countries:
        print(f"Найдено {len(countries)} стран. Добавление в базу данных...")
        insert_into_db("countries", countries)
    else:
        print("Нет данных для добавления.")

    print("\nПолучение курортов...")
    resorts = fetch_data(RESORTS_API_URL)
    if resorts:
        print(f"Найдено {len(resorts)} курортов. Добавление в базу данных...")
        insert_into_db("resorts", resorts)
    else:
        print("Нет данных для добавления.")

    print("\nПолучение отелей по курортам...")
    # fetch_and_insert_hotels()
    print("\nПолучено 182173 отелей")

    print("\nДобавление городов из Excel...")
    insert_cities_from_excel("/home/asd/foo/spravochnik-gorodov-dlya-api-update.xlsx")
