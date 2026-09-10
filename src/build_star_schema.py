import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

RAW_DATA_PATH = "cleaned_fraud_data.parquet"

load_dotenv()

def load_cleaned_data(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
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
    columns = ["customer_id", "cc_num", "first", "last", "gender", "dob", "job", "street", "city", "state", "zip"]
    return customer[columns]

def build_fact_transaction(df: pd.DataFrame, merchant: pd.DataFrame, customer: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(
        merchant, left_on=["merchant", "category"], right_on=["merchant_name", "category"], how="left"
    )
    merged = merged.merge(customer, on="cc_num", how="left")

    fact = merged[[
        "trans_num", "customer_id", "merchant_id", "date_id",
        "trans_time", "amt", "is_fraud", "merch_lat", "merch_long"
    ]]

    validate_fact_transaction(fact, expected_rows=len(df))
    return fact


def validate_fact_transaction(fact: pd.DataFrame, expected_rows: int) -> None:
    assert len(fact) == expected_rows, (
        f"A sorok száma megváltozott a merge során: {expected_rows} helyett {len(fact)}."
    )
    for fk_column in ["customer_id", "merchant_id", "date_id"]:
        missing = fact[fk_column].isna().sum()
        assert missing == 0, f"{missing} sorhoz nem található egyező dimenzió: {fk_column}"

def load_to_postgres(tables: dict[str, pd.DataFrame]) -> None:
    engine = create_engine(
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )

    load_order = ["dim_date", "dim_merchant", "dim_customer", "fact_transaction"]
    for table_name in load_order:
        tables[table_name].to_sql(
            table_name, engine, if_exists="append", index=False, chunksize=10_000
        )
        print(f"{table_name}: {len(tables[table_name])} sor betöltve.")

    engine.dispose()

def main():
    df = load_cleaned_data(RAW_DATA_PATH)

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