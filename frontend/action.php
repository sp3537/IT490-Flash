<?php
require_once('common.php');

$type   = $_POST['action'] ?? '';
$return = $_POST['return'] ?? 'home.php';

if (!preg_match('/^[a-z]+\.php(\?[A-Za-z0-9_=&%\-]*)?$/', $return)) {
    $return = 'home.php';
}

$coinId = trim($_POST['coin_id'] ?? '');
$data = null;

switch ($type) {
    case 'buy':
    case 'sell':
        $amount = (float)($_POST['amount'] ?? 0);
        if ($coinId === '' || $amount <= 0) {
            $_SESSION['flash'] = ['ok' => false, 'msg' => 'Enter an amount greater than 0.'];
            break;
        }
        $data = ['coin_id' => $coinId, 'amount' => $amount];
        break;

    case 'add_watchlist':
    case 'remove_watchlist':
        $data = ['coin_id' => $coinId];
        break;

    case 'set_alert':
        $direction = ($_POST['direction'] ?? '') === 'above' ? 'above' : 'below';
        $target = (float)($_POST['target_price'] ?? 0);
        if ($coinId === '' || $target <= 0) {
            $_SESSION['flash'] = ['ok' => false, 'msg' => 'Pick a coin and enter a target price.'];
            break;
        }
        $data = ['coin_id' => $coinId, 'direction' => $direction, 'target_price' => $target];
        break;

    case 'delete_alert':
        $data = ['alert_id' => (int)($_POST['alert_id'] ?? 0)];
        break;

    case 'update_notifications':
        $data = [
            'email_alerts' => isset($_POST['email_alerts']),
            'text_alerts'  => isset($_POST['text_alerts']),
            'phone'        => preg_replace('/[^0-9]/', '', $_POST['phone'] ?? ''),
        ];
        break;

    default:
        $_SESSION['flash'] = ['ok' => false, 'msg' => 'Unknown action.'];
}

if ($data !== null) {
    $response = api($type, $data);
    $_SESSION['flash'] = [
        'ok'  => isSuccess($response),
        'msg' => errMsg($response, isSuccess($response) ? 'Done.' : 'Request failed.'),
    ];
}

header("Location: $return");
exit();
?>
