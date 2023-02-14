LAST_TOPIC=6

for i in $(seq 0 $LAST_TOPIC)
do
  /usr/local/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --delete --topic frame$i
done
