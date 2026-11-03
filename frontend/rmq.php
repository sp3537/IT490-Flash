<?php

function sendToBackend($request, $timeout = 15) {
    $ini = parse_ini_file(__DIR__ . '/testRabbitMQ.ini', true);
    $cfg = $ini['testServer'];

    try {
        $conn = new AMQPConnection([
            'host'            => $cfg['BROKER_HOST'],
            'port'            => $cfg['BROKER_PORT'],
            'login'           => $cfg['USER'],
            'password'        => $cfg['PASSWORD'],
            'vhost'           => $cfg['VHOST'],
            'connect_timeout' => 5,
            'read_timeout'    => $timeout,
        ]);
        $conn->connect();
        $channel = new AMQPChannel($conn);

        $replyName = 'reply.' . bin2hex(random_bytes(8));
        $replyQueue = new AMQPQueue($channel);
        $replyQueue->setName($replyName);
        $replyQueue->setFlags(AMQP_EXCLUSIVE | AMQP_AUTODELETE);
        $replyQueue->declareQueue();

        $exchange = new AMQPExchange($channel);
        $exchange->setName($cfg['EXCHANGE']);

        $correlationId = bin2hex(random_bytes(8));
        $exchange->publish(json_encode($request), '*', AMQP_NOPARAM, [
            'reply_to'       => $replyName,
            'correlation_id' => $correlationId,
            'content_type'   => 'application/json',
        ]);

        $result = null;
        $replyQueue->consume(function ($msg, $queue) use ($correlationId, &$result) {
            $queue->ack($msg->getDeliveryTag());
            if ($msg->getCorrelationId() !== $correlationId) {
                return true;
            }
            $result = json_decode($msg->getBody(), true);
            return false;
        });

        $conn->disconnect();
        return is_array($result) ? $result : ['success' => false, 'message' => 'Empty reply from server.'];

    } catch (Exception $e) {
        return ['success' => false, 'message' => 'Backend not responding. Make sure RabbitMQ and the database listener are running.'];
    }
}

function isSuccess($response) {
    if (!is_array($response)) return false;
    if (isset($response['returnCode']) && $response['returnCode'] == 1) return true;
    if (isset($response['success']) && $response['success'] === true) return true;
    return false;
}
?>
