import json
import uuid
import bcrypt
import pika
import mysql.connector

# RabbitMQ settings
RABBITMQ_HOST = "100.113.206.1"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "dkr"
RABBITMQ_PASSWORD = "dkr"
RABBITMQ_VHOST = "shlok"
EXCHNAGE = "authExchange"
QUEUE_NAME = "authQueue"

# MySQL settings
DB_HOST = "localhost"
DB_USER = "it490"
DB_PASSWORD = "it490pass"
DB_NAME = "it490"


def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def register_user(data):
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    db = connect_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (username, email, password_hash)
        )

        db.commit()

        return {
            "success": True,
            "message": "Registration successful"
        }

    except mysql.connector.Error as error:
        return {
            "success": False,
            "message": str(error)
        }

    finally:
        cursor.close()
        db.close()


def validate_session(data):
    key = data.get('sessionKey')
    db = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE session_key = %s", (key,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    if row:
        return {'success': True, 'message': 'Session valid', 'username': row[0]}
    return {'success': False, 'message': 'Session invalid'}

def login_user(data):
    username = data.get("username")
    password = data.get("password")

    db = connect_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Login failed"
        }

    if not bcrypt.checkpw(
        password.encode(),
        user["password_hash"].encode()
    ):
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Login failed"
        }

    session_key = str(uuid.uuid4())

    cursor.execute(
        """
        UPDATE users
        SET session_key = %s
        WHERE id = %s
        """,
        (session_key, user["id"])
    )

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Login successful",
        "session_key": session_key
    }


def process_message(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        action = data.get("type")

        print("Received:", data)

        if action == "register":
            response = register_user(data)

        elif action == "login":
            response = login_user(data)

        elif action == "validate_session":
            response = validate_session(data)

        else:
            response = {
                "success": False,
                "message": "Unknown action"
            }

    except Exception as error:
        response = {
            "success": False,
            "message": str(error)
        }

    print("Response:", response)

    if properties.reply_to:
        ch.basic_publish(
            exchange="",
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=json.dumps(response)
        )

    ch.basic_ack(delivery_tag=method.delivery_tag)


credentials = pika.PlainCredentials(
    RABBITMQ_USER,
    RABBITMQ_PASSWORD
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials
    )
)

channel = connection.channel()

channel.queue_declare(
    queue=QUEUE_NAME,
    durable=True
)

channel.basic_consume(
    queue=QUEUE_NAME,
    on_message_callback=process_message
)

print("Database listener runnin")
print("Waiting for authentication messages")

channel.start_consuming()
