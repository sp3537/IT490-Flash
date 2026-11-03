<?php
require_once('common.php');

$news = api('get_news', ['limit' => 30]);

pageTop('News');
?>
<h2>Crypto News</h2>
<p class="muted">Pulled automatically from crypto RSS feeds.</p>

<?php if (!isSuccess($news)): ?>
  <?php showError(errMsg($news, 'Could not load news.')); ?>
<?php elseif (empty($news['articles'])): ?>
  <p class="muted">No articles yet. They'll show up once the news collector runs.</p>
<?php else: ?>
  <?php foreach ($news['articles'] as $a): ?>
    <div class="news-item">
      <a href="<?php echo h($a['link'] ?? '#'); ?>" target="_blank" rel="noopener"><?php echo h($a['title'] ?? ''); ?></a>
      <div class="muted"><?php echo h($a['source'] ?? ''); ?> &middot; <?php echo h($a['published'] ?? ''); ?></div>
      <?php if (!empty($a['summary'])): ?>
        <p><?php echo h(mb_strimwidth(strip_tags($a['summary']), 0, 250, '...')); ?></p>
      <?php endif; ?>
    </div>
  <?php endforeach; ?>
<?php endif; ?>
<?php pageBottom(); ?>
