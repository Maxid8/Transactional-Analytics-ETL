import pandas as pd

df = pd.read_parquet('cleaned_fraud_data.parquet')

#Split the timestamp
datetime_series = pd.to_datetime(df['trans_date_trans_time'])
df['date_id'] = datetime_series.dt.strftime('%Y%m%d').astype(int)
df['trans_time'] = datetime_series.dt.strftime('%H:%M:%S')

year_max = max(df['date_id']) // 10000
year_min = min(df['date_id']) // 10000

#Create the date dimension table
dates = pd.DataFrame({'full_date': pd.date_range(start=f"{year_min}-01-01", end=f"{year_max}-12-31")})
dates['date_id'] = dates['full_date'].dt.strftime('%Y%m%d').astype(int)
dates['full_date'] = pd.to_datetime(dates['full_date'])
dates['year'] = dates['full_date'].dt.year
dates['quarter'] = 'Q' + dates['full_date'].dt.quarter.astype(str)
dates['month'] = dates['full_date'].dt.month
dates['month_name'] = dates['full_date'].dt.strftime('%B')
dates['week'] = dates['full_date'].dt.isocalendar().week
dates['day'] = dates['full_date'].dt.day
dates['day_name'] = dates['full_date'].dt.strftime('%A')

#print(dates.head())

