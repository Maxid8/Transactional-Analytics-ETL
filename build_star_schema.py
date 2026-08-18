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

#Create the merchant dimension table
merchant = df[['merchant', 'category']].drop_duplicates().reset_index(drop=True)
merchant['merchant_id'] = merchant.index + 1
merchant.rename(columns={'merchant': 'merchant_name'}, inplace=True)
merchant = merchant[['merchant_id', 'merchant_name', 'category']]

#print(merchant.head())

#Create the customer dimension table
customer = df[['cc_num', 'first', 'last', 'gender', 'dob', 'job', 'street', 'city', 'state', 'zip']].drop_duplicates(subset=['cc_num']).reset_index(drop=True)
customer['customer_id'] = customer.index + 1
customer = customer[['customer_id', 'cc_num', 'first', 'last', 'gender', 'dob', 'job', 'street', 'city', 'state', 'zip']]

#print(customer.head())

#Create the transactions fact table
df = df.merge(merchant, left_on=['merchant', 'category'], right_on=['merchant_name', 'category'], how='left')
df = df.merge(customer, on='cc_num', how='left')

#print(df.columns)

transactions = df[['trans_num', 'customer_id', 'merchant_id', 'date_id', 'trans_time', 'amt', 'is_fraud', 'merch_lat', 'merch_long']]

#print(transactions.info())

dates.to_parquet('date.parquet', engine='fastparquet', index=False)
merchant.to_parquet('merchant.parquet', engine='fastparquet', index=False)
customer.to_parquet('customer.parquet', engine='fastparquet', index=False)
transactions.to_parquet('transactions.parquet', engine='fastparquet', index=False)