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
# # https://api-gateway.travelata.ru/statistic/cheapestTours
# # ?countries[]=92
# # &departureCity=2
# # &nightRange[from]=4
# # &resorts[]=2175
# # &nightRange[to]=10
# # &touristGroup[adults]=2
# # &touristGroup[kids]=0
# # &touristGroup[infants]=0
# # &hotelCategories[]=2
# # &hotelCategories[]=7
# # &checkInDateRange[from]=2023-01-13
# # &checkInDateRange[to]=2023-01-15
# import requests

# def fetch_countries():
#     url = "https://api-gateway.travelata.ru/directory/countries"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#     }
#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         data = response.json()
        
#         if data.get("success"):
#             for country in data.get("data", []):
#                 print(f"ID: {country['id']}, Name: {country['name']}, Popularity: {country.get('popular', 'N/A')}")
#         else:
#             print("Error:", data.get("message", "Unknown error"))
#     except requests.exceptions.RequestException as e:
#         print("Request failed:", e)

# def fetch_resorts():
#     url = "https://api-gateway.travelata.ru/directory/resorts"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#     }
#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         data = response.json()
        
#         if data.get("success"):
#             for resort in data.get("data", []):
#                 print(f"ID: {resort['id']}, Name: {resort['name']}, Popular: {resort['isPopular']}, Country ID: {resort['countryId']}, At Filtering: {resort['atFiltering']}")
#         else:
#             print("Error:", data.get("message", "Unknown error"))
#     except requests.exceptions.RequestException as e:
#         print("Request failed:", e)

# if __name__ == "__main__":
#     print("Fetching countries...")
#     fetch_countries()
#     print("\nFetching resorts...")
#     fetch_resorts()
import requests
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "dbname": "pg_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

HOTEL_CATEGORIES_API_URL = "http://api-gateway.travelata.ru/directory/hotelCategories"
MEAL_TYPES_API_URL = "https://api-gateway.travelata.ru/directory/meals"

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
        
        conn.commit()
        cur.close()
        print(f"Данные успешно загружены в таблицу {table_name}.")
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
