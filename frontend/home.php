<?php
require_once('common.php');

$portfolio = api('get_portfolio');
$watchlist = api('get_watchlist');
$news      = api('get_news', ['limit' => 5]);

pageTop('Home');
?>
<h2>Welcome, <?php echo h($_SESSION['username']); ?>!</h2>
<?php showFlash(); ?>

<?php if (isSuccess($portfolio)): ?>
  <div class="cards">
    <div class="card"><div class="label">Total value</div><div class="value"><?php echo fmtUsd($portfolio['total_value'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Cash</div><div class="value"><?php echo fmtUsd($portfolio['cash'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Total profit / loss</div>
      <div class="value <?php echo upDown($portfolio['total_profit'] ?? 0); ?>"><?php echo fmtSigned($portfolio['total_profit'] ?? 0); ?></div></div>
  </div>
  <a href="portfolio.php">View full portfolio &rarr;</a>
<?php else: ?>
  <p class="muted">Portfolio unavailable: <?php echo h(errMsg($portfolio)); ?></p>
<?php endif; ?>

<h3>Your watchlist</h3>
<?php if (isSuccess($watchlist) && !empty($watchlist['coins'])): ?>
  <table>
    <tr><th>Coin</th><th>Price</th><th>24h</th></tr>
    <?php foreach (array_slice($watchlist['coins'], 0, 5) as $c): ?>
      <tr>
        <td><a href="coin.php?id=<?php echo urlencode($c['coin_id'] ?? ''); ?>"><strong><?php echo h($c['name'] ?? ''); ?></strong></a> <?php echo h(strtoupper($c['symbol'] ?? '')); ?></td>
        <td><?php echo fmtPrice($c['price'] ?? 0); ?></td>
        <td class="<?php echo upDown($c['change_24h'] ?? 0); ?>"><?php echo fmtPct($c['change_24h'] ?? 0); ?></td>
      </tr>
    <?php endforeach; ?>
  </table>
  <p><a href="watchlist.php">Manage watchlist &rarr;</a></p>
<?php elseif (isSuccess($watchlist)): ?>
  <p class="muted">You're not watching any coins yet. Add some from the <a href="market.php">Market</a>.</p>
<?php else: ?>
  <p class="muted">Watchlist unavailable: <?php echo h(errMsg($watchlist)); ?></p>
<?php endif; ?>

<h3>Latest news</h3>
<?php if (isSuccess($news) && !empty($news['articles'])): ?>
  <?php foreach ($news['articles'] as $a): ?>
    <div class="news-item">
      <a href="<?php echo h($a['link'] ?? '#'); ?>" target="_blank" rel="noopener"><?php echo h($a['title'] ?? ''); ?></a>
      <div class="muted"><?php echo h($a['source'] ?? ''); ?> &middot; <?php echo h($a['published'] ?? ''); ?></div>
    </div>
  <?php endforeach; ?>
  <p><a href="news.php">More news &rarr;</a></p>
<?php else: ?>
  <p class="muted">News unavailable: <?php echo h(errMsg($news, 'No articles yet.')); ?></p>
<?php endif; ?>
<?php pageBottom(); ?>
