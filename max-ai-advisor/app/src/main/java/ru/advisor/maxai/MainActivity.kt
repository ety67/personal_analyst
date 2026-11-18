package ru.advisor.maxai

import android.app.*
import android.content.*
import android.os.*
import android.view.*
import android.widget.*

class MainActivity : Activity() {
 override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState)
  val prefs = getSharedPreferences("config", MODE_PRIVATE)
  val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(24,30,24,16) }
  val title = TextView(this).apply { text="ИИ-советник Lite · v0.3"; textSize=23f }; root.addView(title)
  val help = TextView(this).apply { text="Ручной анализ текста через вставку или меню «Поделиться». Доступа к уведомлениям нет. Текст отправляется на ваш HTTPS-сервер только после подтверждения." }; root.addView(help)
  val url = EditText(this).apply { hint="HTTPS URL сервера, например https://example.org/analyze"; setSingleLine(); setText(prefs.getString("url", "")); inputType=android.text.InputType.TYPE_TEXT_VARIATION_URI }; root.addView(url)
  val token = EditText(this).apply { hint="Токен доступа к серверу"; setSingleLine(); inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD; setText(prefs.getString("token", "")) }; root.addView(token)
  val providers = arrayOf("OpenAI (GPT)", "Google Gemini", "DeepSeek")
  val providerIds = arrayOf("openai", "gemini", "deepseek")
  val providerLabel = TextView(this).apply { text="Модель ИИ (ключи на сервере):" }; root.addView(providerLabel)
  val provider = Spinner(this).apply {
    adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, providers)
    setSelection(providerIds.indexOf(prefs.getString("provider", "openai")).coerceAtLeast(0))
  }; root.addView(provider)
  val status = TextView(this).apply { text="История анализа появится ниже" }; root.addView(status)
  fun save() { prefs.edit().putString("url",url.text.toString().trim()).putString("token",token.text.toString()).putString("provider",providerIds[provider.selectedItemPosition]).apply() }
  val saveButton=Button(this).apply { text="Сохранить настройки"; setOnClickListener { save(); Toast.makeText(this@MainActivity,"Сохранено",Toast.LENGTH_SHORT).show() } }; root.addView(saveButton)
  val analyze=Button(this).apply { text="Анализировать переданный текст"; setOnClickListener { save(); val edit=EditText(this@MainActivity).apply { hint="Вставьте текст"; minLines=3 }; AlertDialog.Builder(this@MainActivity).setTitle("Ручной анализ").setView(edit).setPositiveButton("Анализ") { _,_-> AnalysisClient.submit(this@MainActivity, edit.text.toString(), "manual") }.setNegativeButton("Отмена",null).show() } }; root.addView(analyze)
  val refresh=Button(this).apply { text="Обновить историю"; setOnClickListener { status.text=prefs.getString("history", "История пуста") } }; root.addView(refresh)
  val scroll=ScrollView(this).apply { addView(root) }; setContentView(scroll)
  status.text=prefs.getString("history","История пуста")
  if (intent?.action==Intent.ACTION_SEND && intent.type=="text/plain") { val shared=intent.getStringExtra(Intent.EXTRA_TEXT); if (!shared.isNullOrBlank()) AlertDialog.Builder(this).setTitle("Отправить текст в облачный ИИ?").setMessage(shared.take(300)).setPositiveButton("Отправить") { _,_->AnalysisClient.submit(this,shared,"shared") }.setNegativeButton("Отмена",null).show() }
 }
}
