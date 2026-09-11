DROP TABLE IF EXISTS fact_transaction;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_merchant;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
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

CREATE TABLE dim_customer (
    customer_id INT PRIMARY KEY,
    cc_num BIGINT NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender CHAR(1),
    job VARCHAR(100),
    dob DATE NOT NULL,
    street VARCHAR(100),
    city VARCHAR(100),
    state CHAR(2),
    zip VARCHAR(10)
);

CREATE TABLE dim_merchant (
    merchant_id INT PRIMARY KEY,
    merchant_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE fact_transaction (
    transaction_id CHAR(32) PRIMARY KEY,
    customer_id INT REFERENCES dim_customer(customer_id) NOT NULL,
    merchant_id INT REFERENCES dim_merchant(merchant_id) NOT NULL,
    date_id INT REFERENCES dim_date(date_id) NOT NULL,
    transaction_time TIME NOT NULL,
    amt NUMERIC(20,2) NOT NULL,
    is_fraud SMALLINT NOT NULL,
    merch_lat NUMERIC(9,6),
    merch_long NUMERIC(9,6)
);

CREATE INDEX ON fact_transaction(customer_id);
CREATE INDEX ON fact_transaction(merchant_id);
CREATE INDEX ON fact_transaction(date_id);
CREATE INDEX ON fact_transaction(is_fraud) WHERE is_fraud = 1;