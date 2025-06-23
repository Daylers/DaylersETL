#!/bin/bash

# Ждём, пока Kafka Connect будет доступен
echo "Waiting for Kafka Connect to be ready..."
while ! curl -s http://localhost:8083/connectors > /dev/null; do
  sleep 5
done

echo "Kafka Connect is up, creating connector..."

sleep 40

curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/kafka/etc/connector.json

echo "Connector creation requested."