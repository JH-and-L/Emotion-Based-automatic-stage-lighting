# Emotion-Based-automatic-stage-lighting

This is repository of the team JH&L from the studio project in CMU.

Our project is to develop a stage lighting adjustment demo-system based on emotion detection. Overall, we have utilized two Raspberry Pi as our edge devices and the Google Cloud Platform as our server. For the lighting system, we use KASA Smart light bulb.

![System Architecture](imgs/SystemArchitecture.png)

This repository consists of two main directories, and each of those directories operates separately on Raspberry Pi(`pi/`) and GCP(`gcp/`).

In our demo, we have an additional visualization of input level and VAD module. Code for this live visualization is in `demo/`.


## 0. Configuration

You can easily set configuration parameters such as the Kafka host IP address in `config.json`.


## 1. Edge Device: Raspberry Pi

To run a STT model with VAD, and send detected sentence through Kafka producer,
```
python pi/STT_kafka_producer.py -p ./config.json -i BULB_ID -m PATH_TO_DEEPSPEECH_MODEL -s PATH_TO_DEEPSPEECH_SCORER
```

To run a KASA light adjustment module by recieving detected emotion from server,
```
python pi/KASA_kafka_consumer.py -p ./config.json -i BULB_ID
```


## 2. Server: Google Cloud Platform

On GCP, you first need to setup Kafka environment and run zookeeper/broker. Detailed Kafka configuration on GCP can be found in `gcp/README.md`.
To do so, you can simply run the below scripts subsequently.
- `gcp/0_basic_setting.sh`
- `gcp/1_run_zookeeper.sh`
- `gcp/2_run_kafka_server.sh`

To run the emotion detection on GCP,
```
python gcp/get_stt.py
```

