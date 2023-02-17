from kafka import KafkaConsumer, KafkaProducer

from argparse import ArgumentParser

from transformers import pipeline
from transformers import AutoTokenizer, AutoModelWithLMHead
import logging

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

# def str2sentiment(input_str, model_name="distilbert"):
#     """Change input string to sentiment category and score.

#     Args:
#         input_str (str or list): input string to do the sentiment anlysis
#         model_name (str, optional): pretrained model we want to use(refer: https://huggingface.co/models?dataset=dataset:emotion&sort=downloads)

#     Returns:
#         _type_: labels and scores
#     """
    
#     # we may choose different fine-tuned models
#     if model_name == "distilbert":
#         model='bhadresh-savani/distilbert-base-uncased-emotion'
#     elif model_name == "roberta":
#         model='bhadresh-savani/roberta-base-emotion'
        
#     classifier = pipeline("text-classification",model=model)
    
#     # check whether we have multiple inputs
#     prediction = classifier(input_str)
#     if type(input_str) == list:
#         logging.warning(f"Input strings is a list with length of {len(input_str)}") 
#         label = [prediction[i]['label'] for i in range(len(prediction))]
#         score = [prediction[i]['score'] for i in range(len(prediction))]
#     else:
#         label = prediction[0]['label']
#         score = prediction[0]['score']
        
#     return label, score
          

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--host-ip', type = str , default = 'localhost')
    parser.add_argument('--source-topic', type = str, default = 'stt-text')
    parser.add_argument('--target-topic', type = str, default = 'sentiment')

    args = parser.parse_args()

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
        
        # # TESTING PURPOSES: IGNORE
        # if text == 'anger':
        #     sentiment = '0' # example sentiment
        # elif text == 'fear':
        #     sentiment = '1' # example sentiment
        # else:
        #     sentiment = '2' # example sentiment

        # sentiment = str2sentiment(text)
        sentiment = get_emotion(text)

        # send sentiment to sentiment topic
        print('Sentiment result', sentiment)
        producer.send(args.target_topic, sentiment.encode('utf-8'))
        print('Received data:', text, ', Sent: ', sentiment, ', Score: ', sentiment)
