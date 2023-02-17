import asyncio
import websockets
import argparse
from datetime import datetime
import json
from functools import partial


async def pi1(ip_first, response_first):
    async with websockets.connect(ip_first, ping_interval=None) as websocket:
        while True:
            try:
                message = await websocket.recv()
                #print(message)
                res = json.loads(message)
                json.dump(res, open(respone_first, 'w'))

            except Exception as e: 
                print(e)
                break


async def pi2(ip_second, response_second):
    async with websockets.connect(ip_second, ping_interval=None) as websocket:
        while True:
            try:
                message = await websocket.recv()
                #print(message)
                res = json.loads(message)
                json.dump(res, open(response_second, 'w'))

            except Exception as e: 
                print(e)
                break

async def main(ip_first, ip_second, response_first, response_second):
    run_pi9 = loop.create_task(pi1(ip_first, response_first))
    run_pi10 = loop.create_task(pi2(ip_second, response_second))
    await asyncio.wait([run_pi9, run_pi10])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip_first', type=str)
    parser.add_argument('--ip_second', type=str)
    parser.add_argument('--response_first', type=str)
    parser.add_argument('--response_second', type=str)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.ip_first, 
                                 args.ip_second, 
                                 args.response_first, 
                                 args.response_second))
    loop.close()
