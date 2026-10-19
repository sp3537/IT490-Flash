<?php
session_start();
require_once('rmq.php');

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
?>
<!DOCTYPE html>
<html>
<head>
  <title>Home</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f2f2f2; }
    .box { width: 400px; margin: 80px auto; background: white; padding: 25px; border-radius: 8px; text-align: center; }
    a { color: #0066cc; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Welcome, <?php echo htmlspecialchars($_SESSION['username']); ?>!</h2>
    <p>You are logged in.</p>
    <p><a href="logout.php">Log out</a></p>
  </div>
</body>
</html>
