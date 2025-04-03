DROP TABLE if exists tours;
DROP TABLE if exists hotels;
DROP TABLE if exists hotel_categories;
DROP TABLE if exists cities;
DROP TABLE if exists resorts;
DROP TABLE if exists meal_types;
DROP TABLE if exists countries;


CREATE TABLE meal_types (
    id INT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);


CREATE TABLE countries (
    id INT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    popular DECIMAL(5,2) DEFAULT 0 CHECK (popular >= 0)
);


CREATE TABLE resorts (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INT NOT NULL,
    CONSTRAINT fk_country FOREIGN KEY (country_id) REFERENCES countries(id)
);


CREATE TABLE hotel_categories (
    id INT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);


CREATE TABLE hotels (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    resort_id INT NOT NULL,
    hotel_category_id INT NOT NULL,
    rating DECIMAL(3,2) CHECK (rating BETWEEN 0 AND 5),
    image_url TEXT,
    
    CONSTRAINT fk_resort FOREIGN KEY (resort_id) REFERENCES resorts(id),
    CONSTRAINT fk_hotel_category FOREIGN KEY (hotel_category_id) REFERENCES hotel_categories(id)
);


CREATE TABLE cities (
    id INT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);


CREATE TABLE tours (
    id INT PRIMARY KEY,
    country_id INT NOT NULL,
    departure_city_id INT NOT NULL,
    resort_id INT NOT NULL,
    hotel_id INT NOT NULL,
    hotel_category_id INT NOT NULL,
    hotel_rating DECIMAL(3,2) CHECK (hotel_rating BETWEEN 0 AND 5),
    meal_type_id INT NOT NULL,
    nights INT CHECK (nights > 0),
    checkin_date DATE NOT NULL,
    publish_date DATE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    available_until DATE NOT NULL,
    booking_url TEXT NOT NULL,

    CONSTRAINT fk_country FOREIGN KEY (country_id) REFERENCES countries(id),
    CONSTRAINT fk_city FOREIGN KEY (departure_city_id) REFERENCES cities(id),
    CONSTRAINT fk_resort FOREIGN KEY (resort_id) REFERENCES resorts(id),
    CONSTRAINT fk_hotel FOREIGN KEY (hotel_id) REFERENCES hotels(id),
    CONSTRAINT fk_hotel_category FOREIGN KEY (hotel_category_id) REFERENCES hotel_categories(id),
    CONSTRAINT fk_meal_type FOREIGN KEY (meal_type_id) REFERENCES meal_types(id)
);
