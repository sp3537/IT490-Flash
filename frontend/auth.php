<?php
function requireLogin() {
    if (empty($_SESSION['sessionKey'])) {
        header("Location: login.php");
        exit();
    }
    $response = sendToBackend([
        'type'       => 'validate_session',
        'sessionKey' => $_SESSION['sessionKey']
    ]);
    if (!isSuccess($response)) {
        session_destroy();
        header("Location: login.php");
        exit();
    }
}
?>
