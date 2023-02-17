import asyncio
import websockets
import pyaudio
import wave
import audioop
import datetime
import math
import json
from pathlib import Path

def decibel( data, width ):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        return 20 * math.log(rms, 10)

def rescaled_decibel( data, width ):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        decibel = 20 * math.log(rms, 10)
        return math.tanh( (decibel - 75) * 0.05 )


chunk = 4410 #1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1
fs = 44100  # Record at 44100 samples per second
# seconds = 10


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


async def main():
    async with websockets.serve(handler, "172.26.174.12", 8001, ping_interval=None):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
