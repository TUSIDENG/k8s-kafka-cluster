import time
from kafka import KafkaProducer
import json

BOOTSTRAP_SERVERS = "127.0.0.1:9094,127.0.0.1:9095,127.0.0.1:9096"
TOPIC = "demo-topic"


def create_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def send_messages(producer, count=10):
    for i in range(count):
        message = {"id": i, "content": f"Message {i}", "timestamp": time.time()}
        future = producer.send(TOPIC, key=f"key-{i}", value=message)
        result = future.get(timeout=10)
        print(f"Sent: {message} -> Partition: {result.partition}, Offset: {result.offset}")
        time.sleep(0.5)


def main():
    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS}...")
    producer = create_producer()
    print("Producer created successfully")

    try:
        send_messages(producer, count=10)
        print("All messages sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
