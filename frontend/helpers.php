<?php
function api($type, $data = []) {
    $data['type'] = $type;
    if (!empty($_SESSION['sessionKey'])) {
        $data['sessionKey'] = $_SESSION['sessionKey'];
    }
    return sendToBackend($data);
}

function errMsg($response, $fallback = 'Something went wrong.') {
    return (is_array($response) && isset($response['message'])) ? $response['message'] : $fallback;
}

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES); }

function fmtPrice($n) {
    $n = (float)$n;
    return '$' . ($n >= 1 ? number_format($n, 2) : number_format($n, 6));
}
function fmtUsd($n) {
    $n = (float)$n;
    return ($n < 0 ? '-' : '') . '$' . number_format(abs($n), 2);
}
function fmtSigned($n) {
    $n = (float)$n;
    return ($n >= 0 ? '+' : '-') . '$' . number_format(abs($n), 2);
}
function fmtPct($n) {
    $n = (float)$n;
    return ($n >= 0 ? '+' : '') . number_format($n, 2) . '%';
}
function fmtBig($n) {
    $n = (float)$n;
    if ($n >= 1e12) return '$' . number_format($n / 1e12, 2) . 'T';
    if ($n >= 1e9)  return '$' . number_format($n / 1e9, 2) . 'B';
    if ($n >= 1e6)  return '$' . number_format($n / 1e6, 2) . 'M';
    return '$' . number_format($n, 0);
}
function fmtAmount($n) {
    return rtrim(rtrim(number_format((float)$n, 8, '.', ''), '0'), '.');
}
function upDown($n) { return ((float)$n >= 0) ? 'up' : 'down'; }

function showFlash() {
    if (!empty($_SESSION['flash'])) {
        $f = $_SESSION['flash'];
        unset($_SESSION['flash']);
        echo "<div class='flash " . ($f['ok'] ? 'ok' : 'bad') . "'>" . h($f['msg']) . "</div>";
    }
}

function showError($msg) {
    echo "<div class='flash bad'>" . h($msg) . "</div>";
}

function pageTop($title) {
    echo "<!DOCTYPE html>\n<html>\n<head>\n<meta charset='utf-8'>\n";
    echo "<title>" . h($title) . " - CryptoFlash</title>\n";
    echo "<link rel='stylesheet' href='style.css'>\n</head>\n<body>\n";
    include('nav.php');
    echo "<div class='container'>\n";
}

function pageBottom() {
    echo "</div>\n</body>\n</html>\n";
}

function tradeForm($coinId, $return) {
    echo "<form class='inline' method='POST' action='action.php'>";
    echo "<input type='hidden' name='coin_id' value='" . h($coinId) . "'>";
    echo "<input type='hidden' name='return' value='" . h($return) . "'>";
    echo "<input class='amt' type='number' name='amount' step='any' min='0' placeholder='Amount' required>";
    echo "<button class='buy' name='action' value='buy'>Buy</button>";
    echo "<button class='sell' name='action' value='sell'>Sell</button>";
    echo "</form>";
}

function buttonForm($action, $fields, $label, $return, $class = 'small') {
    echo "<form class='inline' method='POST' action='action.php'>";
    echo "<input type='hidden' name='action' value='" . h($action) . "'>";
    echo "<input type='hidden' name='return' value='" . h($return) . "'>";
    foreach ($fields as $k => $v) {
        echo "<input type='hidden' name='" . h($k) . "' value='" . h($v) . "'>";
    }
    echo "<button class='" . h($class) . "'>" . h($label) . "</button>";
    echo "</form>";
}
?>
