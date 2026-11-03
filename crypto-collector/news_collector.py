import json
import os
import feedparser
import pika
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = {
	"CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
	"Cointelegraph": "https://cointelegraph.com/rss",
	"Decrypt": "https://decrypt.co/feed"
}

articles = []
seen = set()

for source, url in FEEDS.items():
	feed = feedparser.parse(url)

	if feed.bozo and not feed.entries:
		print(f"Could not read {source}: {feed.bozo_exception}")
		continue

	for entry in feed.entries[:10]:
		link = entry.get("link", "")

		if not link or link in seen:
			continue

		seen.add(link)

		published = datetime.now(timezone.utc)

		if entry.get("published"):
			try:
				published = parsedate_to_datetime(
					entry["published"]
				).astimezone(timezone.utc)
			except (ValueError, TypeError, OverflowError):
				pass

		articles.append({
			"title": entry.get("title", "Untitled"),
			"link": link,
			"source": source,
			"published": published.strftime("%Y-%m-%d %H:%M:%S"),
			"summary": entry.get("summary", "")[:2000]
		})

if not articles:
	raise SystemExit("No news articles retrieved")

message = {
	"type": "store_news",
	"articles": articles
}

print(f"Prepared {len(articles)} news articles")

credentials = pika.PlainCredentials(
	os.environ.get("RABBITMQ_USER", "shlok"),
	os.environ["RABBITMQ_PASSWORD"]
)

connection = pika.BlockingConnection(
	pika.ConnectionParameters(
		host=os.environ.get("RABBITMQ_HOST", "localhost"),
		port=5672,
		virtual_host="shlok",
		credentials=credentials
	)
)

channel = connection.channel()
channel.confirm_delivery()

channel.basic_publish(
	exchange="marketExchange",
	routing_key="market.news",
	body=json.dumps(message),
	mandatory=True,
	properties=pika.BasicProperties(
		delivery_mode=2,
		content_type="application/json"
	)
)

connection.close()

print(f"{datetime.now():%Y-%m-%d %H:%M:%S} sent {len(articles)} news articles to RabbitMQ")
