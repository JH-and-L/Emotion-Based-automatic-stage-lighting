# Description of Demo

## Real-time Monitoring for VAD
- send.py: Send messages in Raspberry Pi
- client.py: Receive messages from Raspberry Pi that the send.py is running. 
- draw.py: Draw plots of decibel, rescaled decibel, and whether the rescaled decibel exceeds threshold
- run.sh: Run client.py and draw.py concurrently

## Usage

1. Run send.py in Raspberry pi
```sh
python send.py
```

2. Run run.sh in local machine 
```sh
./run.sh
```
