# Description of Demo

## Real-time Monitoring for VAD
- send.py: Send messages in Raspberry Pi
- client.py: Receive messages from Raspberry Pi that the send.py is running. 
- draw.py: Draw plots of decibel, rescaled decibel, and whether the rescaled decibel exceeds threshold
- run.sh: Run client.py and draw.py concurrently

## Usage

1. Run send.py in Raspberry pi with ip_address for Raspberry pi. The static IP address is recommended.
```sh
python send.py -ip ip_address 
```

2. Modify run.sh file with your own settings.
```
python client.py --ip_first YOUR_IP_ADDRESS --ip_second YOUR_IP_ADDRESS --response_first YOUR_RESPONSE_1.json --response_second YOUR_RESPONSE_2.json & python draw.py --response_first YOUR_RESPONSE_1.json --response_second YOUR_RESPONSE_2.json
```
The client.py file assumes that you own two Raspberry Pi devices and you will use two devices in the same time. Each Raspberry Pi device will send their responses with json file and that file will be saved in your local machine. So, YOUR_RESPONSE_1.json and YOUR_RESPONSE_2.json files are the path to save responses from Raspberry Pi. These paths are also used in draw.py code as arguments.

3. Run run.sh in local machine 
```sh
./run.sh
```

