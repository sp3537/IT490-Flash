<?php
require_once('common.php');

$portfolio = api('get_portfolio');
$trades    = api('get_trades');
$return = 'portfolio.php';

pageTop('Portfolio');
?>
<h2>Portfolio</h2>
<?php showFlash(); ?>

<?php if (!isSuccess($portfolio)): ?>
  <?php showError(errMsg($portfolio, 'Could not load your portfolio.')); ?>
<?php else: ?>
  <div class="cards">
    <div class="card"><div class="label">Total value</div><div class="value"><?php echo fmtUsd($portfolio['total_value'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Cash</div><div class="value"><?php echo fmtUsd($portfolio['cash'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Coins value</div><div class="value"><?php echo fmtUsd($portfolio['holdings_value'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Total profit / loss</div>
      <div class="value <?php echo upDown($portfolio['total_profit'] ?? 0); ?>"><?php echo fmtSigned($portfolio['total_profit'] ?? 0); ?></div></div>
  </div>
  <p class="muted">Everyone starts with $10,000 in fake money. Profit/loss is compared to that starting balance.</p>

  <h3>Holdings</h3>
  <?php $holdings = $portfolio['holdings'] ?? []; ?>
  <?php if (empty($holdings)): ?>
    <p class="muted">You don't own any coins yet. Head to the <a href="market.php">Market</a> to buy some.</p>
  <?php else: ?>
    <table>
      <tr><th>Coin</th><th>Amount</th><th>Avg buy price</th><th>Current price</th><th>Value</th><th>Profit / loss</th><th>Trade</th></tr>
      <?php foreach ($holdings as $hd): ?>
        <tr>
          <td><a href="coin.php?id=<?php echo urlencode($hd['coin_id'] ?? ''); ?>"><strong><?php echo h($hd['name'] ?? ''); ?></strong></a> <?php echo h(strtoupper($hd['symbol'] ?? '')); ?></td>
          <td><?php echo fmtAmount($hd['amount'] ?? 0); ?></td>
          <td><?php echo fmtPrice($hd['avg_price'] ?? 0); ?></td>
          <td><?php echo fmtPrice($hd['current_price'] ?? 0); ?></td>
          <td><?php echo fmtUsd($hd['value'] ?? 0); ?></td>
          <td class="<?php echo upDown($hd['profit'] ?? 0); ?>"><?php echo fmtSigned($hd['profit'] ?? 0); ?> (<?php echo fmtPct($hd['profit_pct'] ?? 0); ?>)</td>
          <td><?php tradeForm($hd['coin_id'] ?? '', $return); ?></td>
        </tr>
      <?php endforeach; ?>
    </table>
  <?php endif; ?>
<?php endif; ?>

<h3>Trade history</h3>
<?php if (!isSuccess($trades)): ?>
  <p class="muted">Trade history unavailable: <?php echo h(errMsg($trades)); ?></p>
<?php elseif (empty($trades['trades'])): ?>
  <p class="muted">No trades yet.</p>
<?php else: ?>
  <table>
    <tr><th>Time</th><th>Side</th><th>Coin</th><th>Amount</th><th>Price</th><th>Total</th></tr>
    <?php foreach ($trades['trades'] as $t): ?>
      <tr>
        <td><?php echo h($t['time'] ?? ''); ?></td>
        <td class="<?php echo ($t['side'] ?? '') === 'buy' ? 'up' : 'down'; ?>"><?php echo h(strtoupper($t['side'] ?? '')); ?></td>
        <td><?php echo h(strtoupper($t['symbol'] ?? $t['coin_id'] ?? '')); ?></td>
        <td><?php echo fmtAmount($t['amount'] ?? 0); ?></td>
        <td><?php echo fmtPrice($t['price'] ?? 0); ?></td>
        <td><?php echo fmtUsd($t['total'] ?? 0); ?></td>
      </tr>
    <?php endforeach; ?>
  </table>
<?php endif; ?>
<?php pageBottom(); ?>
