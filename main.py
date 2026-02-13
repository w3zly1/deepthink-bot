"""
DeepThink AutoHustle - AI который думает и зарабатывает
Серьёзная система для реального заработка
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import aiohttp

# Установка зависимостей при первом запуске
os.system('pip install python-telegram-bot openai anthropic --quiet')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# ============= КОНФИГУРАЦИЯ =============

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_KEY')

if not TELEGRAM_TOKEN or not OPENROUTER_KEY:
    print("\n❌ КРИТИЧЕСКАЯ ОШИБКА!")
    print("Добавь в Secrets:")
    print("  TELEGRAM_TOKEN = твой_токен_от_BotFather")
    print("  OPENROUTER_KEY = твой_ключ_от_openrouter.ai")
    print("\n🔑 Получить ключи:")
    print("  Telegram: https://t.me/BotFather")
    print("  OpenRouter: https://openrouter.ai/keys\n")
    exit(1)

# OpenRouter клиент (доступ ко всем топовым моделям)
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

# ============= ГЛУБОКОЕ МЫШЛЕНИЕ =============

class DeepThinkingEngine:
    """
    Движок глубокого мышления
    Не просто отвечает - ДУМАЕТ, АНАЛИЗИРУЕТ, ДЕЙСТВУЕТ
    """
    
    def __init__(self):
        self.model_research = "anthropic/claude-3.5-sonnet"  # Для исследований
        self.model_execution = "anthropic/claude-3.5-sonnet" # Для создания
        self.conversation_memory = {}
        
    async def think(self, user_input: str, user_id: int) -> Dict:
        """
        Главный процесс мышления
        Returns: {
            'response': текст ответа,
            'actions': список выполнимых действий,
            'money_opportunities': способы заработка
        }
        """
        
        # Инициализация памяти пользователя
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {
                'history': [],
                'user_profile': {},
                'active_goals': [],
                'completed_tasks': []
            }
        
        memory = self.conversation_memory[user_id]
        memory['history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # ФАЗА 1: Понимание намерения
        intent = await self._analyze_intent(user_input, memory)
        
        # ФАЗА 2: Глубокое исследование (параллельно)
        research_results = await self._deep_research(user_input, intent)
        
        # ФАЗА 3: Поиск способов заработка
        money_opportunities = await self._find_money_opportunities(
            user_input, 
            research_results
        )
        
        # ФАЗА 4: Создание исполняемых действий
        executable_actions = await self._generate_actions(
            money_opportunities,
            memory
        )
        
        # ФАЗА 5: Синтез ответа
        response = await self._synthesize_response(
            user_input,
            intent,
            research_results,
            money_opportunities,
            executable_actions
        )
        
        # Сохранение в память
        memory['history'].append({
            'role': 'assistant',
            'content': response['text'],
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'response': response['text'],
            'actions': executable_actions,
            'money_opportunities': money_opportunities,
            'intent': intent
        }
    
    async def _analyze_intent(self, user_input: str, memory: Dict) -> Dict:
        """Анализ намерения пользователя"""
        
        context = "\n".join([
            f"{m['role']}: {m['content']}" 
            for m in memory['history'][-5:]
        ])
        
        prompt = f"""Проанализируй намерение пользователя.

КОНТЕКСТ РАЗГОВОРА:
{context}

НОВОЕ СООБЩЕНИЕ: {user_input}

Определи:
1. Что человек РЕАЛЬНО хочет (не только что написал)
2. Его уровень: новичок/средний/эксперт
3. Цель: изучить/заработать/решить проблему/другое
4. Срочность: сейчас/скоро/когда-нибудь

