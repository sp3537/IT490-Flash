import json
import time
import uuid
import smtplib
from decimal import Decimal
from email.message import EmailMessage

import bcrypt
import pika
import mysql.connector

RABBITMQ_HOST = "100.113.206.1"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "dkr"
RABBITMQ_PASSWORD = "CHANGE_ME"
RABBITMQ_VHOST = "shlok"
AUTH_QUEUE = "authQueue"
MARKET_QUEUE = "marketDataQueue"

DB_HOST = "localhost"
DB_USER = "it490"
DB_PASSWORD = "CHANGE_ME"
DB_NAME = "it490"

STARTING_CASH = Decimal("10000.00")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""


def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def to_json(value):
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def fail(message):
    return {"success": False, "message": message}



def notify(cursor, user_id, subject, text):
    cursor.execute(
        """
        SELECT u.email, s.email_alerts, s.text_alerts, s.phone
        FROM users u LEFT JOIN user_settings s ON s.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,)
    )
    row = cursor.fetchone()
    if not row:
        return

    email_on = row["email_alerts"] if row["email_alerts"] is not None else True
    if email_on and row["email"]:
        send_email(row["email"], subject, text)
    if row["text_alerts"] and row["phone"]:
        print(f"[TEXT to {row['phone']}] {text}")


def send_email(to_address, subject, text):
    if not SMTP_USER:
        print(f"[EMAIL to {to_address}] {subject}: {text}")
        return
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(text)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        print(f"Emailed {to_address}: {subject}")
    except Exception as error:
        print(f"Email to {to_address} failed: {error}")



def register_user(data):
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not password:
        return fail("Username and password are required")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO wallets (user_id, cash) VALUES (%s, %s)", (user_id, STARTING_CASH))
        cursor.execute("INSERT INTO user_settings (user_id) VALUES (%s)", (user_id,))
        db.commit()
        return {"success": True, "message": "Registration successful"}
    except mysql.connector.IntegrityError:
        db.rollback()
        return fail("Username already taken")
    except mysql.connector.Error as error:
        db.rollback()
        return fail(str(error))
    finally:
        cursor.close()
        db.close()


def login_user(data):
    username = data.get("username")
    password = data.get("password") or ""

    db = connect_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return fail("Login failed")

        session_key = str(uuid.uuid4())
        cursor.execute("UPDATE users SET session_key = %s WHERE id = %s", (session_key, user["id"]))
        db.commit()
        return {"success": True, "message": "Login successful", "session_key": session_key}
    finally:
        cursor.close()
        db.close()


def validate_session(data):
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE session_key = %s", (data.get("sessionKey"),))
        row = cursor.fetchone()
        if row:
            return {"success": True, "message": "Session valid", "username": row[0]}
        return fail("Session invalid")
    finally:
        cursor.close()
        db.close()


def get_user_id(cursor, data):
    key = data.get("sessionKey")
    if not key:
        return None
    cursor.execute("SELECT id FROM users WHERE session_key = %s", (key,))
    row = cursor.fetchone()
    if not row:
        return None
    return row["id"] if isinstance(row, dict) else row[0]


def get_cash(cursor, user_id, lock=False):
    sql = "SELECT cash FROM wallets WHERE user_id = %s" + (" FOR UPDATE" if lock else "")
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()
    if row:
        return Decimal(row["cash"])
    cursor.execute("INSERT INTO wallets (user_id, cash) VALUES (%s, %s)", (user_id, STARTING_CASH))
    return STARTING_CASH


def coin_row(c):
    return {
        "coin_id": c["coin_id"],
        "name": c["name"],
        "symbol": c["symbol"],
        "price": c["price"],
        "change_24h": c["change_24h"],
        "market_cap": c["market_cap"],
    }



def get_market(data, cursor, user_id):
    search = (data.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        cursor.execute(
            "SELECT * FROM coins WHERE name LIKE %s OR symbol LIKE %s ORDER BY market_cap DESC LIMIT 250",
            (like, like)
        )
    else:
        cursor.execute("SELECT * FROM coins ORDER BY market_cap DESC LIMIT 250")
    coins = [coin_row(c) for c in cursor.fetchall()]
    if not coins and not search:
        return {"success": True, "message": "No price data yet. Waiting on the data collector.", "coins": []}
    return {"success": True, "message": "OK", "coins": coins}


HISTORY_TIME_COLUMN = None


def history_time_column(cursor):
    global HISTORY_TIME_COLUMN
    if HISTORY_TIME_COLUMN is None:
        cursor.execute(
            """
            SELECT column_name AS col FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'price_history'
              AND data_type IN ('timestamp', 'datetime')
            ORDER BY ordinal_position LIMIT 1
            """
        )
        row = cursor.fetchone()
        HISTORY_TIME_COLUMN = row["col"] if row else ""
    return HISTORY_TIME_COLUMN


def get_coin(data, cursor, user_id):
    coin_id = data.get("coin_id")
    cursor.execute("SELECT * FROM coins WHERE coin_id = %s", (coin_id,))
    coin = cursor.fetchone()
    if not coin:
        return fail("Coin not found")

    col = history_time_column(cursor)
    history = []
    if col:
        cursor.execute(
            f"""
            SELECT price, t FROM (
                SELECT price, `{col}` AS t FROM price_history
                WHERE coin_id = %s ORDER BY `{col}` DESC LIMIT 300
            ) recent ORDER BY t
            """,
            (coin_id,)
        )
        history = [
            {"time": r["t"].strftime("%m-%d %H:%M") if r["t"] else "", "price": r["price"]}
            for r in cursor.fetchall()
        ]
    return {"success": True, "message": "OK", "coin": coin_row(coin), "history": history}



def read_amount(data):
    try:
        amount = Decimal(str(data.get("amount")))
    except Exception:
        return None
    return amount if amount > 0 else None


def buy(data, cursor, user_id):
    amount = read_amount(data)
    if amount is None:
        return fail("Enter an amount greater than 0")

    coin_id = data.get("coin_id")
    cursor.execute("SELECT name, symbol, price FROM coins WHERE coin_id = %s", (coin_id,))
    coin = cursor.fetchone()
    if not coin:
        return fail("Coin not found")

    price = Decimal(coin["price"])
    total = (price * amount).quantize(Decimal("0.01"))
    cash = get_cash(cursor, user_id, lock=True)
    if total > cash:
        return fail(f"Not enough cash. That costs ${total:,.2f} and you have ${cash:,.2f}")

    cursor.execute(
        "SELECT amount, avg_price FROM holdings WHERE user_id = %s AND coin_id = %s FOR UPDATE",
        (user_id, coin_id)
    )
    held = cursor.fetchone()
    if held:
        old_amount = Decimal(held["amount"])
        new_amount = old_amount + amount
        new_avg = (old_amount * Decimal(held["avg_price"]) + amount * price) / new_amount
        cursor.execute(
            "UPDATE holdings SET amount = %s, avg_price = %s WHERE user_id = %s AND coin_id = %s",
            (new_amount, new_avg, user_id, coin_id)
        )
    else:
        cursor.execute(
            "INSERT INTO holdings (user_id, coin_id, amount, avg_price) VALUES (%s, %s, %s, %s)",
            (user_id, coin_id, amount, price)
        )

    cash -= total
    cursor.execute("UPDATE wallets SET cash = %s WHERE user_id = %s", (cash, user_id))
    cursor.execute(
        "INSERT INTO trades (user_id, coin_id, side, amount, price, total) VALUES (%s, %s, 'buy', %s, %s, %s)",
        (user_id, coin_id, amount, price, total)
    )

    symbol = coin["symbol"].upper()
    message = f"Bought {amount.normalize():f} {symbol} at ${price:,.2f} for ${total:,.2f}"
    notify(cursor, user_id, f"CryptoFlash trade: bought {symbol}", message)
    return {"success": True, "message": message, "price": price, "total": total, "cash": cash}


def sell(data, cursor, user_id):
    amount = read_amount(data)
    if amount is None:
        return fail("Enter an amount greater than 0")

    coin_id = data.get("coin_id")
    cursor.execute("SELECT name, symbol, price FROM coins WHERE coin_id = %s", (coin_id,))
    coin = cursor.fetchone()
    if not coin:
        return fail("Coin not found")

    cursor.execute(
        "SELECT amount FROM holdings WHERE user_id = %s AND coin_id = %s FOR UPDATE",
        (user_id, coin_id)
    )
    held = cursor.fetchone()
    owned = Decimal(held["amount"]) if held else Decimal(0)
    symbol = coin["symbol"].upper()
    if amount > owned:
        return fail(f"Not enough coins. You own {owned.normalize():f} {symbol}")

    price = Decimal(coin["price"])
    total = (price * amount).quantize(Decimal("0.01"))
    remaining = owned - amount
    if remaining <= Decimal("0.0000000001"):
        cursor.execute("DELETE FROM holdings WHERE user_id = %s AND coin_id = %s", (user_id, coin_id))
    else:
        cursor.execute(
            "UPDATE holdings SET amount = %s WHERE user_id = %s AND coin_id = %s",
            (remaining, user_id, coin_id)
        )

    cash = get_cash(cursor, user_id, lock=True) + total
    cursor.execute("UPDATE wallets SET cash = %s WHERE user_id = %s", (cash, user_id))
    cursor.execute(
        "INSERT INTO trades (user_id, coin_id, side, amount, price, total) VALUES (%s, %s, 'sell', %s, %s, %s)",
        (user_id, coin_id, amount, price, total)
    )

    message = f"Sold {amount.normalize():f} {symbol} at ${price:,.2f} for ${total:,.2f}"
    notify(cursor, user_id, f"CryptoFlash trade: sold {symbol}", message)
    return {"success": True, "message": message, "price": price, "total": total, "cash": cash}


def get_portfolio(data, cursor, user_id):
    cash = get_cash(cursor, user_id)
    cursor.execute(
        """
        SELECT h.coin_id, h.amount, h.avg_price, c.name, c.symbol, c.price
        FROM holdings h JOIN coins c ON c.coin_id = h.coin_id
        WHERE h.user_id = %s ORDER BY h.amount * c.price DESC
        """,
        (user_id,)
    )
    holdings = []
    holdings_value = Decimal(0)
    for h in cursor.fetchall():
        amount = Decimal(h["amount"])
        avg = Decimal(h["avg_price"])
        price = Decimal(h["price"])
        value = amount * price
        cost = amount * avg
        profit = value - cost
        holdings_value += value
        holdings.append({
            "coin_id": h["coin_id"], "name": h["name"], "symbol": h["symbol"],
            "amount": amount, "avg_price": avg, "current_price": price,
            "value": value.quantize(Decimal("0.01")),
            "profit": profit.quantize(Decimal("0.01")),
            "profit_pct": (profit / cost * 100).quantize(Decimal("0.01")) if cost else 0,
        })

    total_value = cash + holdings_value
    return {
        "success": True, "message": "OK",
        "cash": cash,
        "holdings_value": holdings_value.quantize(Decimal("0.01")),
        "total_value": total_value.quantize(Decimal("0.01")),
        "total_profit": (total_value - STARTING_CASH).quantize(Decimal("0.01")),
        "holdings": holdings,
    }


def get_trades(data, cursor, user_id):
    cursor.execute(
        """
        SELECT t.created_at, t.side, t.coin_id, c.symbol, t.amount, t.price, t.total
        FROM trades t LEFT JOIN coins c ON c.coin_id = t.coin_id
        WHERE t.user_id = %s ORDER BY t.created_at DESC, t.id DESC LIMIT 50
        """,
        (user_id,)
    )
    trades = [
        {
            "time": t["created_at"].strftime("%Y-%m-%d %H:%M"), "side": t["side"],
            "coin_id": t["coin_id"], "symbol": t["symbol"] or t["coin_id"],
            "amount": t["amount"], "price": t["price"], "total": t["total"],
        }
        for t in cursor.fetchall()
    ]
    return {"success": True, "message": "OK", "trades": trades}



def get_watchlist(data, cursor, user_id):
    cursor.execute(
        """
        SELECT c.* FROM watchlist w JOIN coins c ON c.coin_id = w.coin_id
        WHERE w.user_id = %s ORDER BY c.market_cap DESC
        """,
        (user_id,)
    )
    return {"success": True, "message": "OK", "coins": [coin_row(c) for c in cursor.fetchall()]}


def add_watchlist(data, cursor, user_id):
    coin_id = data.get("coin_id")
    cursor.execute("SELECT name FROM coins WHERE coin_id = %s", (coin_id,))
    coin = cursor.fetchone()
    if not coin:
        return fail("Coin not found")
    cursor.execute("INSERT IGNORE INTO watchlist (user_id, coin_id) VALUES (%s, %s)", (user_id, coin_id))
    return {"success": True, "message": f"Added {coin['name']} to your watchlist"}


def remove_watchlist(data, cursor, user_id):
    cursor.execute("DELETE FROM watchlist WHERE user_id = %s AND coin_id = %s", (user_id, data.get("coin_id")))
    return {"success": True, "message": "Removed from watchlist"}


def set_alert(data, cursor, user_id):
    coin_id = data.get("coin_id")
    direction = data.get("direction")
    if direction not in ("above", "below"):
        return fail("Direction must be above or below")
    try:
        target = Decimal(str(data.get("target_price")))
    except Exception:
        return fail("Enter a valid target price")
    if target <= 0:
        return fail("Enter a valid target price")

    cursor.execute("SELECT symbol FROM coins WHERE coin_id = %s", (coin_id,))
    coin = cursor.fetchone()
    if not coin:
        return fail("Coin not found")

    cursor.execute(
        "INSERT INTO alerts (user_id, coin_id, direction, target_price) VALUES (%s, %s, %s, %s)",
        (user_id, coin_id, direction, target)
    )
    return {"success": True, "message": f"Alert set: {coin['symbol'].upper()} {direction} ${target:,.2f}"}


def get_alerts(data, cursor, user_id):
    cursor.execute(
        """
        SELECT a.id, a.coin_id, c.symbol, a.direction, a.target_price, a.triggered
        FROM alerts a LEFT JOIN coins c ON c.coin_id = a.coin_id
        WHERE a.user_id = %s ORDER BY a.triggered, a.created_at DESC
        """,
        (user_id,)
    )
    alerts = [
        {
            "alert_id": a["id"], "coin_id": a["coin_id"], "symbol": a["symbol"] or a["coin_id"],
            "direction": a["direction"], "target_price": a["target_price"], "triggered": bool(a["triggered"]),
        }
        for a in cursor.fetchall()
    ]
    return {"success": True, "message": "OK", "alerts": alerts}


def delete_alert(data, cursor, user_id):
    cursor.execute("DELETE FROM alerts WHERE id = %s AND user_id = %s", (data.get("alert_id"), user_id))
    if cursor.rowcount == 0:
        return fail("Alert not found")
    return {"success": True, "message": "Alert deleted"}


def update_notifications(data, cursor, user_id):
    phone = "".join(ch for ch in str(data.get("phone") or "") if ch.isdigit())
    cursor.execute(
        """
        INSERT INTO user_settings (user_id, email_alerts, text_alerts, phone) VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE email_alerts = VALUES(email_alerts),
            text_alerts = VALUES(text_alerts), phone = VALUES(phone)
        """,
        (user_id, bool(data.get("email_alerts")), bool(data.get("text_alerts")), phone)
    )
    return {"success": True, "message": "Notification settings saved"}


def get_news(data, cursor, user_id):
    try:
        limit = max(1, min(int(data.get("limit") or 20), 100))
    except (TypeError, ValueError):
        limit = 20
    cursor.execute(
        "SELECT title, link, source, published, summary FROM news ORDER BY published DESC, id DESC LIMIT %s",
        (limit,)
    )
    articles = [
        {
            "title": n["title"], "link": n["link"], "source": n["source"],
            "published": n["published"].strftime("%Y-%m-%d %H:%M") if n["published"] else "",
            "summary": n["summary"] or "",
        }
        for n in cursor.fetchall()
    ]
    return {"success": True, "message": "OK", "articles": articles}



def store_prices(data, cursor):
    coins = data.get("coins") or []
    for c in coins:
        if c.get("price") is None:
            continue
        cursor.execute(
            """
            INSERT INTO coins (coin_id, name, symbol, price, change_24h, market_cap)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name), symbol = VALUES(symbol), price = VALUES(price),
                change_24h = VALUES(change_24h), market_cap = VALUES(market_cap)
            """,
            (c["coin_id"], c["name"], c["symbol"], c["price"],
             c.get("change_24h") or 0, int(c.get("market_cap") or 0))
        )
        cursor.execute("INSERT INTO price_history (coin_id, price) VALUES (%s, %s)", (c["coin_id"], c["price"]))

    check_alerts(cursor)
    return {"success": True, "message": f"Stored {len(coins)} coins"}


def check_alerts(cursor):
    cursor.execute(
        """
        SELECT a.id, a.user_id, a.coin_id, a.direction, a.target_price, c.symbol, c.price
        FROM alerts a JOIN coins c ON c.coin_id = a.coin_id
        WHERE a.triggered = FALSE
          AND ((a.direction = 'above' AND c.price >= a.target_price)
            OR (a.direction = 'below' AND c.price <= a.target_price))
        """
    )
    for a in cursor.fetchall():
        cursor.execute("UPDATE alerts SET triggered = TRUE, triggered_at = NOW() WHERE id = %s", (a["id"],))
        symbol = a["symbol"].upper()
        text = (f"{symbol} is now ${Decimal(a['price']):,.2f}, which is {a['direction']} "
                f"your alert price of ${Decimal(a['target_price']):,.2f}.")
        print("Alert triggered:", text)
        notify(cursor, a["user_id"], f"CryptoFlash alert: {symbol}", text)


def store_news(data, cursor):
    added = 0
    for n in data.get("articles") or []:
        if not n.get("title") or not n.get("link"):
            continue
        cursor.execute("SELECT 1 FROM news WHERE link = %s LIMIT 1", (n["link"][:700],))
        if cursor.fetchone():
            continue
        cursor.execute(
            """
            INSERT INTO news (title, link, source, published, summary)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (n["title"][:500], n["link"][:700], (n.get("source") or "")[:100],
             n.get("published") or None, n.get("summary") or "")
        )
        added += cursor.rowcount
    return {"success": True, "message": f"Stored {added} new articles"}



