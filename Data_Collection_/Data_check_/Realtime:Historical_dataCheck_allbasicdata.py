# check data in a period if they are matched with API data

import os
import psycopg2
import requests
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine






# enter into database and get a specific time period for data check
# 2025-04-01 11:12:00+00--2025-04-01 11:31:00+00
# 1743505920000---1743507060000

starttime=1743505920000
endtime=1743507060000


# connect binance API and return data in designated period
# the column names should same just for convenience

def get_binance_kline_data(start,end,symbol='BTCUSDT',interval='1m'):
    binance_api = f"https://fapi.binance.com/fapi/v1/klines"
    params={
        'symbol': symbol,
        'interval': interval,
        'startTime': start,
        'endTime': end,
        'limit': 1000
    }
    # get all data and save into a list
    all_data=[]
    while(True):
        response = requests.get(binance_api, params=params)
        data=response.json()
        if not data:
            break
        all_data.extend(data)
        print(all_data)
        lastkline_time=data[-1][0]
        if lastkline_time>end or len(data)<1000:
            break
        params['startTime']=lastkline_time+1

    return pd.DataFrame(all_data,columns=['open_time','open_price','high_price','low_price','close_price','volume',
                                          'close_time','quote_asset_volume','number_of_trades',
                                          'taker_buy_base_volume','taker_buy_quote_volume','ignore'
                                          ])
def get_postgreSQL_kline(start, end):
    user = os.getenv('PostgreSQL_USER')
    password = os.getenv('PostgreSQL_PASSWORD')
    host = ''
    port = os.getenv('PostgreSQL_PORT')
    database = os.getenv('PostgreSQL_DATABASE')

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(db_url)

    sql = f"""
    SELECT open_time, open_price, high_price, low_price, close_price, volume,
           close_time, quote_asset_volume, number_of_trades,
           taker_buy_base_volume, taker_buy_quote_volume
    FROM realtime_btc_futures_1mdata
    WHERE open_time BETWEEN {start} AND {end}
    ORDER BY open_time
    """

    df = pd.read_sql(sql, engine)
    return df

binance_kline=get_binance_kline_data(starttime,endtime)
postgreSQL_data=get_postgreSQL_kline(starttime,endtime)


# delete ignore
binance_data = binance_kline[[
    'open_time','open_price','high_price','low_price','close_price','volume',
    'close_time','quote_asset_volume','number_of_trades',
    'taker_buy_base_volume','taker_buy_quote_volume'
]]

# turn data type into float type and int type
for col in ['open_price','high_price','low_price','close_price','volume',
            'quote_asset_volume','taker_buy_base_volume','taker_buy_quote_volume']:
    binance_data.loc[:, col] = binance_data[col].astype(float)
    postgreSQL_data[col] = postgreSQL_data[col].astype(float)

binance_data.loc[:, 'number_of_trades'] = binance_data['number_of_trades'].astype(int)
postgreSQL_data['number_of_trades'] = postgreSQL_data['number_of_trades'].astype(int)

# make sure all data are sorted by opentime
binance_data = binance_data.sort_values(by='open_time')
postgreSQL_data.sort_values(by='open_time', inplace=True)
binance_data.reset_index(drop=True, inplace=True)
postgreSQL_data.reset_index(drop=True, inplace=True)

# match data of every row
diff = binance_data.compare(postgreSQL_data)

if diff.empty:
    print("✅ Data matched.")
else:
    print("❌ Data not matched and different row are: ")
    print(diff)




# connect database and get the data in same time period


# check if API returned data match with database data

# print in terminal if data are matched