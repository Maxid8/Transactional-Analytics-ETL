CREATE TABLE date (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year SMALLINT NOT NULL,
    quarter CHAR(2) NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(12) NOT NULL,
    week SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    day_name VARCHAR(9) NOT NULL
);

CREATE TABLE customer (
    customer_id INT PRIMARY KEY,
    cc_num BIGINT NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender CHAR(1),
    job VARCHAR(100),
    dob DATE NOT NULL,
    street VARCHAR(100),
    city VARCHAR(100),
    state CHAR(2),
    zip INT
);

CREATE TABLE merchant (
    merchant_id INT PRIMARY KEY,
    merchant_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE transactions (
    transaction_id CHAR(32) PRIMARY KEY,
    customer_id INT REFERENCES customer(customer_id),
    merchant_id INT REFERENCES merchant(merchant_id),
    date_id INT REFERENCES date(date_id),
    transaction_time TIME NOT NULL,
    amt NUMERIC(20,2) NOT NULL,
    is_fraud BOOLEAN NOT NULL DEFAULT FALSE,
    merch_lat NUMERIC(9,6),
    merch_long NUMERIC(9,6)
);