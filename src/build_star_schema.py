import pandas as pd
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from clean import load_and_clean
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ENV_VARS = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]

def get_db_config() -> dict[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Create an .env file in the root of your project based on .env.example."
        )
    return {var: os.environ[var] for var in REQUIRED_ENV_VARS}

def add_date_id(df: pd.DataFrame) -> pd.DataFrame:
    datetime_series = pd.to_datetime(df["trans_date_trans_time"])
    df["date_id"] = datetime_series.dt.strftime("%Y%m%d").astype(int)
    df["trans_time"] = datetime_series.dt.strftime("%H:%M:%S")
    return df

def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    year_min = df["date_id"].min() // 10000
    year_max = df["date_id"].max() // 10000

    dates = pd.DataFrame({
        "full_date": pd.date_range(start=f"{year_min}-01-01", end=f"{year_max}-12-31")
    })
    dates["date_id"] = dates["full_date"].dt.strftime("%Y%m%d").astype(int)
    dates["year"] = dates["full_date"].dt.year
    dates["quarter"] = "Q" + dates["full_date"].dt.quarter.astype(str)
    dates["month"] = dates["full_date"].dt.month
    dates["month_name"] = dates["full_date"].dt.strftime("%B")
    dates["week"] = dates["full_date"].dt.isocalendar().week
    dates["day"] = dates["full_date"].dt.day
    dates["day_name"] = dates["full_date"].dt.strftime("%A")
    return dates


def build_dim_merchant(df: pd.DataFrame) -> pd.DataFrame:
    merchant = df[["merchant", "category"]].drop_duplicates().reset_index(drop=True)
    merchant["merchant_id"] = merchant.index + 1
    merchant = merchant.rename(columns={"merchant": "merchant_name"})
    return merchant[["merchant_id", "merchant_name", "category"]]


def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    customer = (
        df[["cc_num", "first", "last", "gender", "dob", "job", "street", "city", "state", "zip"]]
        .drop_duplicates(subset=["cc_num"])
        .reset_index(drop=True)
    )
    customer["customer_id"] = customer.index + 1
    customer = customer.rename(columns={"first": "first_name", "last": "last_name"})
    columns = ["customer_id", "cc_num", "first_name", "last_name", "gender", "job", "dob", "street", "city", "state", "zip"]
    return customer[columns]

def build_fact_transaction(df: pd.DataFrame, merchant: pd.DataFrame, customer: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(
        merchant, left_on=["merchant", "category"], right_on=["merchant_name", "category"], how="left"
    )
    merged = merged.merge(customer, on="cc_num", how="left")

    fact = merged[[
        "trans_num", "customer_id", "merchant_id", "date_id",
        "trans_time", "amt", "is_fraud", "merch_lat", "merch_long"
    ]].rename(columns={"trans_num": "transaction_id", "trans_time": "transaction_time"})

    validate_fact_transaction(fact, expected_rows=len(df))
    return fact


def validate_fact_transaction(fact: pd.DataFrame, expected_rows: int) -> None:
    assert len(fact) == expected_rows, (
        f"The number of rows changed during the merge: expected {expected_rows}, got {len(fact)}."
    )
    for fk_column in ["customer_id", "merchant_id", "date_id"]:
        missing = fact[fk_column].isna().sum()
        assert missing == 0, f"{missing} rows have no matching dimension for {fk_column}."

def assert_columns_match(engine, df: pd.DataFrame, table_name: str) -> None:
    inspector = inspect(engine)
    expected = {col["name"] for col in inspector.get_columns(table_name)}
    actual = set(df.columns)
    assert actual == expected, (
        f"{table_name}: columns do not match the actual database schema. "
        f"Only in DataFrame: {actual - expected}, only in table: {expected - actual}"
    )

def load_to_postgres(tables: dict[str, pd.DataFrame]) -> None:
    config = get_db_config()
    engine = create_engine(
        f"postgresql+psycopg2://{config['DB_USER']}:{config['DB_PASSWORD']}"
        f"@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}"
    )

    load_order = ["dim_date", "dim_merchant", "dim_customer", "fact_transaction"]
    for table_name in load_order:
        df = tables[table_name]
        assert_columns_match(engine, df, table_name)
        df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=10_000)
        print(f"{table_name}: {len(df)} rows loaded.")

    engine.dispose()

def main():
    df = load_and_clean()
    df = add_date_id(df)

    dim_date = build_dim_date(df)
    dim_merchant = build_dim_merchant(df)
    dim_customer = build_dim_customer(df)
    fact_transaction = build_fact_transaction(df, dim_merchant, dim_customer)

    load_to_postgres({
        "dim_date": dim_date,
        "dim_merchant": dim_merchant,
        "dim_customer": dim_customer,
        "fact_transaction": fact_transaction,
    })

if __name__ == "__main__":
    main()