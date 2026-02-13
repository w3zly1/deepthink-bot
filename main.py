"""
DeepThink AutoHustle - Совместимая версия
Использует asyncio напрямую для совместимости с Python 3.14
"""

import asyncio
import json
import os
from datetime import datetime

TELEGRAM_TOKEN = "8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY"
OPENROUTER_KEY = "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"

print("🚀 Загрузка...")

import httpx
from openai import OpenAI

ai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

# Память и статистика
user_contexts = {}
stats = {'queries': 0, 'tasks': 0}

# ═══════════════════════════════════════════
# АГЕНТЫ
# ═══════════════════════════════════════════

class Agent:
    def __init__(self, name, role, expertise):
        self.name = name
        self.role = role
        self.expertise = expertise
    
    async def think(self, task, context=""):
        prompt = f"""Ты - {self.name}, {self.role}.
Экспертиза: {self.expertise}

Контекст: {context}

Задача: {task}

Дай подробный, конкретный ответ с цифрами и примерами."""

        try:
            response = ai.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000
            )
            return {'response': response.choices[0].message.content, 'success': True}
        except Exception as e:
            return {'response': f"Ошибка: {e}", 'success': False}

agents = {
    'researcher': Agent("🔬 Исследователь", "Глубокий анализ", "рынки, тренды, данные"),
    'money': Agent("💰 Эксперт заработка", "Монетизация", "заработок, бизнес, доход"),
    'strategy': Agent("🏗️ Стратег", "Планирование", "стратегии, планы, масштабирование"),
    'content': Agent("✍️ Контент", "Создание контента", "тексты, посты, копирайтинг"),
    'coder': Agent("💻 Кодер", "Программирование", "Python, автоматизация, боты"),
    'marketing': Agent("📢 Маркетинг", "Продвижение", "реклама, SMM, growth"),
    'coach': Agent("🎯 Коуч", "Мотивация", "рост, продуктивность, mindset"),
}

print(f"✅ {len(agents)} агентов готовы")

# ═══════════════════════════════════════════
# TELEGRAM BOT (через HTTP API напрямую)
# ═══════════════════════════════════════════

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def send_message(chat_id, text, reply_markup=None):
    """Отправить сообщение"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        data = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": "Markdown"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            await client.post(f"{TELEGRAM_API}/sendMessage", json=data)
        except:
            # Если Markdown не работает, отправляем без него
            data.pop("parse_mode", None)
            await client.post(f"{TELEGRAM_API}/sendMessage", json=data)

async def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактировать сообщение"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:4096]
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        await client.post(f"{TELEGRAM_API}/editMessageText", json=data)

async def answer_callback(callback_id):
    """Ответить на callback"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": callback_id})

async def deep_think(query, user_id):
    """Глубокий анализ с агентами"""
    
    stats['queries'] += 1
    
    # Выбираем агентов
    query_lower = query.lower()
    needed = ['money', 'researcher']
    
    if any(w in query_lower for w in ['план', 'стратегия', 'как начать']):
        needed.append('strategy')
    if any(w in query_lower for w in ['контент', 'текст', 'пост']):
        needed.append('content')
    if any(w in query_lower for w in ['код', 'бот', 'автоматизация']):
        needed.append('coder')
    if any(w in query_lower for w in ['маркетинг', 'реклама']):
        needed.append('marketing')
    
    needed = list(set(needed))[:4]
    
    # Запускаем агентов
    results = []
    for name in needed:
        agent = agents.get(name)
        if agent:
            result = await agent.think(query)
            if result['success']:
                results.append({'agent': agent.name, 'text': result['response']})
    
    # Синтез
    synthesis_prompt = f"""Объедини ответы в один полезный ответ.

ЗАПРОС: {query}

ОТВЕТЫ:
{chr(10).join([f"[{r['agent']}]: {r['text'][:600]}" for r in results])}

СОЗДАЙ ОТВЕТ:

🧠 **СУТЬ**
[объяснение]

📊 **АНАЛИЗ**
[данные]

💰 **КАК ЗАРАБОТАТЬ**

**СПОСОБ 1:** [название]
• Потенциал: $X/мес
• Срок: когда результат
• AI делает: 90%+
• Шаги: 1, 2, 3

**СПОСОБ 2:** [аналогично]

**СПОСОБ 3:** [аналогично]

🎯 **РЕКОМЕНДАЦИЯ**
[что делать сейчас]"""

    try:
        final = ai.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.7,
            max_tokens=3500
        )
        response_text = final.choices[0].message.content
    except Exception as e:
        response_text = f"Ошибка: {e}"
    
    # Генерируем действия
    actions = await generate_actions(query, response_text)
    
    return {
        'response': response_text,
        'agents': [agents[n].name for n in needed if n in agents],
        'actions': actions
    }

