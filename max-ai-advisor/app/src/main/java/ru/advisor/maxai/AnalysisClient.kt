package ru.advisor.maxai

import android.app.*
import android.content.*
import android.os.Build
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

object AnalysisClient {
 private val pool=Executors.newSingleThreadExecutor()
 fun submit(context: Context, text: String, source: String) {
  if(text.isBlank()) return
  val app=context.applicationContext
  val prefs=app.getSharedPreferences("config",Context.MODE_PRIVATE)
  val endpoint=prefs.getString("url", "").orEmpty()
  val token=prefs.getString("token", "").orEmpty()
  if(!endpoint.startsWith("https://") || token.isBlank()) return
  pool.execute {
   try {
    val conn=(URL(endpoint).openConnection() as HttpURLConnection).apply { requestMethod="POST"; connectTimeout=12000; readTimeout=35000; doOutput=true; setRequestProperty("Content-Type","application/json; charset=utf-8"); setRequestProperty("Authorization","Bearer $token") }
    try {
     conn.outputStream.use { it.write(JSONObject().put("text",text.take(6000)).put("source",source).put("provider",prefs.getString("provider","openai")).toString().toByteArray(Charsets.UTF_8)) }
     if(conn.responseCode !in 200..299) return@execute
     val result=JSONObject(conn.inputStream.bufferedReader().use { it.readText() }).optString("analysis","Нет результата").take(5000)
     val old=prefs.getString("history","").orEmpty()
     prefs.edit().putString("history",(java.text.SimpleDateFormat("dd.MM HH:mm",java.util.Locale.getDefault()).format(java.util.Date())+" · "+source+"\n"+result+"\n\n"+old).take(30000)).apply()
    } finally { conn.disconnect() }
   } catch (_:Exception) { /* Не отправляем содержимое сообщений в логи */ }
  }
 }
}
