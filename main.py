"""
DeepThink AutoHustle - версия с ключами внутри кода
"""

import asyncio
import json
from datetime import datetime

# ============= ВСТАВЬ СЮДА СВОИ КЛЮЧИ =============

TELEGRAM_TOKEN = "8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY"
OPENROUTER_KEY = "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"

# ==================================================

# Проверка что ключи вставлены
if TELEGRAM_TOKEN == "8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY":
    print("\n❌ ОШИБКА!")
    print("Замени строку TELEGRAM_TOKEN = ... на свой реальный токен")
    exit(1)

if OPENROUTER_KEY == "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":
    print("\n❌ ОШИБКА!")
    print("Замени строку OPENROUTER_KEY = ... на свой реальный ключ")
    exit(1)

print(f"✅ Токены найдены!")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# OpenRouter клиент
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

# ============= МОЗГ СИСТЕМЫ =============

class DeepThinkBrain:
    def __init__(self):
        self.model = "anthropic/claude-3.5-sonnet"
        self.conversations = {}
    
    async def think(self, user_input: str, user_id: int) -> dict:
        """Главное мышление"""
        
        # Инициализация памяти юзера
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Добавляем в историю
        self.conversations[user_id].append({
            'role': 'user',
            'content': user_input
        })
        
        # ФАЗА 1: Глубокий анализ
        analysis_prompt = f"""Проанализируй запрос пользователя максимально глубоко.

ЗАПРОС: {user_input}

ЗАДАЧА:
1. Понять что РЕАЛЬНО хочет человек (не только что написал)
2. Провести глубокое исследование темы
3. Найти конкретные способы ЗАРАБОТКА на этой теме
4. Дать пошаговый план

СТРУКТУРА ОТВЕТА (используй эмодзи):

🧠 [СУТЬ ТЕМЫ]
[Краткое объяснение что это]

📊 [РЫНОЧНЫЙ АНАЛИЗ]
• Размер рынка: [данные]
• Тренды: [что происходит]
• Возможности: [где можно зайти]

⚠️ [РЕАЛЬНЫЕ СЛОЖНОСТИ]
[Честно о подводных камнях]

💰 [3 СПОСОБА ЗАРАБОТКА]

**СПОСОБ 1: [Название]** (Быстрый старт)
💵 Потенциал: $X-Y/месяц
⏱ Срок: [когда результат]
🤖 AI делает: [что автоматизируется]
👤 Ты делаешь: [твоя роль]
📝 Шаги:
1. [конкретный шаг]
2. [конкретный шаг]
3. [конкретный шаг]

**СПОСОБ 2: [Название]** (Средний уровень)
[аналогично]

**СПОСОБ 3: [Название]** (Масштаб)
[аналогично]

🎯 [МОЯ РЕКОМЕНДАЦИЯ]
[Конкретный совет что делать СЕЙЧАС для конкретного человека]

❓ [УТОЧНЕНИЯ]
[Вопросы чтобы дать еще более точный совет]

Будь максимально конкретным, с цифрами и реальными примерами."""

        try:
            response = ai_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "Ты - эксперт-аналитик который помогает людям зарабатывать деньги. Даёшь глубокие анализы и конкретные планы действий."
                }, {
                    "role": "user",
                    "content": analysis_prompt
                }],
                temperature=0.7,
                max_tokens=4000
            )
            
            answer = response.choices[0].message.content
            
            # Сохраняем в историю
            self.conversations[user_id].append({
                'role': 'assistant',
                'content': answer
            })
            
            # ФАЗА 2: Генерация автоматических действий
            actions = await self._generate_actions(user_input, answer)
            
            return {
                'response': answer,
                'actions': actions
            }
            
        except Exception as e:
            return {
                'response': f"⚠️ Произошла ошибка при анализе:\n{str(e)}\n\nПопробуй переформулировать вопрос.",
                'actions': []
            }
    
    async def _generate_actions(self, user_input: str, analysis: str) -> list:
        """Генерация автоматических действий"""
        
        # Определяем что можно автоматизировать
        actions_prompt = f"""На основе анализа определи что AI может АВТОМАТИЧЕСКИ СОЗДАТЬ для пользователя.

ЗАПРОС: {user_input}
АНАЛИЗ: {analysis[:1000]}

ДОСТУПНЫЕ ТИПЫ ДЕЙСТВИЙ:
- create_content: создать готовый контент (статья, пост, скрипт)
- create_product: создать цифровой продукт для продажи
- create_code: написать рабочий код/сайт
- create_guide: создать подробный гайд/инструкцию
- create_plan: создать бизнес-план

Выбери 1-3 действия которые МАКСИМАЛЬНО полезны.

JSON формат:
[
  {{
    "type": "тип действия",
    "name": "Краткое название",
    "description": "Что именно создастся",
    "value": "Какую ценность даст пользователю"
  }}
]

Только JSON без лишнего текста!"""

        try:
            response = ai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": actions_prompt}],
                temperature=0.5,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            
            # Извлекаем JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            elif "[" in result:
                start = result.find("[")
                end = result.rfind("]") + 1
                result = result[start:end]
            
            actions = json.loads(result.strip())
            return actions if isinstance(actions, list) else []
            
        except:
            return []