async def generate_actions(query, analysis):
    """Генерация действий"""
    prompt = f"""Предложи 3 автоматических действия.

ЗАПРОС: {query}
АНАЛИЗ: {analysis[:1000]}

JSON:
[{{"type":"create_content/create_code/create_plan","name":"Название","description":"Описание"}}]

Только JSON!"""

    try:
        response = ai.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=600
        )
        result = response.choices[0].message.content
        
        if "[" in result:
            start = result.find("[")
            end = result.rfind("]") + 1
            return json.loads(result[start:end])
    except:
        pass
    return []

async def execute_action(action, context):
    """Выполнить действие"""
    prompts = {
        'create_content': f"Создай готовый контент: {action.get('description', '')}",
        'create_code': f"Напиши рабочий код: {action.get('description', '')}",
        'create_plan': f"Создай план: {action.get('description', '')}"
    }
    
    prompt = prompts.get(action.get('type', ''), prompts['create_plan'])
    
    try:
        response = ai.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt + f"\n\nКонтекст: {context}"}],
            temperature=0.6,
            max_tokens=5000
        )
        stats['tasks'] += 1
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

async def handle_update(update):
    """Обработка обновления от Telegram"""
    
    # Обработка сообщений
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_id = update["message"]["from"]["id"]
        text = update["message"]["text"]
        
        if text == "/start":
            await send_message(chat_id, 
                f"🧠 *DeepThink AutoHustle*\n\n"
                f"👥 Агентов: {len(agents)}\n"
                f"🤖 Автоматизация: 95%+\n\n"
                f"*Агенты:*\n"
                f"🔬 Исследователь\n"
                f"💰 Эксперт заработка\n"
                f"🏗️ Стратег\n"
                f"✍️ Контент-мейкер\n"
                f"💻 Кодер\n"
                f"📢 Маркетолог\n"
                f"🎯 Коуч\n\n"
                f"*Примеры:*\n"
                f"• как заработать на AI\n"
                f"• тренды 2025\n"
                f"• создай бизнес-план\n\n"
                f"🚀 Просто напиши вопрос!"
            )
            return
        
        if text == "/help":
            await send_message(chat_id,
                "📖 *Справка*\n\n"
                "/start - Начало\n"
                "/help - Помощь\n\n"
                "Просто напиши вопрос!"
            )
            return
        
        # Обычное сообщение - думаем
        thinking = await send_message(chat_id,
            "🧠 *DEEP THINKING*\n\n"
            "⚙️ Анализирую...\n"
            "🔬 Агенты работают...\n"
            "💰 Ищу заработок..."
        )
        
        try:
            result = await deep_think(text, user_id)
            
            response = result['response']
            actions = result['actions']
            agents_used = result['agents']
            
            footer = f"\n\n---\n👥 Работали: {', '.join(agents_used)}"
            full = response + footer
            
            # Кнопки
            buttons = []
            if actions:
                for i, act in enumerate(actions[:3]):
                    buttons.append([{"text": f"🤖 {act.get('name', 'Действие')[:20]}", "callback_data": f"act_{i}_{user_id}"}])
            buttons.append([{"text": "📊 Статистика", "callback_data": f"stats_{user_id}"}])
            
            reply_markup = {"inline_keyboard": buttons}
            
            # Сохраняем
            user_contexts[user_id] = {'actions': actions, 'context': text}
            
            await send_message(chat_id, full[:4096], reply_markup)
            
        except Exception as e:
            await send_message(chat_id, f"⚠️ Ошибка: {e}")
    
    # Обработка callback
    elif "callback_query" in update:
        callback = update["callback_query"]
        callback_id = callback["id"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]
        
        await answer_callback(callback_id)
        
        if data.startswith("act_"):
            parts = data.split("_")
            idx = int(parts[1])
            uid = int(parts[2])
            
            ctx = user_contexts.get(uid, {})
            actions = ctx.get('actions', [])
            context = ctx.get('context', '')
            
            if idx < len(actions):
                action = actions[idx]
                await send_message(chat_id, f"🤖 Выполняю: {action.get('name', '')}...")
                
                result = await execute_action(action, context)
                await send_message(chat_id, f"✅ *Готово!*\n\n{result[:4000]}")
        
        elif data.startswith("stats_"):
            await send_message(chat_id, 
                f"📊 *Статистика*\n\n"
                f"💬 Запросов: {stats['queries']}\n"
                f"✅ Задач: {stats['tasks']}\n"
                f"👥 Агентов: {len(agents)}"
            )

async def main():
    """Главный цикл бота"""
    
    print("\n" + "="*50)
    print("🧠 DEEPTHINK AUTOHUSTLE")
    print("="*50)
    print(f"👥 Агентов: {len(agents)}")
    print("="*50 + "\n")
    
    offset = 0
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("✅ БОТ ЗАПУЩЕН!")
        print("📱 Проверяй в Telegram\n")
        
        while True:
            try:
                # Получаем обновления
                response = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                
                data = response.json()
                
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        await handle_update(update)
                
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
