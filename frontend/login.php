<?php
session_start();
require_once('rmq.php');
$msg = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $request = [
        'type'     => 'login',
        'username' => trim($_POST['username']),
        'password' => $_POST['password']
    ];
    $response = sendToBackend($request);

    if (isSuccess($response) && !empty($response['sessionKey'])) {
        $_SESSION['username']   = $request['username'];
        $_SESSION['sessionKey'] = $response['sessionKey'];
        header("Location: home.php");
        exit();
    }
    $msg = is_array($response) && isset($response['message']) ? $response['message'] : "Invalid username or password.";
}
?>
<!DOCTYPE html>
<html>
<head>
  <title>Login</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f2f2f2; }
    .box { width: 320px; margin: 80px auto; background: white; padding: 25px; border-radius: 8px; }
    input { width: 100%; padding: 8px; margin: 6px 0 14px; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
    .error { color: red; }
    .ok { color: green; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Log In</h2>
    <?php if (isset($_GET['registered'])) echo "<p class='ok'>Account created! You can log in now.</p>"; ?>
    <?php if ($msg) echo "<p class='error'>" . htmlspecialchars($msg) . "</p>"; ?>
    <form method="POST">
      Username <input type="text" name="username" required>
      Password <input type="password" name="password" required>
      <button type="submit">Log In</button>
    </form>
    <p>No account? <a href="register.php">Register</a></p>
  </div>
</body>
</html>
