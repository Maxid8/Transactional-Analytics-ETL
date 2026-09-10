import pandas as pd

RAW_FILES = ["data/raw/fraudTest.csv", "data/raw/fraudTrain.csv"]


def load_raw_data(paths: list[str]) -> pd.DataFrame:
    return pd.concat(
        [pd.read_csv(f, parse_dates=["trans_date_trans_time", "dob"]) for f in paths],
        ignore_index=True,
    )


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["Unnamed: 0"])
    df = df.drop_duplicates(subset=["trans_num"])
    return df


def load_and_clean() -> pd.DataFrame:
    df = load_raw_data(RAW_FILES)
    return clean(df)