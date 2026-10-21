# RabbitMQ Setup

Host: shlokvm
Tailscale IP: 100.113.206.1

## Ports
- 5672: RabbitMQ AMQP
- 15672: RabbitMQ Management

## Configuration
- Virtual host: shlok
- Exchange: authExchange (topic)
- Queue: authQueue
- Routing key: *

## Users
- shlok: Admin
- Mohammed: Web VM
- dkr: Database VM

## Setup Commands
sudo apt install rabbitmq-server -y
sudo systemctl enable --now rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management

## Firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow from 100.85.120.3 to any port 5672 proto tcp
sudo ufw allow from 100.118.36.30 to any port 5672 proto tcp
sudo ufw enable
