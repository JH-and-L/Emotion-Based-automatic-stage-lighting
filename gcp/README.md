# Kafka Backbone (GCP)
This repository contains code for setting up the kafka pipeline.

## 1. Install
To install kafka, run

```bash
sh 0_basic_setting.sh
```

which will install Java Development Kit (JDK), download binary Kafka zip file, unzip and move the Kafka files to /usr/local directory.

It will also install PyTorch after installing all kafka components

## 2. Zookeeper

```bash
sh 1_run_zookeeper.sh
```

While Kafka zookeeper will be deprecated in the new version, the current version still requires zookeeper to be running for the kafka brokers to start.

## 3. Kafka Broker

```bash
sh 2_run_kafka_server.sh
```

OR

```bash
/usr/local/kafka/bin/kafka-server-start.sh <broker properties path>
```

The script ```2_run_kafka_server.sh``` starts the broker on the zookeeper.

However, there are changes that must be made to the broker properties. The properties file can be accessed in /usr/local/kafka/config/server.properties.

The additional configurations that must be added are:

```
# allow requests from specific IP addresses
listeners=PLAINTEXT://<first pi IP address>:9092,PLAINTEXT://<second pi IP address>:9092

# host broker on external IP address of GCP VM instance
advertised.listeners=PLAINTEXT://<GCP VM instance external IP address>:9092
```

This will allow Raspberry Pis to send producer or consumer requests to the broker hosted on the external IP address of the GCP VM instance

### Additional Brokers
Since we have set up a backup broker to account for failures of the primary broker, we also create another properties file:

```
cp /usr/local/kafka/config/server.properties /usr/local/kafka/config/backup-server.properties
```

with these following configuration:

```
# new ID for backup broker
broker.id=1

# allow requests from specific IP addresses
listeners=PLAINTEXT://<first pi IP address>:9093,PLAINTEXT://<second pi IP address>:9093

# host broker on external IP address of GCP VM instance
advertised.listeners=PLAINTEXT://<GCP VM instance external IP address>:9093

# separate directory for event logs
log.dirs=/tmp/kafka-logs-backup
```

## 4. Create Topics

```
sh 3_create_topic.sh <topic name>
```

```3_create_topic.sh``` contains code for creating new topics.

To keep the FIFO behavior of events, the number of partitions are kept as 1, but to replicate the events to the backup broker, the replication factor is set as 2. Thus, two brokers are required to be hosted before running this code. 

If only a single broker is to be utilized, change REPLICATION to 1 before running this code 

## 5. Emotion Classification

```bash
python3 get_stt.py --source-topic <stt result topic name> --target-topic <sentiment result topic name> 
```

```get_stt.py``` contains the code for retrieving Speech-to-Text results, running emotion classification model, and producing the resulting emotion event.

```source-topic``` argument should be the topic name where the STT results are stored, and ```target-topic``` argument should be the topic name where the resulting emotions should be sent.