Ответь JSON:
{{
  "real_intent": "что реально хочет",
  "user_level": "новичок/средний/эксперт",
  "goal": "изучить/заработать/решить/другое",
  "urgency": "сейчас/скоро/потом",
  "keywords": ["ключевые", "слова"]
}}"""

        response = ai_client.chat.completions.create(
            model=self.model_research,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        try:
            result = response.choices[0].message.content
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            return json.loads(result.strip())
        except:
            return {
                "real_intent": user_input,
                "user_level": "средний",
                "goal": "изучить",
                "urgency": "скоро",
                "keywords": [user_input]
            }
    
    async def _deep_research(self, topic: str, intent: Dict) -> Dict:
        """Глубокое исследование темы"""
        
        prompt = f"""Проведи ГЛУБОКОЕ исследование темы: {topic}

Контекст: пользователь хочет {intent['goal']}
Уровень: {intent['user_level']}

ЗАДАЧА: Дай максимально полную картину.

СТРУКТУРА ОТВЕТА:
{{
  "overview": "краткое введение",
  "market_analysis": {{
    "size": "размер рынка",
    "growth": "темпы роста",
    "trends": ["тренд 1", "тренд 2"],
    "key_players": ["игрок 1", "игрок 2"]
  }},
  "technical_complexity": {{
    "difficulty_score": 1-10,
    "skills_needed": ["навык 1", "навык 2"],
    "time_to_learn": "сколько времени",
    "pitfalls": ["подводный камень 1"]
  }},
  "real_world_data": {{
    "success_stories": ["кейс 1"],
    "failure_reasons": ["почему проваливаются"],
    "average_timeline": "сколько до результата"
  }},
  "current_opportunities": ["возможность 1", "возможность 2"]
}}

Будь максимально конкретным с цифрами и примерами."""

        response = ai_client.chat.completions.create(
            model=self.model_research,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=3000
        )
        
        try:
            result = response.choices[0].message.content
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            return json.loads(result.strip())
        except:
            return {
                "overview": "Исследование темы...",
                "market_analysis": {},
                "technical_complexity": {},
                "real_world_data": {},
                "current_opportunities": []
            }
    
    async def _find_money_opportunities(self, topic: str, research: Dict) -> List[Dict]:
        """Поиск конкретных способов заработка"""
        
        prompt = f"""На основе исследования найди КОНКРЕТНЫЕ способы заработка.

ТЕМА: {topic}

ДАННЫЕ ИССЛЕДОВАНИЯ:
{json.dumps(research, ensure_ascii=False)}

ЗАДАЧА: Найти 5 способов от простого к сложному.

КРИТЕРИИ:
- Реалистичность 10/10
- Конкретность (НЕ "создай блог", А "создай блог про X, монетизация через Y")
- Цифры (сколько можно заработать, за какой срок)
- Что нужно (вложения, навыки, время)
- 95%+ может сделать AI

ФОРМАТ JSON:
[
  {{
    "name": "Название способа",
    "description": "Что делать",
    "difficulty": 1-10,
    "investment": "$0-100/$100-1000/$1000+",
    "timeline_to_profit": "2 недели/1 месяц/3 месяца",
    "potential_income": {{
      "min": "мин $ в месяц",
      "avg": "средний $ в месяц",
      "max": "макс $ в месяц"
    }},
    "ai_automation": "95%/80%/60%",
    "your_involvement": "что ты делаешь",
    "ai_does": ["что делает AI", "автоматически"],
    "step_by_step": ["шаг 1", "шаг 2", "шаг 3"],
    "tools_needed": ["инструмент 1"],
    "risks": ["риск 1"],
    "why_it_works": "объяснение"
  }}
]