# ============= ИСПОЛНИТЕЛЬ ДЕЙСТВИЙ =============

class ActionExecutor:
    def __init__(self):
        self.model = "anthropic/claude-3.5-sonnet"
    
    async def execute(self, action: dict, context: str) -> str:
        """Выполнить автоматическое действие"""
        
        action_type = action['type']
        
        prompts = {
            'create_content': f"""Создай ГОТОВЫЙ К ПУБЛИКАЦИИ контент.

ЗАДАЧА: {action['description']}
КОНТЕКСТ: {context}

ТРЕБОВАНИЯ:
- Профессиональное качество
- Готов к копипасте и использованию
- Структурированный и читаемый
- Практическая ценность

Создай контент который РЕАЛЬНО можно использовать прямо сейчас.""",

            'create_product': f"""Создай ГОТОВЫЙ К ПРОДАЖЕ цифровой продукт.

ЧТО СОЗДАТЬ: {action['description']}
КОНТЕКСТ: {context}

СОЗДАЙ:
1. Сам продукт (полный контент)
2. Описание для продажи
3. Ценообразование
4. Где и как продавать

Продукт должен давать реальную ценность покупателю.""",

            'create_code': f"""Напиши РАБОЧИЙ КОД готовый к запуску.

ПРОЕКТ: {action['description']}
КОНТЕКСТ: {context}

ТРЕБОВАНИЯ:
- Production-ready код
- Комментарии на русском
- Инструкция по запуску
- Список зависимостей

Код должен работать БЕЗ ДОРАБОТОК.""",

            'create_guide': f"""Создай ПОДРОБНЫЙ ПРАКТИЧЕСКИЙ ГАЙД.

ТЕМА: {action['description']}
КОНТЕКСТ: {context}

СТРУКТУРА:
- Введение
- Пошаговая инструкция
- Примеры
- Частые ошибки
- Ресурсы и инструменты

Гайд должен позволить СРАЗУ начать действовать.""",

            'create_plan': f"""Создай ДЕТАЛЬНЫЙ БИЗНЕС-ПЛАН.

ИДЕЯ: {action['description']}
КОНТЕКСТ: {context}

ВКЛЮЧИ:
- Executive Summary
- Анализ рынка
- Стратегия монетизации
- План запуска (помесячно)
- Финансовый прогноз
- Риски и способы их минимизации

План должен быть реалистичным и выполнимым."""
        }
        
        prompt = prompts.get(action_type, prompts['create_guide'])
        
        try:
            response = ai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=8000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Ошибка при создании: {str(e)}"

# ============= ИНИЦИАЛИЗАЦИЯ =============

brain = DeepThinkBrain()
executor = ActionExecutor()