USER_ACTIONS = {
    "get_market": get_market,
    "get_coin": get_coin,
    "buy": buy,
    "sell": sell,
    "get_portfolio": get_portfolio,
    "get_trades": get_trades,
    "get_watchlist": get_watchlist,
    "add_watchlist": add_watchlist,
    "remove_watchlist": remove_watchlist,
    "set_alert": set_alert,
    "get_alerts": get_alerts,
    "delete_alert": delete_alert,
    "update_notifications": update_notifications,
    "get_news": get_news,
}

DATA_ACTIONS = {
    "store_prices": store_prices,
    "store_news": store_news,
}


def handle(data):
    action = data.get("type")

    if action == "register":
        return register_user(data)
    if action == "login":
        return login_user(data)
    if action == "validate_session":
        return validate_session(data)

    if action not in USER_ACTIONS and action not in DATA_ACTIONS:
        return fail("Unknown action")

    db = connect_db()
    cursor = db.cursor(dictionary=True)
    try:
        if action in DATA_ACTIONS:
            response = DATA_ACTIONS[action](data, cursor)
        else:
            user_id = get_user_id(cursor, data)
            if user_id is None:
                return fail("Session invalid")
            response = USER_ACTIONS[action](data, cursor, user_id)
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def process_message(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        if data.get("type") in DATA_ACTIONS:
            print("Received:", data.get("type"), f"({len(data.get('coins') or data.get('articles') or [])} items)")
        else:
            print("Received:", {k: v for k, v in data.items() if k != "password"})
        response = handle(data)
    except Exception as error:
        response = fail(str(error))

    print("Response:", response.get("success"), response.get("message"))

    if properties.reply_to:
        ch.basic_publish(
            exchange="",
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=json.dumps(response, default=to_json)
        )

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=60
    )

    while True:
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=AUTH_QUEUE, durable=True)
            channel.queue_declare(queue=MARKET_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=AUTH_QUEUE, on_message_callback=process_message)
            channel.basic_consume(queue=MARKET_QUEUE, on_message_callback=process_message)
            print("Database listener running")
            print(f"Listening on {AUTH_QUEUE} and {MARKET_QUEUE}")
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Stopped")
            break
        except pika.exceptions.AMQPError as error:
            print(f"Lost connection to RabbitMQ ({error.__class__.__name__}). Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
