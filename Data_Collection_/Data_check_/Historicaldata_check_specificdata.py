import datetime
import calendar
import requests



time=datetime.datetime(20**,1,1,1,1,1)
targettime=calendar.timegm(time.timetuple())*1000

BINANCE_REST_API = "**"

params={
    "symbol":"**",
    "interval":"*",
    "startTime":targettime,
    'limit':*
}

response=requests.get(BINANCE_REST_API,params=params)
data=response.json()

if data:
    kine=data[0]
    print(kine)
else:
    print('No data to return')




