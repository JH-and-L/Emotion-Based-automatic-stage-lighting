TOPIC_NAME=$1
PARTITIONS=1
REPLICATION=2

/usr/local/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic $TOPIC_NAME --partitions $PARTITIONS --replication-factor $REPLICATION