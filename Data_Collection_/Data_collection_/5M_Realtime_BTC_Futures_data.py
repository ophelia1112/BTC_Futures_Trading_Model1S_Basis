import asyncio
import logging
import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timezone
import websockets
import json
import pandas as pd
import talib

# Configure logs to write error in
logging.basicConfig(
    filename='**',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# API connection
BINANCE_WEBSOCKET_API = "**"

# Database connection
load_dotenv()
HOST = os.getenv('**')
PORT = int(os.getenv('**'))
USER = os.getenv('**')
PASSWORD = os.getenv('**')
DATABASE = os.getenv('**')
if not HOST or not PORT or not USER or not PASSWORD or not DATABASE:
    logging.error('❌Can not get env documents.')
    exit()


def database_connection():
    try:
        connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        connection.autocommit = True
        return connection
    except Exception as e:
        logging.error(f'❌Database connection error: {e}')
        exit()


logging.info('✅Database connected')

# Data queue
data_queue = asyncio.Queue(maxsize=*)

# Cache data to calculate financial indicators
MAX_CACHE_SIZE = *
cache_kline_data = []


# Transform timestamp
def change_timestamp(timestamp_ms):
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# Save data in table
def save_dataInto_postgresql(data):
    try:
        with database_connection() as connection:
            cursor = connection.cursor()
            sql = """
            INSERT INTO **(
            symbol,open_time,open_timestamp,close_time,close_timestamp,

            open_price,close_price,high_price,low_price,

            volume,number_of_trades,is_closed,quote_asset_volume,

            taker_buy_base_volume,taker_buy_quote_volume,

            EMA_10,EMA_20,SMA_10,SMA_50,

            MACD,MACD_signal,MACD_hist,

            BB_upper,BB_middle,BB_lower,

            RSI_14,

            K,D,J,CCI_14,

            OBV,VWAP,ATR_14
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)ON CONFLICT (open_time) DO NOTHING;
            """
            cursor.execute(sql, data)
            connection.commit()
            logging.info(f"✅ Insert success: {data[0]} | {data[2]}")
    except Exception as e:
        logging.error(f'❌Database insert error:{e}')


# Monitor websocket API and get realtime data
async def monitor_realtimedata():
    while True:
        try:
            async with websockets.connect(BINANCE_WEBSOCKET_API) as websocketConnection:
                async for message in websocketConnection:
                    data = json.loads(message)
                    kline = data['k']
                    # make sure x:ture and the kline is complete
                    if kline['x']:
                        open_time = int(kline['t'])
                        open_timestamp = change_timestamp(open_time)
                        close_time = int(kline['T'])
                        close_timestamp = change_timestamp(close_time)

                        kline_data = [
                            kline['s'], open_time, open_timestamp, close_time, close_timestamp,
                            float(kline['o']), float(kline['c']), float(kline['h']), float(kline['l']),
                            float(kline['v']), int(kline['n']), bool(kline['x']), float(kline['q']),
                            float(kline['V']), float(kline['Q'])
                        ]
                        await data_queue.put(kline_data)
                        logging.info('✅Data monitored successfully')
        except Exception as e:
            logging.error(f'❌Websocket losed connection:{e},retrying to connect')
            await asyncio.sleep(2)


# Process data structure and transform into df, calculate financial indicators, then save them all
async def process_klineData():
    while True:
        cachedkline = await data_queue.get()
        cache_kline_data.append(cachedkline)
        if len(cache_kline_data) > MAX_CACHE_SIZE:
            cache_kline_data.pop(0)

        df = pd.DataFrame(cache_kline_data, columns=[
            'symbol', 'open_time', 'open_timestamp', 'close_time', 'close_timestamp',
            'open_price', 'close_price', 'high_price', 'low_price', 'volume', 'number_of_trades',
            'is_closed', 'quote_asset_volume', 'taker_buy_base_volume', 'taker_buy_quote_volume'
        ])

        # calculate financial indicators, careful about indicators calculation(format and tool)
        df['EMA_10'] = talib.EMA(df['close_price'], timeperiod=10)
        df['EMA_20'] = talib.EMA(df['close_price'], timeperiod=20)

        df['SMA_10'] = talib.SMA(df['close_price'], timeperiod=10)
        df['SMA_50'] = talib.SMA(df['close_price'], timeperiod=50)

        df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close_price'], fastperiod=12, slowperiod=26,
                                                                    signalperiod=9)

        df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close_price'], timeperiod=20, nbdevup=2,
                                                                       nbdevdn=2)

        df['RSI_14'] = talib.RSI(df['close_price'], timeperiod=14)

        df['K'], df['D'] = talib.STOCH(df['high_price'], df['low_price'], df['close_price'], fastk_period=14,
                                       slowk_period=3, slowd_period=3)
        df['J'] = 3 * df['K'] - 2 * df['D']

        df['CCI_14'] = talib.CCI(df['high_price'], df['low_price'], df['close_price'], timeperiod=14)

        df['OBV'] = talib.OBV(df['close_price'], df['volume'])

        df['VWAP'] = df['quote_asset_volume'] / df['volume']
        df["VWAP"] = df["VWAP"].replace([float("inf"), -float("inf")], 0).fillna(0)

        df['ATR_14'] = talib.ATR(df['high_price'], df['low_price'], df['close_price'], timeperiod=14)
        df.fillna(0, inplace=True)

        # get the last data row and add the new row in database
        final_data = df.iloc[-1].apply(lambda x: x.item() if hasattr(x, 'item') else x).tolist()
        save_dataInto_postgresql(final_data)

        data_queue.task_done()
        logging.info(f'✅Financial indicators calculated successfully and saved : {final_data}')


# main program
async def main():
    task1 = asyncio.create_task(monitor_realtimedata())
    task2 = asyncio.create_task(process_klineData())
    await asyncio.gather(task1, task2)


# activate main program
if __name__ == '__main__':
    asyncio.run(main())







