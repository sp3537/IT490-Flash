<?php
require_once('path.inc');
require_once('get_host_info.inc');
require_once('rabbitMQLib.inc');

function sendToBackend($request) {
    $client = new rabbitMQClient("testRabbitMQ.ini", "testServer");
    return $client->send_request($request);
}

function isSuccess($response) {
    return is_array($response) && isset($response['returnCode']) && $response['returnCode'] == 1;
}
?>
