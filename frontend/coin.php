<?php
require_once('common.php');

$coinId = trim($_GET['id'] ?? '');
if ($coinId === '') {
    header("Location: market.php");
    exit();
}
$response = api('get_coin', ['coin_id' => $coinId]);
$coin = (isSuccess($response) && isset($response['coin'])) ? $response['coin'] : null;
$history = (isSuccess($response) && isset($response['history']) && is_array($response['history'])) ? $response['history'] : [];
$return = 'coin.php?id=' . urlencode($coinId);

function priceChart($history) {
    if (count($history) < 2) {
        return "<p class='muted'>Not enough price history yet. The chart fills in as the data collector runs.</p>";
    }
    $w = 900; $h = 260; $pad = 45; $left = 95;
    $prices = array_map(fn($p) => (float)$p['price'], $history);
    $min = min($prices); $max = max($prices);
    if ($max == $min) { $max += 1; $min -= 1; }
    $n = count($prices);
    $points = [];
    foreach ($prices as $i => $p) {
        $x = $left + ($w - $left - $pad) * $i / ($n - 1);
        $y = $h - $pad - ($h - 2 * $pad) * ($p - $min) / ($max - $min);
        $points[] = round($x, 1) . ',' . round($y, 1);
    }
    $color = (end($prices) >= $prices[0]) ? '#138a36' : '#c62828';
    $first = h($history[0]['time'] ?? '');
    $last  = h($history[$n - 1]['time'] ?? '');
    $svg  = "<svg class='chart' viewBox='0 0 $w $h' role='img' aria-label='Price history chart'>";
    $svg .= "<line x1='$left' y1='$pad' x2='" . ($w - $pad) . "' y2='$pad' stroke='#e3e6f0'/>";
    $svg .= "<line x1='$left' y1='" . ($h - $pad) . "' x2='" . ($w - $pad) . "' y2='" . ($h - $pad) . "' stroke='#e3e6f0'/>";
    $svg .= "<text x='5' y='" . ($pad + 4) . "' font-size='12' fill='#666'>" . fmtPrice($max) . "</text>";
    $svg .= "<text x='5' y='" . ($h - $pad + 4) . "' font-size='12' fill='#666'>" . fmtPrice($min) . "</text>";
    $svg .= "<polyline fill='none' stroke='$color' stroke-width='2.5' points='" . implode(' ', $points) . "'/>";
    $svg .= "<text x='$left' y='" . ($h - 12) . "' font-size='12' fill='#666'>$first</text>";
    $svg .= "<text x='" . ($w - $pad) . "' y='" . ($h - 12) . "' font-size='12' fill='#666' text-anchor='end'>$last</text>";
    $svg .= "</svg>";
    return $svg;
}

pageTop($coin['name'] ?? 'Coin');
?>
<p><a href="market.php">&larr; Back to market</a></p>
<?php showFlash(); ?>

<?php if (!$coin): ?>
  <?php showError(errMsg($response, 'Could not load this coin.')); ?>
<?php else: ?>
  <h2><?php echo h($coin['name'] ?? ''); ?> <span class="muted"><?php echo h(strtoupper($coin['symbol'] ?? '')); ?></span></h2>
  <div class="cards">
    <div class="card"><div class="label">Price</div><div class="value"><?php echo fmtPrice($coin['price'] ?? 0); ?></div></div>
    <div class="card"><div class="label">24h change</div><div class="value <?php echo upDown($coin['change_24h'] ?? 0); ?>"><?php echo fmtPct($coin['change_24h'] ?? 0); ?></div></div>
    <div class="card"><div class="label">Market cap</div><div class="value"><?php echo fmtBig($coin['market_cap'] ?? 0); ?></div></div>
  </div>

  <h3>Price history</h3>
  <?php echo priceChart($history); ?>

  <div class="box">
    <strong>Trade</strong><br>
    <?php tradeForm($coinId, $return); ?>
    <?php buttonForm('add_watchlist', ['coin_id' => $coinId], '+ Add to watchlist', $return); ?>
  </div>

  <div class="box">
    <strong>Set a price alert</strong>
    <form method="POST" action="action.php">
      <input type="hidden" name="action" value="set_alert">
      <input type="hidden" name="coin_id" value="<?php echo h($coinId); ?>">
      <input type="hidden" name="return" value="<?php echo h($return); ?>">
      Alert me when the price goes
      <select name="direction"><option value="below">below</option><option value="above">above</option></select>
      $<input type="number" name="target_price" step="any" min="0" required>
      <button type="submit">Set alert</button>
    </form>
  </div>
<?php endif; ?>
<?php pageBottom(); ?>
