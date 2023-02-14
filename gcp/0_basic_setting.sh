#based on codes
#https://tecadmin.net/install-apache-kafka-ubuntu/

sudo apt update
sudo apt install default-jdk

wget https://archive.apache.org/dist/kafka/3.3.1/kafka_2.12-3.3.1.tgz
tar xzf kafka_2.12-3.3.1.tgz
sudo mv kafka_2.12-3.3.1 /usr/local/kafka
