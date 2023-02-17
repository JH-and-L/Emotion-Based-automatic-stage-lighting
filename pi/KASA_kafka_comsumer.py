from kafka import KafkaConsumer

import asyncio
from kasa import SmartBulb

import json

sent_class = {'anger': 0, 'fear': 1, 'joy': 2, 'love': 3, 'sadness': 4, 'surprise': 5, 'neutral' : 6}
HSVs = [[0,100,100], [272,57,10], [60,50,90], [320,25,30], [240,100,20], [0,0,80], [0,0,5]]

def moving_window_voting(data, window_size):
    window = data[-window_size:]
    if window_size == len(set(window)):
        return 6
    return max(set(window), key=window.count)

async def real_time_voting_and_change_color(window_size, bulb_ip, consumer):

    bulb = SmartBulb(bulb_ip)
    await bulb.update()
    await bulb.set_hsv(*HSVs[6])
    data = []

    for msg_emotion in consumer:
        sentiment = msg_emotion.value.decode(encoding = 'utf-8')
        print(f"[Kafka Consumer] Recieved sentiment: {sentiment}")
        print()
        new_data = sent_class[sentiment]
        data.append(new_data)
        await bulb.set_hsv(*HSVs[moving_window_voting(data, window_size)])
        await asyncio.sleep(0.01)


if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--config-path', type=str, default='config.json')

    parser.add_argument('-i', '--bulb-id', type=int, default = 1, help="either 1 or 2")
    parser.add_argument('-w', '--window-size', type = int, default = 3, required = False)

    args = parser.parse_args()

    with open("config.json", "r") as f:
        config = json.load(f)

    gcp_ip = config["GCP_IP"]
    port = config["PORT"]
    bulb_ip = config[f"BULB_IP{args.bulb_id}"]
    kafka_topic = config[f"EMOTION_TOPIC{args.bulb_id}"]

    consumer_emotion = KafkaConsumer(bootstrap_servers=[f'{gcp_ip}:{port}'], 
            auto_offset_reset='latest')
    consumer_emotion.subscribe([kafka_topic])

    asyncio.run(real_time_voting_and_change_color(args.window_size, bulb_ip, consumer_emotion))
    
