# Kafka Backbone (GCP)
This repository contains code for setting up the kafka pipeline.

## 1. Install
To install kafka, run

```bash
sh 0_basic_setting.sh
```

which will install Java Development Kit (JDK), download binary Kafka zip file, unzip and move the Kafka files to /usr/local directory.

## 2. Zookeeper

```bash
sh 1_run_zookeeper.sh
```

Since  