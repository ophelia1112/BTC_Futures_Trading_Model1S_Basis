import asyncio
import websockets
import json

async def get_closed_kline_raw():
    websocketsAPI = "**"
    async with websockets.connect(websocketsAPI) as ws:
        print("⏳ Monitoring kline...")
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            kline = data['k']

            if kline['x']:
                print("\n✅ Original kline: ")
                print(json.dumps(kline, indent=2))
                break

asyncio.run(get_closed_kline_raw())



