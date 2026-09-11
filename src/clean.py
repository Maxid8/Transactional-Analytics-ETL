import os
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILES = [PROJECT_ROOT / "data/raw/fraudTest.csv", PROJECT_ROOT / "data/raw/fraudTrain.csv"]

def load_raw_data(paths: list[Path]) -> pd.DataFrame:
    return pd.concat(
        [pd.read_csv(f, parse_dates=["trans_date_trans_time", "dob"]) for f in paths],
        ignore_index=True,
    )

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["Unnamed: 0"])
    df = df.drop_duplicates(subset=["trans_num"])
    return df

def load_and_clean(cache_path: Path = PROJECT_ROOT / "data/processed/cleaned_fraud_data.parquet") -> pd.DataFrame:
    os.makedirs(cache_path.parent, exist_ok=True)
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    df = clean(load_raw_data(RAW_FILES))
    df.to_parquet(cache_path, index=False)
    return df