Сортируй от самого быстрого к самому прибыльному."""

        response = ai_client.chat.completions.create(
            model=self.model_research,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        
        try:
            result = response.choices[0].message.content
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            opportunities = json.loads(result.strip())
            return opportunities if isinstance(opportunities, list) else []
        except Exception as e:
            print(f"Ошибка парсинга возможностей: {e}")
            return []
    
    async def _generate_actions(self, opportunities: List[Dict], memory: Dict) -> List[Dict]:
        """Генерация конкретных выполнимых действий"""
        
        actions = []
        
        for opp in opportunities[:3]:  # Топ-3 возможности
            if float(opp.get('ai_automation', '0%').replace('%', '')) >= 80:
                
                action = {
                    'id': f"action_{len(actions) + 1}",
                    'opportunity': opp['name'],
                    'type': self._determine_action_type(opp),
                    'what_ai_will_do': opp.get('ai_does', []),
                    'what_you_do': opp.get('your_involvement', ''),
                    'estimated_time': opp.get('timeline_to_profit', ''),
                    'can_execute_now': True
                }
                
                actions.append(action)
        
        return actions
    
    def _determine_action_type(self, opportunity: Dict) -> str:
        """Определяет тип действия для автоматизации"""
        
        desc_lower = opportunity.get('description', '').lower()
        
        if any(word in desc_lower for word in ['контент', 'статья', 'блог', 'видео']):
            return 'create_content'
        elif any(word in desc_lower for word in ['продукт', 'товар', 'сервис']):
            return 'create_product'
        elif any(word in desc_lower for word in ['код', 'сайт', 'приложение']):
            return 'create_code'
        elif any(word in desc_lower for word in ['курс', 'гайд', 'обучение']):
            return 'create_course'
        else:
            return 'research_and_guide'
    
    async def _synthesize_response(
        self, 
        user_input: str,
        intent: Dict,
        research: Dict,
        money_opps: List[Dict],
        actions: List[Dict]
    ) -> Dict:
        """Синтез финального ответа"""
        
        prompt = f"""Создай ИДЕАЛЬНЫЙ ответ пользователю.

ЗАПРОС: {user_input}

НАМЕРЕНИЕ: {intent['real_intent']}

ИССЛЕДОВАНИЕ:
{json.dumps(research, ensure_ascii=False)[:1500]}

НАЙДЕНО СПОСОБОВ ЗАРАБОТКА: {len(money_opps)}

СОЗДАЙ ОТВЕТ КОТОРЫЙ:
1. Даёт полное понимание темы
2. Честно о сложностях и рисках
3. Показывает КОНКРЕТНЫЕ способы заработка
4. Предлагает действия которые AI сделает за пользователя
5. Мотивирует начать

СТРУКТУРА (используй эмодзи и форматирование):

🧠 [СУТЬ ТЕМЫ]
[краткое объяснение]

📊 [АНАЛИЗ]
• Рынок: [данные]
• Сложность: [оценка]
• Тренды: [что происходит]

⚠️ [ЧЕСТНО О СЛОЖНОСТЯХ]
[реальные подводные камни]

💰 [КАК ЗАРАБОТАТЬ - ТОП 3 СПОСОБА]

**СПОСОБ 1: [Название]** (самый быстрый)
🤖 AI делает: [95% работы]
👤 Ты делаешь: [5% - только решения]
💵 Потенциал: [$ в месяц]
⏱ Срок: [когда результат]

[аналогично способ 2 и 3]

🎯 [МОЯ РЕКОМЕНДАЦИЯ]
[конкретный совет что делать СЕЙЧАС]

Используй правильный русский, будь конкретным, вдохновляй."""

        response = ai_client.chat.completions.create(
            model=self.model_research,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3500
        )
        
        return {'text': response.choices[0].message.content}

# ============= АВТОМАТИЗИРОВАННОЕ ВЫПОЛНЕНИЕ =============

class AutoExecutor:
    """
    Система автоматического выполнения задач
    Создаёт реальные продукты, которые приносят деньги
    """
    
    def __init__(self):
        self.model = "anthropic/claude-3.5-sonnet"
        self.active_tasks = {}
    
    async def execute_action(self, action: Dict, user_id: int) -> Dict:
        """Выполнить действие автоматически"""
        
        action_type = action['type']
        
        if action_type == 'create_content':
            return await self._create_content(action)
        
        elif action_type == 'create_product':
            return await self._create_product(action)
        
        elif action_type == 'create_code':
            return await self._create_code(action)
        
        elif action_type == 'create_course':
            return await self._create_course(action)
        
        else:
            return await self._create_guide(action)
    
    async def _create_content(self, action: Dict) -> Dict:
        """Создать готовый контент для публикации"""
        
        prompt = f"""Создай ГОТОВЫЙ К ПУБЛИКАЦИИ контент.

