# historical btc futures 1m data collection
import logging
import os
import time
import psycopg2
import requests
from dotenv import load_dotenv
from datetime import datetime,timezone
import pandas as pd
import talib
import calendar


# Log configuration
logging.basicConfig(
    filename='**',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
console=logging.StreamHandler()
console.setLevel(logging.INFO)
formatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


# Database configuration and connection
load_dotenv()

HOST = os.getenv("**")
PORT = os.getenv("**")
USER = os.getenv("**")
PASSWORD = os.getenv("**")
DATABASE = os.getenv("**")
if not HOST or not PORT or not USER or not PASSWORD or not DATABASE:
    logging.error('❌Failed to connect database as failed to get env documents.')
    exit()


def database_connection():
    try:
        connection=psycopg2.connect(
            host=HOST,
            port=int(PORT),
            user=USER,
            password=PASSWORD,
            database=DATABASE
    )
        connection.autocommit=True
        return connection
    except Exception as e:
        logging.error(f'❌Database connection error: {e}')
        exit()
logging.info('✅Database connected')


# save data into database
# save data into function maybe should put behind, but when process data function end, it needs
# to save data list into database, so put data save function forward
def save_data_into_db(data_rows):
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            sql="""
            INSERT INTO ** (
                symbol,
                
                open_time,open_timestamp,
                
                close_time,close_timestamp,
                
                open_price,close_price,
                
                high_price,low_price,
                
                volume,number_of_trades,
                
                quote_asset_volume,taker_buy_base_volume,
                
                taker_buy_quote_volume,
                
                EMA_10,EMA_20,
                
                SMA_10,SMA_50,
                
                MACD,MACD_signal,MACD_hist,
                
                BB_upper,BB_middle,BB_lower,
                
                RSI_14,K,D,J,
                
                CCI_14,OBV,VWAP,ATR_14
                
            )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)ON CONFLICT (open_time) DO NOTHING;
            """

            cursor.executemany(sql,data_rows)
            connection.commit()
            # data_rows is a data array, need to locate the position of data



            logging.info(f"✅ Insert success: symbol--{data_rows[0][1]} | opentime--{data_rows[0][2]}")
    except Exception as e:
        logging.error(f'❌Database insert data error: {e}')


# before get data, need to do some preparation----like timestamp transformation...
def transform_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

# get data
def get_historical_kline_data(start_date,end_date,symbol='*',interval='*',limit=*):
    # designate parameters in function, start_date and end_date will be designated when using function at end
    # connect binance api
    BINANCE_REST_API = '**'
    # designate parameters
    params={
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
        'startTime':start_date,
        'endTime':end_date,
    }
    try:
        # get data
        response=requests.get(BINANCE_REST_API,params=params)
        response.raise_for_status()
        # the point is get json(data)
        return response.json()
    except Exception as e:
        logging.error(f'❌Can not get data from binance: {e}')
        return []

# analyze and process data, calculate financial indicators
def process_originalData_calculate_financial_indicators(klines):
    # original data positing
    df=pd.DataFrame(klines,columns=[
        'open_time','open_price','high_price','low_price','close_price',
        'volume','close_time','quote_asset_volume','number_of_trades',
        'taker_buy_base_volume','taker_buy_quote_volume','ignore'
    ])
    df.drop(columns=['ignore'],inplace=True)
    # everytime we process data we need to convert data type in case of string type
    df=df.astype({
        'open_time':'int64',
        'open_price':'float',
        'high_price':'float',
        'low_price':'float',
        'close_price':'float',
        'volume':'float',
        'close_time':'int64',
        'quote_asset_volume':'float',
        'number_of_trades':'int',
        'taker_buy_base_volume':'float',
        'taker_buy_quote_volume':'float'
    }
    )
    # add some columns, including symbol, transformed timestamp, financial indicators
    df['symbol']='BTCUSDT'
    df['open_timestamp'] = df['open_time'].apply(transform_timestamp)
    df['close_timestamp'] = df['close_time'].apply(transform_timestamp)

    # calculate financial indicators and add them in df
    df['EMA_10']=talib.EMA(df['close_price'],timeperiod=10)
    df['EMA_20']=talib.EMA(df['close_price'],timeperiod=20)

    df['SMA_10']=talib.SMA(df['close_price'],timeperiod=10)
    df['SMA_50']=talib.SMA(df['close_price'],timeperiod=50)

    df['MACD'],df['MACD_signal'],df['MACD_hist']=talib.MACD(df['close_price'],fastperiod=12,slowperiod=26,signalperiod=9)

    df['BB_upper'],df['BB_middle'],df['BB_lower']=talib.BBANDS(df['close_price'],timeperiod=20,nbdevup=2,nbdevdn=2)

    df['RSI_14']=talib.RSI(df['close_price'],timeperiod=14)

    df['K'],df['D']=talib.STOCH(df['high_price'],df['low_price'],df['close_price'],fastk_period=14,slowk_period=3,slowd_period=3)
    df['J']=3*df['K']-2*df['D']

    df['CCI_14']=talib.CCI(df['high_price'],df['low_price'],df['close_price'],timeperiod=14)

    df['OBV']=talib.OBV(df['close_price'],df['volume'])

    df['VWAP'] = df['quote_asset_volume'] / df['volume']
    df['VWAP'] = df['VWAP'].replace([float('inf'), -float('inf')], 0)

    df['ATR_14'] = talib.ATR(df['high_price'], df['low_price'], df['close_price'], timeperiod=14)
    df.fillna(0, inplace=True)

    data_rows=[]
    for _,row in df.iterrows():
        data_rows.append(
            (
                row['symbol'], row['open_time'], row['open_timestamp'], row['close_time'], row['close_timestamp'],
                row['open_price'], row['close_price'], row['high_price'], row['low_price'],
                row['volume'], row['number_of_trades'], row['quote_asset_volume'], row['taker_buy_base_volume'],
                row['taker_buy_quote_volume'], row['EMA_10'], row['EMA_20'],
                row['SMA_10'], row['SMA_50'], row['MACD'], row['MACD_signal'], row['MACD_hist'],
                row['BB_upper'], row['BB_middle'], row['BB_lower'], row['RSI_14'],
                row['K'], row['D'], row['J'], row['CCI_14'], row['OBV'], row['VWAP'], row['ATR_14']
            )
        )
    save_data_into_db(data_rows)

# save data in dtabase :see upper function

# main function
def main():
    start_time = datetime(20**, 1, 1, 1, 1, 1)
    end_time = datetime(20**, 1, 1, 1, 1, 1)
    start_time_ms = calendar.timegm(start_time.timetuple()) * 1000
    end_time_ms = calendar.timegm(end_time.timetuple()) * 1000

    while start_time_ms < end_time_ms:
        batch_end_time=start_time_ms+1000*60_000
        if batch_end_time > end_time_ms:
            batch_end_time=end_time_ms


        kline_data=get_historical_kline_data(start_time_ms,batch_end_time)
        if not kline_data:
            break

        logging.info(
            f"📦 Current batch's time period : {transform_timestamp(kline_data[0][0])} → {transform_timestamp(kline_data[-1][0])}")

        process_originalData_calculate_financial_indicators(kline_data)
        last_time=kline_data[-1][0]
        start_time_ms = last_time + 60_000
        time.sleep(1.2)

    logging.info(f'✅Historical data collected over.')

if __name__ == '__main__':
    main()


















