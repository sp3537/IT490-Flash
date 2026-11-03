<?php
require_once('common.php');
pageTop('Settings');
?>
<h2>Notification Settings</h2>
<?php showFlash(); ?>
<p>Choose how you want to hear about price alerts and trades.</p>

<div class="box">
  <form method="POST" action="action.php">
    <input type="hidden" name="action" value="update_notifications">
    <input type="hidden" name="return" value="settings.php">
    <label><input type="checkbox" name="email_alerts" checked> Email me (to the email I registered with)</label>
    <label><input type="checkbox" name="text_alerts"> Text me</label>
    <label>Phone number (for texts): <input type="tel" name="phone" placeholder="5551234567"></label>
    <button type="submit">Save settings</button>
  </form>
</div>
<?php pageBottom(); ?>
