import pandas as pd
import streamlit as st
import sqlite3
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "relationships.db"
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ Не найден OPENAI_API_KEY в файле .env. Скопируйте .env.example в .env и вставьте ваш ключ.")
    st.stop()

client = OpenAI(api_key=API_KEY)

# --- Инициализация БД ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, context TEXT, behavior TEXT, feelings TEXT,
        ai_analysis TEXT, confidence TEXT, created_at TIMESTAMP
    )""")
    conn.commit()
    conn.close()

init_db()

# --- UI ---
st.set_page_config(page_title="🧠 Личный AI-аналитик", layout="wide")
st.title("🧠 Персональный AI-аналитик отношений")
st.caption("Инструмент рефлексии. Данные хранятся локально. ИИ даёт гипотезы, а не диагнозы.")

tab_input, tab_list, tab_export = st.tabs(["📝 Внести запись", "📊 Список людей", "📤 Экспорт"])

with tab_input:
    with st.form("new_entry"):
        name = st.text_input("Имя / Псевдоним", placeholder="Например: Алексей")
        context = st.text_input("Контекст знакомства", placeholder="Коллега, друг, партнёр, знакомый в соцсетях...")
        behavior = st.text_area("Наблюдаемое поведение (факты)", placeholder="Перебивает, берёт инициативу, выполняет обещания, избегает зрительного контакта...")
        feelings = st.text_area("Ваши ощущения и реакции", placeholder="Чувствую напряжение, но уважаю компетентность...")
        
        col1, col2 = st.columns(2)
        analyze_now = col1.checkbox("🔍 Сразу проанализировать", value=True)
        submit = col2.form_submit_button("💾 Сохранить", type="primary")

    if submit and name and behavior:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        ai_res = ""
        conf = "—"
        if analyze_now:
            with st.spinner("🤖 ИИ анализирует паттерны..."):
                prompt = f"""Ты — персональный аналитик взаимодействия. Работай в рамках психологических моделей (Big Five, теория привязанности, коммуникационные стили).
                Контекст: {context or "не указан"}
                Поведение: {behavior}
                Мои ощущения: {feelings or "не описаны"}
                
                Дай:
                1. Гипотезу о возможных чертах/паттернах (кратко)
                2. 1-2 практических совета по выстраиванию коммуникации
                3. Уровень уверенности: низкий / средний / высокий
                
                Важно: формулируй как гипотезы, не ставь диагнозов. Будь объективен, учитывай контекст."""
                try:
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
                    ai_res = res.choices[0].message.content
                    if "высокий" in ai_res.lower(): conf = "высокий"
                    elif "средний" in ai_res.lower(): conf = "средний"
                    else: conf = "низкий"
                except Exception as e:
                    ai_res = f"Ошибка API: {str(e)}"
        
        c.execute("INSERT INTO entries (name, context, behavior, feelings, ai_analysis, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (name, context, behavior, feelings, ai_res, conf, datetime.now()))
        conn.commit()
        conn.close()
        st.success("✅ Запись сохранена!")
        st.rerun()

with tab_list:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name, context, behavior, feelings, ai_analysis, confidence, created_at FROM entries ORDER BY created_at DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Записей пока нет. Добавьте первую во вкладке «Внести запись».")
    else:
        st.table(df.reset_index(drop=True))
        
        st.divider()
        del_id = st.number_input("ID записи для удаления", min_value=1, step=1)
        if st.button("🗑 Удалить запись"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM entries WHERE id = ?", (del_id,))
            conn.commit()
            conn.close()
            st.success("Удалено!")
            st.rerun()

with tab_export:
    st.info("Экспорт в Markdown для Obsidian/Notion")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM entries").fetchall()
    conn.close()
    
    if not rows:
        st.warning("Нет данных для экспорта")
    else:
        md = ""
        for r in rows:
            md += f"---\ndate: {r[7]}\nperson: {r[1]}\ntags: [relationships, ai-analysis]\n---\n\n## Контекст\n{r[2] or '—'}\n\n## Наблюдения\n{r[3]}\n\n## Ощущения\n{r[4] or '—'}\n\n## AI-анализ\n{r[5] or '—'}\n\n---\n\n"
        
        st.download_button("📥 Скачать exports.md", data=md, file_name="relationships_export.md", mime="text/markdown")
