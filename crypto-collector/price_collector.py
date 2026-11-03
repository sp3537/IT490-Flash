import os
import requests
import json
import pika
import getpass

API_KEY = os.environ.get("COINGECKO_API_KEY")

if not API_KEY:
    raise SystemExit("missing key")

url = "https://api.coingecko.com/api/v3/coins/markets"

params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "24h"

}

response = requests.get(
    url,
    headers={"x-cg-demo-api-key": API_KEY},
    params=params,
    timeout=30 
)

if not response.ok:
    print("CoinGecko error:", response.status_code)
    print(response.text)
    raise SystemExit(1)

coins = response.json()

print(f"Successfully fetched {len(coins)} cryptocurrencies!")

for coin in coins[:5]:
    print(
        coin["name"],
        coin["symbol"].upper(),
	"$" + str(coin["current_price"])
    )
message = {
    "type": "store_prices",
    "coins": [
        {
		"coin_id": coin["id"],
		"name": coin["name"],
		"symbol": coin["symbol"],
		"price": coin["current_price"],
		"change_24h": coin.get("price_change_percentage_24h"),
		"market_cap": coin.get("market_cap")
		}
		for coin in coins
	]

}

print("Prepared", len(message["coins"]), "coins for RabbitMQ")

# For Connecting to rabbbitmq

rabbit_password = getpass.getpass("Rabbitmq pass: ")

credentials = pika.PlainCredentials(
    "shlok",
    rabbit_password
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host = "localhost",
        port = 5672,
        virtual_host = "shlok",
        credentials = credentials
 )
)

channel = connection.channel()
channel.confirm_delivery()

channel.basic_publish(
    exchange = "marketExchange",
    routing_key = "market.prices",
    body = json.dumps(message),
    mandatory = True,
    properties = pika.BasicProperties(
        delivery_mode = 2,
        content_type = "application/json"

 )
)

connection.close()

print("Successfully sent 250 coins to rabbitmq")
