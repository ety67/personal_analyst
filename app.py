import streamlit as st
import sqlite3
import pandas as pd
import os
import re
from datetime import datetime
from openai import OpenAI

st.set_page_config(page_title="🧠 Личный AI-аналитик", layout="wide")

# 🔐 УНИВЕРСАЛЬНАЯ ИНИЦИАЛИЗАЦИЯ КЛИЕНТА (Облако / Локально)
def get_client_and_model():
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    use_local = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

    if use_local or not api_key:
        # Локальная модель (GPT4All / Ollama / LM Studio)
        client = OpenAI(api_key="not-needed", base_url="http://localhost:4891/v1")
        model = "qwen2.5-1.5b-instruct"
    else:
        # OpenAI Cloud
        client = OpenAI(api_key=api_key)
        model = "gpt-3.5-turbo"
    return client, model

# 🗄 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
DB_PATH = "relationships.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, context TEXT, behavior TEXT, feelings TEXT,
    ai_analysis TEXT, confidence TEXT, threat_level TEXT, created_at TIMESTAMP
)""")
# Миграция: добавляем колонку threat_level, если её нет в старой базе
try:
    c.execute("ALTER TABLE entries ADD COLUMN threat_level TEXT DEFAULT '?'")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Колонка уже существует

# 🧠 ГЛУБОКИЙ ПРОМПТ-ФРЕЙМВОРК
def build_deep_analysis_prompt(context, behavior, feelings):
    return f"""Ты — эксперт по поведенческой психологии, конфликтологии и личной безопасности.
Твоя задача — проанализировать описание взаимодействия и дать ПРАКТИЧЕСКИЙ, глубокий разбор, который поможет пользователю лучше понимать людей, защищать границы и выбирать оптимальную стратегию общения.

ВХОДНЫЕ ДАННЫЕ:
• Контекст: {context or "не указан"}
• Наблюдения (факты поведения): {behavior}
• Ощущения пользователя: {feelings or "не описаны"}

СТРУКТУРА ОТВЕТА (следуй ей строго):

### 🧩 1. Что стоит за этим поведением? (Паттерн)
• Опиши вероятный психологический механизм или мотивацию.
• Объясни, почему такие люди так действуют.
• Подтверди или нормализуй ощущения пользователя: «Ваши чувства логичны, потому что...»

### 🔎 2. Как распознавать таких людей на ранних этапах?
• Перечисли 3–5 конкретных поведенческих маркеров.
• Укажи фразы, жесты или изменения тона, предшествующие конфликту/манипуляции.

### 🗣 3. Стратегия взаимодействия (пошагово)
• Дай чёткий алгоритм: как отвечать, что делать, чего избегать.
• Приведи 2–3 КОНКРЕТНЫЕ фразы для разговора (спокойные, короткие).
• Укажи, как вести себя при продолжении давления.

### ⚖️ 4. Оценка ситуации и приоритеты
• Уровень угрозы: [1–5] с кратким обоснованием.
• Главный приоритет: [безопасность / сохранение энергии / деловая эффективность / эмоциональная дистанция].
• Когда отступить, а когда выстроить рабочие рамки.

### 🌱 5. Долгосрочный навык (рефлексия)
• Как этот опыт прокачивает способность «читать» людей?
• 1 вопрос Франклина: «Что в этой ситуации зависит от меня, а что — нет?»

