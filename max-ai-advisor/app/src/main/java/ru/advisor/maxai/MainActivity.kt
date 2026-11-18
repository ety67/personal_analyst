package ru.advisor.maxai

import android.Manifest
import android.app.*
import android.content.*
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.*

class MainActivity : Activity() {
 override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState)
  if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 5)
  val prefs = getSharedPreferences("config", MODE_PRIVATE)
  val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(24,30,24,16) }
  val title = TextView(this).apply { text="ИИ-советник MAX · v0.2"; textSize=23f }; root.addView(title)
  val help = TextView(this).apply { text="Анализируются только доступные уведомления MAX. Текст отправляется на указанный HTTPS-сервер. Не используйте для конфиденциальной переписки без разрешения." }; root.addView(help)
  val url = EditText(this).apply { hint="HTTPS URL сервера, например https://example.org/analyze"; setSingleLine(); setText(prefs.getString("url", "")); inputType=android.text.InputType.TYPE_TEXT_VARIATION_URI }; root.addView(url)
  val token = EditText(this).apply { hint="Токен доступа к серверу"; setSingleLine(); inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD; setText(prefs.getString("token", "")) }; root.addView(token)
  val providers = arrayOf("OpenAI (GPT)", "Google Gemini", "DeepSeek")
  val providerIds = arrayOf("openai", "gemini", "deepseek")
  val providerLabel = TextView(this).apply { text="Модель ИИ (ключи на сервере):" }; root.addView(providerLabel)
  val provider = Spinner(this).apply {
    adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, providers)
    setSelection(providerIds.indexOf(prefs.getString("provider", "openai")).coerceAtLeast(0))
  }; root.addView(provider)
  val pkg = EditText(this).apply { hint="Пакет MAX (проверьте на устройстве)"; setSingleLine(); setText(prefs.getString("package", "ru.oneme.app")) }; root.addView(pkg)
  val enabled = Switch(this).apply { text="Включить отправку уведомлений в ИИ"; isChecked=prefs.getBoolean("enabled", false) }; root.addView(enabled)
  val status = TextView(this).apply { text="История анализа появится ниже" }; root.addView(status)
  fun save() { prefs.edit().putString("url",url.text.toString().trim()).putString("token",token.text.toString()).putString("package",pkg.text.toString().trim()).putString("provider",providerIds[provider.selectedItemPosition]).putBoolean("enabled",enabled.isChecked).apply() }
  enabled.setOnCheckedChangeListener { _, _ -> save() }
  val saveButton=Button(this).apply { text="Сохранить настройки"; setOnClickListener { save(); Toast.makeText(this@MainActivity,"Сохранено",Toast.LENGTH_SHORT).show() } }; root.addView(saveButton)
  val permission=Button(this).apply { text="Разрешить доступ к уведомлениям"; setOnClickListener { save(); startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) } }; root.addView(permission)
  val analyze=Button(this).apply { text="Анализировать переданный текст"; setOnClickListener { save(); val edit=EditText(this@MainActivity).apply { hint="Вставьте текст"; minLines=3 }; AlertDialog.Builder(this@MainActivity).setTitle("Ручной анализ").setView(edit).setPositiveButton("Анализ") { _,_-> AnalysisClient.submit(this@MainActivity, edit.text.toString(), "manual") }.setNegativeButton("Отмена",null).show() } }; root.addView(analyze)
  val refresh=Button(this).apply { text="Обновить историю"; setOnClickListener { status.text=prefs.getString("history", "История пуста") } }; root.addView(refresh)
  val scroll=ScrollView(this).apply { addView(root) }; setContentView(scroll)
  status.text=prefs.getString("history","История пуста")
  if (intent?.action==Intent.ACTION_SEND && intent.type=="text/plain") { val shared=intent.getStringExtra(Intent.EXTRA_TEXT); if (!shared.isNullOrBlank()) AlertDialog.Builder(this).setTitle("Отправить текст в облачный ИИ?").setMessage(shared.take(300)).setPositiveButton("Отправить") { _,_->AnalysisClient.submit(this,shared,"shared") }.setNegativeButton("Отмена",null).show() }
 }
}