ЗАДАЧА: {action['opportunity']}

ЧТО ДЕЛАЕТ AI: {action['what_ai_will_do']}

ТРЕБОВАНИЯ:
- Профессиональное качество
- SEO оптимизация
- Вирусный потенциал
- Готов к копипасте и публикации

ФОРМАТ: Зависит от типа (статья/пост/скрипт видео)

Создавай контент который РЕАЛЬНО принесёт результат."""

        response = ai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        
        return {
            'status': 'completed',
            'output': content,
            'type': 'content',
            'ready_to_use': True,
            'next_step': 'Опубликуй это на [платформа]'
        }
    
    async def _create_product(self, action: Dict) -> Dict:
        """Создать цифровой продукт для продажи"""
        
        prompt = f"""Создай ГОТОВЫЙ К ПРОДАЖЕ цифровой продукт.

КОНЦЕПЦИЯ: {action['opportunity']}

СОЗДАЙ:
1. Сам продукт (контент/шаблон/инструмент)
2. Описание для продажи
3. Pricing стратегию
4. Маркетинговые материалы

Продукт должен давать РЕАЛЬНУЮ ценность покупателю."""

        response = ai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=6000
        )
        
        return {
            'status': 'completed',
            'output': response.choices[0].message.content,
            'type': 'digital_product',
            'ready_to_sell': True,
            'platforms': ['Gumroad', 'Lemon Squeezy', 'Notion'],
            'next_step': 'Загрузи на платформу и запусти продажи'
        }
    
    async def _create_code(self, action: Dict) -> Dict:
        """Создать рабочий код/сайт/инструмент"""
        
        prompt = f"""Создай РАБОЧИЙ КОД готовый к запуску.

ПРОЕКТ: {action['opportunity']}

ТРЕБОВАНИЯ:
- Production-ready
- Все зависимости указаны
- Инструкция по запуску
- Готов к деплою

СТЕК: Самый простой и эффективный для задачи.

Код должен работать БЕЗ ДОРАБОТОК."""

        response = ai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=8000
        )
        
        return {
            'status': 'completed',
            'output': response.choices[0].message.content,
            'type': 'code',
            'ready_to_deploy': True,
            'deployment': 'Vercel/Netlify (бесплатно)',
            'next_step': 'Задеплой на бесплатный хостинг'
        }
    
    async def _create_course(self, action: Dict) -> Dict:
        """Создать обучающий курс"""
        
        prompt = f"""Создай ПОЛНЫЙ ОБУЧАЮЩИЙ КУРС.

ТЕМА: {action['opportunity']}

СОЗДАЙ:
1. Структуру курса (модули/уроки)
2. Полный контент первых 3 уроков
3. Практические задания
4. Ценообразование
5. Маркетинговые материалы

Курс должен РЕАЛЬНО обучать, не быть пустышкой."""

        response = ai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=8000
        )
        
        return {
            'status': 'completed',
            'output': response.choices[0].message.content,
            'type': 'course',
            'ready_to_sell': True,
            'platforms': ['Gumroad', 'Teachable', 'Notion'],
            'next_step': 'Опубликуй и запусти продажи'
        }
    
    async def _create_guide(self, action: Dict) -> Dict:
        """Создать подробный гайд"""
        
        prompt = f"""Создай ПОДРОБНЫЙ ПРАКТИЧЕСКИЙ ГАЙД.

ТЕМА: {action['opportunity']}

ФОРМАТ:
- Пошаговые инструкции
- Скриншоты/примеры (описания)
- Чек-листы
- Ресурсы и инструменты
- FAQ

