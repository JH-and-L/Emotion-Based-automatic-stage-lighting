from kafka import KafkaConsumer, KafkaProducer

from transformers import pipeline
from transformers import AutoTokenizer, AutoModelWithLMHead
import logging

import json

tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-emotion")
model = AutoModelWithLMHead.from_pretrained("mrm8488/t5-base-finetuned-emotion")

def get_emotion(text):
    """Change input text to sentiment category

    Args:
        input_str (str): input string to do the sentiment anlysis

    Returns:
        label (str): sentiment label
    """
    input_ids = tokenizer.encode(text + '</s>', return_tensors='pt')
    output = model.generate(input_ids=input_ids, max_length=2)
    dec = [tokenizer.decode(ids) for ids in output]
    label = dec[0]
    label = label.replace('<pad>', '').strip()
    return label


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--config-path', type=str, default='config.json')
    parser.add_argument('-i', '--bulb-id', type=int, default = 1, help="either 1 or 2")
    
    args = parser.parse_args()

    with open("config.json", "r") as f:
        config = json.load(f)

    server = f"localhost:{config['PORT']}"
    source_topic = config[f"STT_TOPIC{config['bulb_id']}"]
    target_topic = config[f"EMOTION_TOPIC{config['bulb_id']}"]

    try:
        # main broker
        consumer = KafkaConsumer(bootstrap_servers=[f'{args.host_ip}:9092'], auto_offset_reset='latest')
        consumer.subscribe([args.source_topic])

        producer = KafkaProducer(bootstrap_servers=[f'{args.host_ip}:9092'])
    except:
        # backup broker
        consumer = KafkaConsumer(bootstrap_servers=[f'{args.host_ip}:9093'], auto_offset_reset='latest')
        consumer.subscribe([args.source_topic])

        producer = KafkaProducer(bootstrap_servers=[f'{args.host_ip}:9093'])

    for msg in consumer:
        # get stt result
        text = msg.value.decode(encoding='utf-8')

        sentiment = get_emotion(text)

        # send sentiment to sentiment topic
        print('Sentiment result', sentiment)
        producer.send(target_topic, sentiment.encode('utf-8'))
        print('Received data:', text, ', Sent: ', sentiment, ', Score: ', sentiment)
