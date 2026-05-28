from kafka import KafkaConsumer
import json

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "test-topic"
GROUP_ID = "test-consumer-group"


def create_consumer():
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )


def consume_messages(consumer, max_messages=10):
    count = 0
    print(f"Starting to consume messages from topic '{TOPIC}'...")
    for message in consumer:
        print(f"Received: Key={message.key}, Value={message.value}, "
              f"Partition={message.partition}, Offset={message.offset}")
        count += 1
        if max_messages and count >= max_messages:
            print(f"Reached {max_messages} messages, stopping...")
            break


def main():
    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS}...")
    consumer = create_consumer()
    print("Consumer created successfully")

    try:
        consume_messages(consumer, max_messages=10)
    except KeyboardInterrupt:
        print("\nConsumer stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
