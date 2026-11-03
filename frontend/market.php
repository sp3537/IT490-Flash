<?php
require_once('common.php');

$search = trim($_GET['search'] ?? '');
$response = api('get_market', ['search' => $search]);
$coins = (isSuccess($response) && isset($response['coins']) && is_array($response['coins'])) ? $response['coins'] : [];
$return = 'market.php' . ($search !== '' ? '?search=' . urlencode($search) : '');

pageTop('Market');
?>
<h2>Market</h2>
<?php showFlash(); ?>
<form method="GET">
  <input type="text" name="search" placeholder="Search by name or symbol" value="<?php echo h($search); ?>">
  <button type="submit">Search</button>
  <?php if ($search !== '') echo ' <a href="market.php">Clear</a>'; ?>
</form>

<?php if (!isSuccess($response)): ?>
  <?php showError(errMsg($response, 'Could not load market data.')); ?>
<?php elseif (empty($coins)): ?>
  <p>No coins found.</p>
<?php else: ?>
  <table>
    <tr><th>#</th><th>Coin</th><th>Price</th><th>24h</th><th>Market Cap</th><th>Trade</th><th></th></tr>
    <?php foreach ($coins as $i => $c): ?>
      <tr>
        <td><?php echo $i + 1; ?></td>
        <td><a href="coin.php?id=<?php echo urlencode($c['coin_id'] ?? ''); ?>"><strong><?php echo h($c['name'] ?? ''); ?></strong></a> <?php echo h(strtoupper($c['symbol'] ?? '')); ?></td>
        <td><?php echo fmtPrice($c['price'] ?? 0); ?></td>
        <td class="<?php echo upDown($c['change_24h'] ?? 0); ?>"><?php echo fmtPct($c['change_24h'] ?? 0); ?></td>
        <td><?php echo fmtBig($c['market_cap'] ?? 0); ?></td>
        <td><?php tradeForm($c['coin_id'] ?? '', $return); ?></td>
        <td><?php buttonForm('add_watchlist', ['coin_id' => $c['coin_id'] ?? ''], '+ Watch', $return); ?></td>
      </tr>
    <?php endforeach; ?>
  </table>
  <p class="muted">Amount is the number of coins. Trades use the latest price in our database.</p>
<?php endif; ?>
<?php pageBottom(); ?>
