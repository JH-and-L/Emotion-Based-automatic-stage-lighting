import asyncio
import websockets
import pyaudio
import wave
import audioop
import datetime
import math
import json
import argparse
from pathlib import Path

def decibel(data, width):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        return 20 * math.log(rms, 10)

def rescaled_decibel(data, width):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        decibel = 20 * math.log(rms, 10)
        return math.tanh( (decibel - 75) * 0.05 )

async def handler(websocket):
    i = 0
    while True:
        frame_data = stream.read(chunk)
        decibel_value = decibel(frame_data, sampwidth)
        rescaled_decibel_value = rescaled_decibel(frame_data, sampwidth)

        if frame_data == "b''":
            break

        now = datetime.datetime.now()
        message = f"[{now}] Decibel={decibel_value}; Rescaled={rescaled_decibel_value}"
        temp = {'ts': now.strftime('%H:%M:%S.%f'),
                'db': decibel_value,
                'db_rescale': rescaled_decibel_value}

        res = json.dumps(temp)
        await websocket.send(res)

async def main(ip_address):
    async with websockets.serve(handler, ip_address, 8001, ping_interval=None):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip_address', type=str)
    parser.add_argument('--chunk', type=int, default=4410)
    parser.add_arugment('--channel', type=int, default=1)
    parser.add_argument('--sample_rate', type=int, default=44100)
    args = parser.parse_args()

    chunk = args.chunk #1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = args.channel
    fs = args.sampel_rate # Record at 44100 samples per second

    # Create an interface to PortAudio
    p = pyaudio.PyAudio()
    
    # Open a .Stream object to get mic input
    stream = p.open(format = sample_format,
                    channels = channels,
                    rate = fs,
                    frames_per_buffer = chunk,
                    input = True)
    
    sampwidth = p.get_sample_size(sample_format)
    rate = fs
    
    asyncio.run(main(args.ip_address))
