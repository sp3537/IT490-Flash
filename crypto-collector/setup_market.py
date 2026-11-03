import pika
import getpass

password = getpass.getpass("Rabbitmq password for shlok: ")

credentials = pika.PlainCredentials("shlok", password)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="localhost",
	port=5672,
	virtual_host="shlok",
	credentials=credentials

    )
)

channel = connection.channel()

channel.exchange_declare(
    exchange="marketExchange",
    exchange_type="topic",
    durable=True
)

channel.queue_declare(
    queue="marketDataQueue",
    durable=True
)

channel.queue_bind(
    exchange="marketExchange",
    queue="marketDataQueue",
    routing_key="market.#"
)

print("Market exchange and queue created successfully!")

connection.close()
