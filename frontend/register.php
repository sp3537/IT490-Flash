<?php
session_start();
require_once('rmq.php');
$msg = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $request = [
        'type'     => 'register',
        'username' => trim($_POST['username']),
        'email'    => trim($_POST['email']),
        'password' => $_POST['password']
    ];
    $response = sendToBackend($request);

    if (isSuccess($response)) {
        header("Location: login.php?registered=1");
        exit();
    }
    $msg = is_array($response) && isset($response['message']) ? $response['message'] : "Registration failed.";
}
?>
<!DOCTYPE html>
<html>
<head>
  <title>Register</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f2f2f2; }
    .box { width: 320px; margin: 80px auto; background: white; padding: 25px; border-radius: 8px; }
    input { width: 100%; padding: 8px; margin: 6px 0 14px; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
    .error { color: red; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Create Account</h2>
    <?php if ($msg) echo "<p class='error'>" . htmlspecialchars($msg) . "</p>"; ?>
    <form method="POST">
      Username <input type="text" name="username" required>
      Email <input type="email" name="email" required>
      Password <input type="password" name="password" required>
      <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="login.php">Log in</a></p>
  </div>
</body>
</html>