# ============= TELEGRAM HANDLERS =============

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка любого сообщения"""
    
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Показываем процесс мышления
    thinking_msg = await update.message.reply_text(
        "🧠 **ДУМАЮ...**\n\n"
        "⚙️ Анализирую запрос...\n"
        "🔍 Провожу исследование...\n"
        "💰 Ищу способы заработка...\n"
        "🤖 Генерирую план действий...",
        parse_mode='Markdown'
    )
    
    try:
        # ГЛАВНОЕ МЫШЛЕНИЕ
        result = await brain.think(user_message, user_id)
        
        response_text = result['response']
        actions = result['actions']
        
        # Создаём кнопки для автодействий
        keyboard = []
        
        if actions:
            for i, action in enumerate(actions):
                keyboard.append([
                    InlineKeyboardButton(
                        f"🤖 {action['name']}",
                        callback_data=f"exec_{i}_{user_id}"
                    )
                ])
        
        # Отправляем ответ
        if len(response_text) > 4096:
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            await thinking_msg.delete()
            
            for idx, part in enumerate(parts):
                if idx == len(parts) - 1 and keyboard:
                    await update.message.reply_text(
                        part,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(part, parse_mode='Markdown')
        else:
            markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await thinking_msg.edit_text(
                response_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        # Сохраняем действия
        if actions:
            context.user_data[f'actions_{user_id}'] = actions
            context.user_data[f'context_{user_id}'] = user_message
            
    except Exception as e:
        await thinking_msg.edit_text(
            f"⚠️ Ошибка: {str(e)}\n\n"
            "Попробуй переформулировать вопрос."
        )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('exec_'):
        parts = data.split('_')
        action_idx = int(parts[1])
        user_id = int(parts[2])
        
        actions = context.user_data.get(f'actions_{user_id}', [])
        user_context = context.user_data.get(f'context_{user_id}', '')
        
        if action_idx < len(actions):
            action = actions[action_idx]
            
            await query.message.edit_text(
                f"🤖 **ВЫПОЛНЯЮ АВТОМАТИЧЕСКИ**\n\n"
                f"Создаю: {action['name']}\n\n"
                f"Это займёт 1-3 минуты...",
                parse_mode='Markdown'
            )
            
            # ВЫПОЛНЕНИЕ
            result = await executor.execute(action, user_context)
            
            # Отправляем результат
            result_text = (
                f"✅ **ГОТОВО!**\n\n"
                f"**{action['name']}**\n\n"
                f"{result[:3500]}"
            )
            
            if len(result) > 3500:
                result_text += f"\n\n_[Текст обрезан, полная версия {len(result)} символов]_"
            
            await query.message.reply_text(result_text, parse_mode='Markdown')

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    
    await update.message.reply_text(
        "🧠 **DeepThink AutoHustle**\n\n"
        "Я - AI который не просто отвечает, а **ДУМАЕТ** и **ДЕЙСТВУЕТ**.\n\n"
        "**ЧТО Я УМЕЮ:**\n\n"
        "🔍 **Глубокий анализ**\n"
        "Любая тема → полное исследование рынка\n\n"
        "💰 **Поиск заработка**\n"
        "К каждой теме - конкретные способы заработка с цифрами\n\n"
        "🤖 **Автоматическое выполнение**\n"
        "Создаю готовые продукты, контент, код, планы\n\n"
        "**ПРОСТО НАПИШИ:**\n"
        "• расскажи про NFT\n"
        "• как заработать на копирайтинге\n"
        "• анализ рынка EdTech\n"
        "• создай бизнес-план для кофейни\n\n"
        "Я пойму и дам максимально полезный ответ + автоматические действия!\n\n"
        "🚀 **Начни прямо сейчас!**",
        parse_mode='Markdown'
    )

def main():
    """Запуск бота"""
    
    print("\n" + "="*60)
    print("🧠 DEEPTHINK AUTOHUSTLE - ЗАПУСК")
    print("="*60)
    print(f"\n✅ Telegram токен: {TELEGRAM_TOKEN[:15]}...")
    print(f"✅ OpenRouter ключ: {OPENROUTER_KEY[:20]}...")
    print("\n🎯 Возможности:")
    print("  • Глубокий анализ любой темы")
    print("  • Автопоиск способов заработка")
    print("  • Создание готовых продуктов")
    print("  • 95%+ автоматизация\n")
    print("="*60 + "\n")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    print("✅ БОТ АКТИВЕН!")
    print("📱 Проверяй в Telegram\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
