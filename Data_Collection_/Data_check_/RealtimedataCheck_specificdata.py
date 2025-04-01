# only check one or several kline data on specific time

import datetime
import calendar
import requests

# designate time
time=datetime.datetime(20**,1,1,1,1,1)
targettime=calendar.timegm(time.timetuple())*1000

# connect REST API get historical data
BINANCE_REST_API = "**"

# configure some parameters and set symbol name, interval, start time and limit
params={
    "symbol":"**",
    "interval":"*",
    "startTime":targettime,
    'limit':*
}


# get data, analyze data and print data
response=requests.get(BINANCE_REST_API,params=params)
data=response.json()
if data:
    kline=data[0]
    print('kline:\n')
    print(f'opentime:{datetime.datetime.fromtimestamp(kline[0]/1000, tz=datetime.UTC)}({kline[0]})')
    print(f'open:{kline[1]}')
    print(f'high:{kline[2]}')
    print(f'low:{kline[3]}')
    print(f'close:{kline[4]}')
    print(f'volume:{kline[5]}')
    print(f"Close time:{datetime.datetime.fromtimestamp(kline[6]/1000, tz=datetime.UTC)} ({kline[6]})")
    print(f"Quote Asset Volume: {kline[7]}")
    print(f"Number of Trades:   {kline[8]}")
    print(f"Taker Buy Base Vol: {kline[9]}")
    print(f"Taker Buy Quote Vol:{kline[10]}")
    print(f"Is this final:      {kline[11]}")
else:
    print("❌ can not find any data")








