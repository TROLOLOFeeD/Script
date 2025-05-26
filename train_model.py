import pandas as pd
import psycopg2
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from datetime import datetime, timedelta
import numpy as np

# === Ввод пользователя ===
user_nights = 7
user_adults = 2
user_teens = 1
user_children = 1

# Подключение к базе данных
conn = psycopg2.connect(
    dbname="pg_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

# Загрузка данных с JOIN на названия курортов
query = """
SELECT
    t.country_id,
    c.popular AS country_popular,
    t.departure_city_id,
    t.resort_id,
    r.name AS resort_name,
    t.hotel_id,
    t.hotel_category_id,
    t.hotel_rating,
    t.meal_type_id,
    t.nights,
    t.checkin_date,
    t.publish_date,
    t.price
FROM tours t
JOIN countries c ON t.country_id = c.id
JOIN resorts r ON t.resort_id = r.id
"""
df = pd.read_sql(query, conn)
conn.close()

# Преобразование дат
df['checkin_date'] = pd.to_datetime(df['checkin_date'])
df['publish_date'] = pd.to_datetime(df['publish_date'])
df['days_before_checkin'] = (df['checkin_date'] - df['publish_date']).dt.days

# Добавим данные о пассажирах
df['adults'] = np.random.randint(1, 3, size=len(df))
df['teens'] = np.random.randint(0, 2, size=len(df))
df['children'] = np.random.randint(0, 2, size=len(df))

# Признаки и цели
features = [
    'country_id', 'country_popular', 'departure_city_id',
    'resort_id', 'hotel_id', 'hotel_category_id',
    'hotel_rating', 'meal_type_id', 'nights',
    'adults', 'teens', 'children'
]
categorical = ['country_id', 'departure_city_id', 'resort_id', 'hotel_id', 'hotel_category_id', 'meal_type_id']
numeric = ['country_popular', 'hotel_rating', 'nights', 'adults', 'teens', 'children']

# Предобработка
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical)
])

# Модель 1: предсказание цены
X_price = df[features]
y_price = df['price']

pipeline_price = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# Модель 2: предсказание дней до покупки
y_days = df['days_before_checkin']
pipeline_days = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# Для модели предсказания цены
X_price_train, X_price_test, y_price_train, y_price_test = train_test_split(X_price, y_price, test_size=0.2, random_state=42)
pipeline_price.fit(X_price_train, y_price_train)

# Для модели предсказания дней до покупки
X_days_train, X_days_test, y_days_train, y_days_test = train_test_split(X_price, y_days, test_size=0.2, random_state=42)
pipeline_days.fit(X_days_train, y_days_train)

# Уникальные курорты и предсказания
results = []
today = datetime.today()

for resort_id in df['resort_id'].unique():
    resort_sample = df[df['resort_id'] == resort_id].iloc[0]

    input_data = {
        'country_id': resort_sample['country_id'],
        'country_popular': resort_sample['country_popular'],
        'departure_city_id': resort_sample['departure_city_id'],
        'resort_id': resort_id,
        'hotel_id': resort_sample['hotel_id'],
        'hotel_category_id': resort_sample['hotel_category_id'],
        'hotel_rating': resort_sample['hotel_rating'],
        'meal_type_id': resort_sample['meal_type_id'],
        'nights': user_nights,
        'adults': user_adults,
        'teens': user_teens,
        'children': user_children
    }

    input_df = pd.DataFrame([input_data])

    predicted_price = pipeline_price.predict(input_df)[0]
    predicted_days_before_checkin = int(pipeline_days.predict(input_df)[0])

    # Предположим ближайшую возможную дату заезда — через 30 дней
    checkin_date = today + timedelta(days=30)
    recommended_purchase_date = checkin_date - timedelta(days=predicted_days_before_checkin)

    results.append({
        'resort_name': resort_sample['resort_name'],
        'predicted_price': round(predicted_price, 2),
        'recommended_purchase_date': recommended_purchase_date.date()
    })

# Сортировка по цене
results_df = pd.DataFrame(results).sort_values(by='predicted_price')

# Вывод
print("Рекомендации по направлениям:")
print(results_df)