ПРАВИЛА:
• Пиши как наставник/аналитик: уважительно, без воды, с опорой на факты.
• Не ставь диагнозы. Формулируй как гипотезы: «возможно», «часто указывает на».
• Если данных мало — честно напиши об этом.
• Сохраняй структуру. Используй маркеры и короткие абзацы.
"""

# 🎨 ИНДИКАТОРЫ УГРОЗЫ
def threat_badge(level):
    try:
        l = int(level)
        if l <= 2: return "🟢 Низкий"
        if l == 3: return "🟡 Средний"
        return "🔴 Высокий"
    except:
        return "⚪ Не оценено"

# ─────────────────────────────────────────────────────────────
# 🖥 ИНТЕРФЕЙС
# ─────────────────────────────────────────────────────────────
tab_input, tab_list, tab_export = st.tabs(["📝 Внести запись", "📊 Список людей", "📤 Экспорт"])

# 📥 ВКЛАДКА 1: ВВОД ДАННЫХ
with tab_input:
    with st.form("new_entry"):
        name = st.text_input("Имя / Псевдоним", placeholder="Например: Алексей")
        context = st.text_input("Контекст знакомства", placeholder="Коллега, друг, партнёр...")
        behavior = st.text_area("Наблюдаемое поведение (факты)", placeholder="Перебивает, берёт инициативу, избегает зрительного контакта...")
        feelings = st.text_area("Ваши ощущения и реакции", placeholder="Чувствую напряжение, но уважаю компетентность...")
        analyze_now = st.checkbox("🔍 Сразу проанализировать", value=True)
        submit = st.form_submit_button("💾 Сохранить и проанализировать", type="primary")

    if submit and name and behavior:
        with st.spinner("🤖 ИИ анализирует паттерны..."):
            ai_res = ""
            threat = "?"
            conf = "—"
            if analyze_now:
                client, model = get_client_and_model()
                prompt = build_deep_analysis_prompt(context, behavior, feelings)
                try:
                    res = client.chat.completions.create(
                        model=model, messages=[{"role": "user", "content": prompt}],
                        temperature=0.3, max_tokens=1500
                    )
                    ai_res = res.choices[0].message.content
                    # Авто-извлечение уровня угрозы из ответа ИИ
                    t_match = re.search(r"Уровень угрозы:\s*([1-5])", ai_res)
                    threat = t_match.group(1) if t_match else "?"
                    if "высокий" in ai_res.lower(): conf = "высокий"
                    elif "средний" in ai_res.lower(): conf = "средний"
                    else: conf = "низкий"
                except Exception as e:
                    ai_res = f"⚠️ Ошибка API: {str(e)}"

            c.execute("INSERT INTO entries (name, context, behavior, feelings, ai_analysis, confidence, threat_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (name, context, behavior, feelings, ai_res, conf, threat, datetime.now()))
            conn.commit()
            st.success("✅ Запись сохранена и проанализирована!")
            st.rerun()

# 📊 ВКЛАДКА 2: СПИСОК ЛЮДЕЙ С ЦВЕТОВЫМИ ИНДИКАТОРАМИ
with tab_list:
    df = pd.read_sql_query("SELECT * FROM entries ORDER BY created_at DESC", conn)
    if df.empty:
        st.info("Записей пока нет. Добавьте первую во вкладке «Внести запись».")
    else:
        df["Индикатор"] = df["threat_level"].apply(threat_badge)
        st.dataframe(df[["Индикатор", "id", "name", "context", "threat_level", "created_at"]], use_container_width=True, hide_index=True)
        
        st.divider()
        for _, row in df.iterrows():
            with st.expander(f"👤 {row['name']} (ID: {row['id']}) — {threat_badge(row['threat_level'])}"):
                st.write(f"**📍 Контекст:** {row['context'] or '—'}")
                st.write(f"**👁 Наблюдения:** {row['behavior']}")
                st.write(f"**💭 Ощущения:** {row['feelings'] or '—'}")
                st.markdown("---")
                st.markdown(row['ai_analysis'] if row['ai_analysis'] else "*Анализ не проводился или произошла ошибка*")
                
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("🗑 Удалить", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM entries WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.rerun()

# 📤 ВКЛАДКА 3: ЭКСПОРТ В MARKDOWN
with tab_export:
    st.info("Экспорт в Markdown для Obsidian/Notion. Данные не покидают ваше устройство.")
    rows = conn.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
    if not rows:
        st.warning("Нет данных для экспорта")
    else:
        md = ""
        for r in rows:
            md += f"---\ndate: {r[7]}\nperson: {r[1]}\nthreat_level: {r[8]}\ntags: [relationships, ai-analysis]\n---\n\n## Контекст\n{r[2] or '—'}\n\n## Наблюдения\n{r[3]}\n\n## Ощущения\n{r[4] or '—'}\n\n## AI-анализ\n{r[5] or '—'}\n\n---\n\n"
        st.download_button("📥 Скачать exports.md", data=md, file_name="relationships_export.md", mime="text/markdown")

conn.close()
