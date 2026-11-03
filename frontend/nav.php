<?php $current = basename($_SERVER['PHP_SELF']); ?>
<div class="nav">
  <a class="brand" href="home.php">CryptoFlash</a>
  <div class="links">
    <?php
    $pages = [
        'home.php'      => 'Home',
        'market.php'    => 'Market',
        'portfolio.php' => 'Portfolio',
        'watchlist.php' => 'Watchlist',
        'news.php'      => 'News',
        'settings.php'  => 'Settings',
    ];
    foreach ($pages as $file => $label) {
        $active = ($current === $file) ? " class='active'" : "";
        echo "<a href='$file'$active>$label</a>";
    }
    ?>
    <span class="user"><?php echo htmlspecialchars($_SESSION['username'] ?? ''); ?></span>
    <a href="logout.php">Log out</a>
  </div>
</div>
