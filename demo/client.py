import asyncio
import websockets

from datetime import datetime
import json
from functools import partial


async def pi10():
    async with websockets.connect('ws://172.26.174.12:8001', ping_interval=None) as websocket:
        while True:
            try:
                message = await websocket.recv()
                #print(message)
                res = json.loads(message)
                json.dump(res, open('res_pi10.json', 'w'))

            except Exception as e: 
                print(e)
                break


async def pi9():
    async with websockets.connect('ws://172.26.174.123:8001', ping_interval=None) as websocket:
        while True:
            try:
                message = await websocket.recv()
                #print(message)
                res = json.loads(message)
                json.dump(res, open('res_pi9.json', 'w'))

            except Exception as e: 
                print(e)
                break

async def main():
    run_pi9 = loop.create_task(pi9())
    run_pi10 = loop.create_task(pi10())
    await asyncio.wait([run_pi9, run_pi10])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
