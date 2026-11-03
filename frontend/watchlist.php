<?php
require_once('common.php');

$watchlist = api('get_watchlist');
$alerts    = api('get_alerts');
$coins = (isSuccess($watchlist) && is_array($watchlist['coins'] ?? null)) ? $watchlist['coins'] : [];
$return = 'watchlist.php';

pageTop('Watchlist');
?>
<h2>Watchlist</h2>
<?php showFlash(); ?>

<?php if (!isSuccess($watchlist)): ?>
  <?php showError(errMsg($watchlist, 'Could not load your watchlist.')); ?>
<?php elseif (empty($coins)): ?>
  <p class="muted">You're not watching any coins yet. Use the "+ Watch" button on the <a href="market.php">Market</a> page.</p>
<?php else: ?>
  <table>
    <tr><th>Coin</th><th>Price</th><th>24h</th><th>Trade</th><th></th></tr>
    <?php foreach ($coins as $c): ?>
      <tr>
        <td><a href="coin.php?id=<?php echo urlencode($c['coin_id'] ?? ''); ?>"><strong><?php echo h($c['name'] ?? ''); ?></strong></a> <?php echo h(strtoupper($c['symbol'] ?? '')); ?></td>
        <td><?php echo fmtPrice($c['price'] ?? 0); ?></td>
        <td class="<?php echo upDown($c['change_24h'] ?? 0); ?>"><?php echo fmtPct($c['change_24h'] ?? 0); ?></td>
        <td><?php tradeForm($c['coin_id'] ?? '', $return); ?></td>
        <td><?php buttonForm('remove_watchlist', ['coin_id' => $c['coin_id'] ?? ''], 'Remove', $return); ?></td>
      </tr>
    <?php endforeach; ?>
  </table>

  <div class="box">
    <strong>Set a buy/sell alert</strong>
    <form method="POST" action="action.php">
      <input type="hidden" name="action" value="set_alert">
      <input type="hidden" name="return" value="<?php echo $return; ?>">
      Alert me when
      <select name="coin_id">
        <?php foreach ($coins as $c): ?>
          <option value="<?php echo h($c['coin_id'] ?? ''); ?>"><?php echo h($c['name'] ?? ''); ?></option>
        <?php endforeach; ?>
      </select>
      goes
      <select name="direction"><option value="below">below (buy signal)</option><option value="above">above (sell signal)</option></select>
      $<input type="number" name="target_price" step="any" min="0" required>
      <button type="submit">Set alert</button>
    </form>
  </div>
<?php endif; ?>

<h3>Your alerts</h3>
<?php if (!isSuccess($alerts)): ?>
  <p class="muted">Alerts unavailable: <?php echo h(errMsg($alerts)); ?></p>
<?php elseif (empty($alerts['alerts'])): ?>
  <p class="muted">No alerts set. You'll get an email or text when one triggers (see <a href="settings.php">Settings</a>).</p>
<?php else: ?>
  <table>
    <tr><th>Coin</th><th>Condition</th><th>Status</th><th></th></tr>
    <?php foreach ($alerts['alerts'] as $a): ?>
      <tr>
        <td><?php echo h(strtoupper($a['symbol'] ?? $a['coin_id'] ?? '')); ?></td>
        <td>Price goes <?php echo h($a['direction'] ?? ''); ?> <?php echo fmtPrice($a['target_price'] ?? 0); ?></td>
        <td><?php echo !empty($a['triggered']) ? '<span class="up">Triggered</span>' : 'Waiting'; ?></td>
        <td><?php buttonForm('delete_alert', ['alert_id' => $a['alert_id'] ?? 0], 'Delete', $return); ?></td>
      </tr>
    <?php endforeach; ?>
  </table>
<?php endif; ?>
<?php pageBottom(); ?>
