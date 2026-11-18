package ru.advisor.maxai

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class MaxNotificationListener : NotificationListenerService() {
 override fun onNotificationPosted(sbn: StatusBarNotification) {
  val prefs=getSharedPreferences("config",MODE_PRIVATE)
  if (!prefs.getBoolean("enabled",false) || sbn.packageName != prefs.getString("package","ru.oneme.app")) return
  val extras=sbn.notification.extras
  val title=extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
  val body=extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() ?: extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
  if (body.isBlank() || body.contains("код подтверждения",true) || body.matches(Regex(".*\\b\\d{4,8}\\b.*"))) return
  AnalysisClient.submit(applicationContext,"От: $title\n$body","notification")
 }
}