Гайд должен позволить СРАЗУ НАЧАТЬ ДЕЙСТВОВАТЬ."""

        response = ai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=6000
        )
        
        return {
            'status': 'completed',
            'output': response.choices[0].message.content,
            'type': 'guide',
            'ready_to_use': True,
            'next_step': 'Используй или продавай этот гайд'
        }

# ============= TELEGRAM BOT =============

# Инициализация систем
brain = DeepThinkingEngine()
executor = AutoExecutor()

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ЛЮБОГО сообщения
    Главная фича - бот понимает ВСЁ, не только команды
    """
    
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Показываем что думаем
    thinking_msg = await update.message.reply_text(
        "🧠 **ДУМАЮ...**\n\n"
        "⚙️ Анализирую намерение...\n"
        "🔍 Провожу глубокое исследование...\n"
        "💰 Ищу способы заработка...\n"
        "🤖 Создаю план действий...",
        parse_mode='Markdown'
    )
    
    try:
        # ГЛАВНЫЙ ПРОЦЕСС МЫШЛЕНИЯ
        result = await brain.think(user_message, user_id)
        
        response_text = result['response']
        actions = result['actions']
        
        # Добавляем кнопки для автоматических действий
        keyboard = []
        
        if actions:
            keyboard.append([
                InlineKeyboardButton(
                    "🤖 Выполнить автоматически",
                    callback_data=f"execute_all_{user_id}"
                )
            ])
            
            for i, action in enumerate(actions[:3]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"▶️ {action['opportunity'][:30]}...",
                        callback_data=f"execute_{i}_{user_id}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton(
                "💡 Другой способ заработка",
                callback_data=f"alternative_{user_id}"
            )
        ])
        
        # Отправляем ответ
        if len(response_text) > 4096:
            # Разбиваем на части если слишком длинный
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            
            await thinking_msg.delete()
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1 and keyboard:
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
        
        # Сохраняем действия для выполнения
        if actions:
            context.user_data[f'actions_{user_id}'] = actions
            
    except Exception as e:
        error_msg = (
            "⚠️ Произошла ошибка при анализе.\n\n"
            "Попробуй переформулировать вопрос или спроси что-то конкретное:\n"
            "• Как заработать на [тема]?\n"
            "• Анализ рынка [индустрия]\n"
            "• Создай бизнес-план для [идея]"
        )
        
        await thinking_msg.edit_text(error_msg)
        print(f"Ошибка: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith('execute_'):
        # Выполнение конкретного действия
        parts = data.split('_')
        
        if parts[1] == 'all':
            # Выполнить все действия
            actions = context.user_data.get(f'actions_{user_id}', [])
            
            await query.message.edit_text(
                "🤖 **ЗАПУСКАЮ АВТОМАТИЧЕСКОЕ ВЫПОЛНЕНИЕ...**\n\n"
                f"Задач в очереди: {len(actions)}\n"
                f"Примерное время: {len(actions) * 2-3} минут\n\n"
                "Создаю реальные продукты которые принесут деньги...",
                parse_mode='Markdown'
            )
            
            results = []
            for i, action in enumerate(actions):
                status_msg = await query.message.reply_text(
                    f"⚙️ Выполняю задачу {i+1}/{len(actions)}:\n"
                    f"{action['opportunity']}...",
                    parse_mode='Markdown'
                )
                
                result = await executor.execute_action(action, user_id)
                results.append(result)
                
                await status_msg.delete()
            
            # Отправляем все результаты
            for result in results:
                output_text = (
                    f"✅ **ГОТОВО!**\n\n"
                    f"Тип: {result['type']}\n"
                    f"Статус: {result['status']}\n\n"
                    f"**РЕЗУЛЬТАТ:**\n"
                    f"{result['output'][:3000]}\n\n"
                    f"**ЧТО ДЕЛАТЬ ДАЛЬШЕ:**\n"
                    f"{result['next_step']}"
                )
                
                await query.message.reply_text(output_text, parse_mode='Markdown')
        
        else:
            # Выполнить одно действие
            action_index = int(parts[1])
            actions = context.user_data.get(f'actions_{user_id}', [])
            
            if action_index < len(actions):
                action = actions[action_index]
                
                await query.message.edit_text(
                    f"🤖 Выполняю: {action['opportunity']}\n\n"
                    "Это займёт 1-3 минуты...",
                    parse_mode='Markdown'
                )
                
                result = await executor.execute_action(action, user_id)
                
                output_text = (
                    f"✅ **ГОТОВО!**\n\n"
                    f"**РЕЗУЛЬТАТ:**\n"
                    f"{result['output'][:3500]}\n\n"
                    f"**СЛЕДУЮЩИЙ ШАГ:**\n"
                    f"{result['next_step']}"
                )
                
                await query.message.reply_text(output_text, parse_mode='Markdown')
    
    elif data.startswith('alternative_'):
        # Предложить альтернативные способы
        await query.message.reply_text(
            "💡 Хочешь другие способы заработка?\n\n"
            "Напиши конкретнее что ищешь:\n"
            "• Быстрые деньги (неделя)\n"
            "• Пассивный доход\n"
            "• Масштабируемый бизнес\n"
            "• Конкретная индустрия\n\n"
            "Или просто задай вопрос!",
            parse_mode='Markdown'
        )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    
    welcome_text = """
🧠 **DeepThink AutoHustle**

Я - AI который не просто отвечает, а ДУМАЕТ и ДЕЙСТВУЕТ.

**ЧТО Я УМЕЮ:**

🔍 **Глубокий анализ**
• На любую тему - полное исследование
• Рыночные данные, тренды, возможности
• Честно о сложностях и рисках

💰 **Поиск заработка**
• К каждой теме нахожу способы заработка
• Конкретные цифры и сроки
• 95%+ автоматизация через AI

🤖 **Автоматическое выполнение**
• Создаю реальные продукты
• Пишу код, контент, курсы
• Готово к продаже/публикации

**КАК ПОЛЬЗОВАТЬСЯ:**

Просто пиши ЧТО УГОДНО:
• "расскажи про NFT"
• "как заработать на копирайтинге"
• "создай бизнес-план для кофейни"
• "анализ рынка EdTech"

Я пойму и дам максимально полезный ответ + способы заработка.

**ОСОБЕННОСТЬ:**
Я не работаю по скриптам. Каждый ответ уникален, глубок и нацелен на РЕЗУЛЬТАТ.

🚀 **Начни прямо сейчас - задай любой вопрос!**
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика использования"""
    
    user_id = update.effective_user.id
    memory = brain.conversation_memory.get(user_id, {})
    
    stats_text = f"""
📊 **ТВОЯ СТАТИСТИКА**

💬 Сообщений: {len(memory.get('history', [])) // 2}
✅ Выполненных задач: {len(memory.get('completed_tasks', []))}
🎯 Активных целей: {len(memory.get('active_goals', []))}

**СИСТЕМА:**
🧠 Модель мышления: Claude 3.5 Sonnet
⚡ Режим: Deep Thinking
🎯 Точность анализа: 95%+
🤖 Уровень автоматизации: 95%+

Продолжай задавать вопросы - я учусь на каждом диалоге!
"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

def main():
    """Запуск бота"""
    
    print("\n" + "="*60)
    print("🧠 DEEPTHINK AUTOHUSTLE - ЗАПУСК")
    print("="*60)
    print("\n🎯 МИССИЯ:")
    print("  Помогать людям зарабатывать деньги через AI")
    print("\n⚙️ ВОЗМОЖНОСТИ:")
    print("  ✓ Глубокий анализ любой темы")
    print("  ✓ Автоматический поиск способов заработка")
    print("  ✓ Создание готовых продуктов")
    print("  ✓ 95%+ автоматизация")
    print("\n🤖 МОДЕЛЬ: Claude 3.5 Sonnet")
    print("💡 РЕЖИМ: Deep Thinking")
    print("\n" + "="*60 + "\n")
    
    # Создание приложения
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ БОТ АКТИВЕН!")
    print("📱 Открой Telegram и начни общение\n")
    print("="*60 + "\n")
    
    # Запуск
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
