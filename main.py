"""
╔══════════════════════════════════════════════════════════════════════════╗
║         DEEPTHINK AUTOHUSTLE v3.0 - ULTIMATE MONEY EDITION               ║
║                                                                          ║
║  🚀 Готов к деплою на Render.com                                         ║
║  🤖 20 AI-агентов для заработка                                          ║
║  💰 База знаний о монетизации                                            ║
║  ⚡ Оптимизирован для бесплатных API                                     ║
║                                                                          ║
║  Python 3.8+ Compatible | Render.com Ready                               ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import re
import sys
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK HTTP SERVER (для Render.com)
# ═══════════════════════════════════════════════════════════════════════════

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Простой HTTP handler для health check"""
    
    def do_GET(self):
        """Ответ на GET запросы"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "service": "DeepThink AutoHustle v3.0",
            "timestamp": datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_HEAD(self):
        """Ответ на HEAD запросы"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Отключаем логирование HTTP запросов"""
        pass

def start_health_server():
    """Запуск HTTP сервера для health check в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 Health check server запущен на порту {port}")
    server.serve_forever()

# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # API ключи (можно переопределить через environment variables)
    TELEGRAM_TOKEN: str = field(default_factory=lambda: os.environ.get(
        'TELEGRAM_TOKEN', 
        '8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY'
    ))
    
    OPENROUTER_KEY: str = field(default_factory=lambda: os.environ.get(
        'OPENROUTER_KEY',
        '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'
    ))
    
    # БЕСПЛАТНЫЕ МОДЕЛИ - приоритет
    FREE_MODELS: List[str] = field(default_factory=lambda: [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
    ])
    
    DEFAULT_MODEL: str = "google/gemini-2.0-flash-exp:free"
    
    # ЛИМИТЫ ТОКЕНОВ - оптимизированы для бесплатного плана
    MAX_TOKENS_RESPONSE: int = 800
    MAX_TOKENS_SHORT: int = 400
    MAX_TOKENS_ACTION: int = 1000
    
    TEMPERATURE: float = 0.7
    
    # Лимиты
    MAX_AGENTS: int = 3
    MAX_CONTEXT: int = 1500
    MAX_HISTORY: int = 10
    MAX_ACTIONS: int = 5
    
    # Таймауты
    API_TIMEOUT: int = 60
    POLLING_TIMEOUT: int = 30
    
    @property
    def TELEGRAM_API(self) -> str:
        return f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}"

config = Config()

# ═══════════════════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════

def log(message: str, level: str = "INFO"):
    """Простое логирование"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════
# ИМПОРТЫ (после конфигурации)
# ═══════════════════════════════════════════════════════════════════════════

log("🚀 Запуск DeepThink AutoHustle v3.0...")

try:
    import httpx
    log("✅ httpx загружен")
except ImportError as e:
    log(f"❌ Ошибка импорта httpx: {e}", "ERROR")
    sys.exit(1)

try:
    from openai import OpenAI
    log("✅ openai загружен")
except ImportError as e:
    log(f"❌ Ошибка импорта openai: {e}", "ERROR")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# AI КЛИЕНТ
# ═══════════════════════════════════════════════════════════════════════════

class AIClient:
    """AI клиент с поддержкой бесплатных моделей и fallback"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_KEY
        )
        self.model_index = 0
        self.requests = 0
        self.errors = 0
        log("✅ AI клиент инициализирован")
    
    def _get_model(self) -> str:
        """Получить текущую модель"""
        models = config.FREE_MODELS
        return models[self.model_index % len(models)]
    
    def _next_model(self):
        """Переключиться на следующую модель"""
        self.model_index += 1
        log(f"🔄 Переключение на модель: {self._get_model()}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        system: str = None
    ) -> Tuple[str, bool]:
        """Генерация ответа с автоматическим fallback"""
        
        max_tokens = min(max_tokens or config.MAX_TOKENS_RESPONSE, 1000)
        temperature = temperature or config.TEMPERATURE
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system[:500]})
        messages.append({"role": "user", "content": prompt[:config.MAX_CONTEXT]})
        
        # Пробуем несколько моделей
        for attempt in range(len(config.FREE_MODELS)):
            model = self._get_model()
            
            try:
                self.requests += 1
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                result = response.choices[0].message.content
                log(f"✅ Ответ от {model.split('/')[-1][:20]}")
                return result, True
                
            except Exception as e:
                error_msg = str(e)
                log(f"⚠️ Ошибка {model.split('/')[-1][:15]}: {error_msg[:50]}", "WARN")
                
                # Если ошибка с кредитами или лимитами - меняем модель
                if any(x in error_msg.lower() for x in ['402', 'credit', 'limit', 'quota']):
                    self._next_model()
                    continue
                
                self.errors += 1
                self._next_model()
        
        return "⚠️ Временные проблемы с AI. Попробуйте позже.", False
    
    async def generate_short(self, prompt: str) -> Tuple[str, bool]:
        """Короткий ответ"""
        return await self.generate(prompt, max_tokens=config.MAX_TOKENS_SHORT)

ai = AIClient()

# ═══════════════════════════════════════════════════════════════════════════
# БАЗА ЗНАНИЙ О ЗАРАБОТКЕ
# ═══════════════════════════════════════════════════════════════════════════

class MoneyKnowledge:
    """База знаний о способах заработка"""
    
    BUSINESS_MODELS = {
        "freelance": {
            "name": "🎨 Фриланс",
            "income": "$500 - $10,000/мес",
            "time": "1-4 недели",
            "ai_help": "60%",
            "platforms": ["Upwork", "Fiverr", "Kwork", "FL.ru"],
            "steps": [
                "Выбрать навык (копирайтинг, дизайн, код)",
                "Создать портфолио с помощью AI",
                "Зарегистрироваться на 3-5 платформах",
                "Отправлять 10-20 откликов в день",
                "Собирать отзывы, повышать цены"
            ]
        },
        "affiliate": {
            "name": "🔗 Партнёрский маркетинг",
            "income": "$200 - $50,000/мес",
            "time": "1-3 месяца",
            "ai_help": "80%",
            "platforms": ["Amazon", "Admitad", "CJ", "партнёрки инфопродуктов"],
            "steps": [
                "Выбрать нишу с высокими комиссиями",
                "Создать Telegram канал или блог",
                "Генерировать контент с AI",
                "Вставлять партнёрские ссылки",
                "Масштабировать трафик"
            ]
        },
        "digital": {
            "name": "📱 Цифровые продукты",
            "income": "$100 - $100,000/мес",
            "time": "2-8 недель",
            "ai_help": "90%",
            "platforms": ["Gumroad", "Notion", "Boosty", "GetCourse"],
            "steps": [
                "Найти боль аудитории",
                "Создать продукт с AI (курс, гайд, шаблон)",
                "Настроить продажу",
                "Запустить трафик",
                "Собирать отзывы и улучшать"
            ]
        },
        "ai_services": {
            "name": "🤖 AI-сервисы",
            "income": "$1,000 - $50,000/мес",
            "time": "1-4 недели",
            "ai_help": "95%",
            "platforms": ["Telegram боты", "Собственный сайт", "Fiverr"],
            "steps": [
                "Выбрать услугу (тексты, картинки, код)",
                "Создать бота или лендинг",
                "Настроить автоматизацию",
                "Привлечь первых клиентов",
                "Масштабировать"
            ]
        },
        "content": {
            "name": "📝 Контент-бизнес",
            "income": "$100 - $100,000/мес",
            "time": "3-12 месяцев",
            "ai_help": "70%",
            "platforms": ["YouTube", "Telegram", "TikTok", "Дзен"],
            "steps": [
                "Выбрать нишу и формат",
                "Создать контент-план",
                "Публиковать регулярно",
                "Монетизировать (реклама, донаты)",
                "Диверсифицировать доходы"
            ]
        },
        "automation": {
            "name": "⚙️ Автоматизация",
            "income": "$2,000 - $30,000/мес",
            "time": "2-4 недели",
            "ai_help": "70%",
            "platforms": ["Make", "Zapier", "n8n", "Telegram"],
            "steps": [
                "Изучить no-code инструменты",
                "Найти бизнесы с рутинными процессами",
                "Предложить автоматизацию",
                "Создать решение",
                "Брать абонентскую плату"
            ]
        },
        "bots": {
            "name": "🤖 Telegram-боты",
            "income": "$500 - $20,000/мес",
            "time": "1-2 недели",
            "ai_help": "80%",
            "platforms": ["Telegram", "Python/aiogram"],
            "steps": [
                "Изучить aiogram (с помощью AI)",
                "Найти идею бота",
                "Разработать MVP",
                "Найти клиентов",
                "Масштабировать"
            ]
        },
        "dropshipping": {
            "name": "📦 Дропшиппинг",
            "income": "$500 - $30,000/мес",
            "time": "2-6 недель",
            "ai_help": "50%",
            "platforms": ["Wildberries", "Ozon", "Shopify"],
            "steps": [
                "Найти winning product",
                "Найти поставщика",
                "Создать магазин/карточку",
                "Настроить рекламу",
                "Масштабировать"
            ]
        }
    }
    
    QUICK_WINS = [
        {"name": "AI-копирайтинг на Kwork", "income": "$300-1000/мес", "time": "3-7 дней"},
        {"name": "Telegram-бот на заказ", "income": "$500-3000/проект", "time": "1-2 недели"},
        {"name": "Notion-шаблоны", "income": "$100-5000/мес", "time": "1 неделя"},
        {"name": "AI-дизайн (Midjourney)", "income": "$500-2000/мес", "time": "1 неделя"},
        {"name": "AI-консультации", "income": "$1000-5000/мес", "time": "Сразу"},
    ]
    
    HOT_NICHES = [
        {"niche": "AI-инструменты для бизнеса", "trend": "🔥🔥🔥"},
        {"niche": "Автоматизация с n8n/Make", "trend": "🔥🔥🔥"},
        {"niche": "Микро-SaaS", "trend": "🔥🔥🔥"},
        {"niche": "Telegram-боты", "trend": "🔥🔥"},
        {"niche": "No-code разработка", "trend": "🔥🔥"},
        {"niche": "AI-контент", "trend": "🔥🔥"},
        {"niche": "Образовательные продукты", "trend": "🔥🔥"},
    ]
    
    @classmethod
    def get_model_info(cls, key: str) -> str:
        """Получить информацию о бизнес-модели"""
        data = cls.BUSINESS_MODELS.get(key)
        if not data:
            return "Модель не найдена"
        
        steps = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(data['steps'])])
        platforms = ", ".join(data['platforms'])
        
        return f"""{data['name']}

💵 Доход: {data['income']}
⏱ До результата: {data['time']}
🤖 AI помогает: {data['ai_help']}

📋 *Шаги:*
{steps}

🌐 *Платформы:* {platforms}"""
    
    @classmethod
    def get_all_models_short(cls) -> str:
        """Краткий список всех моделей"""
        text = "💰 *СПОСОБЫ ЗАРАБОТКА:*\n\n"
        for key, data in cls.BUSINESS_MODELS.items():
            text += f"{data['name']}\n"
            text += f"  💵 {data['income']} | ⏱ {data['time']}\n\n"
        return text
    
    @classmethod
    def get_quick_wins(cls) -> str:
        """Быстрые победы"""
        text = "⚡ *БЫСТРЫЙ СТАРТ (деньги за неделю):*\n\n"
        for i, qw in enumerate(cls.QUICK_WINS, 1):
            text += f"*{i}. {qw['name']}*\n"
            text += f"   💰 {qw['income']} | ⏱ {qw['time']}\n\n"
        return text
    
    @classmethod
    def get_niches(cls) -> str:
        """Горячие ниши"""
        text = "🔥 *ГОРЯЧИЕ НИШИ 2024-2025:*\n\n"
        for n in cls.HOT_NICHES:
            text += f"• {n['niche']} {n['trend']}\n"
        return text

# ═══════════════════════════════════════════════════════════════════════════
# СИСТЕМА АГЕНТОВ
# ═══════════════════════════════════════════════════════════════════════════

class Agent:
    """AI Агент"""
    
    def __init__(self, name: str, emoji: str, specialty: str, keywords: List[str]):
        self.name = name
        self.emoji = emoji
        self.specialty = specialty
        self.keywords = keywords
        self.calls = 0
    
    @property
    def display(self) -> str:
        return f"{self.emoji} {self.name}"
    
    def relevance(self, query: str) -> float:
        """Оценка релевантности для запроса"""
        q = query.lower()
        matches = sum(1 for kw in self.keywords if kw in q)
        return min(matches / max(len(self.keywords) * 0.3, 1), 1.0)
    
    async def think(self, task: str, context: str = "") -> Tuple[str, bool]:
        """Анализ задачи"""
        self.calls += 1
        
        system = f"Ты {self.name} - {self.specialty}. Отвечай кратко, конкретно, с цифрами."
        
        prompt = f"""Задача: {task}
{f'Контекст: {context[:300]}' if context else ''}

Дай ответ с:
- Конкретными цифрами
- Способами заработка
- Первым шагом"""
        
        return await ai.generate(prompt, system=system)

class Swarm:
    """Рой агентов"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._init()
    
    def _init(self):
        """Инициализация агентов"""
        agents_data = [
            ("researcher", "Исследователь", "🔬", "анализ рынков и трендов",
             ["анализ", "исследование", "тренд", "рынок", "статистика"]),
            
            ("money", "Эксперт заработка", "💰", "монетизация и доход",
             ["заработок", "деньги", "доход", "монетизация", "прибыль"]),
            
            ("strategist", "Стратег", "🏗️", "стратегии и планирование",
             ["план", "стратегия", "roadmap", "масштаб", "этап"]),
            
            ("content", "Контент-мейкер", "✍️", "создание контента",
             ["контент", "текст", "пост", "статья", "копирайт"]),
            
            ("coder", "Кодер", "💻", "программирование и боты",
             ["код", "программа", "бот", "скрипт", "python", "автоматизация"]),
            
            ("marketer", "Маркетолог", "📢", "маркетинг и продвижение",
             ["маркетинг", "реклама", "продвижение", "таргет", "трафик"]),
            
            ("freelancer", "Фрилансер", "🎯", "фриланс и услуги",
             ["фриланс", "заказ", "клиент", "услуга", "kwork", "fiverr"]),
            
            ("affiliate", "Партнёрщик", "🔗", "партнёрский маркетинг",
             ["партнёрка", "affiliate", "реферал", "комиссия"]),
            
            ("automation", "Автоматизатор", "⚙️", "автоматизация процессов",
             ["автоматизация", "интеграция", "zapier", "make", "n8n"]),
            
            ("coach", "Коуч", "🎯", "мотивация и развитие",
             ["мотивация", "цель", "рост", "привычка", "продуктивность"]),
        ]
        
        for key, name, emoji, specialty, keywords in agents_data:
            self.agents[key] = Agent(name, emoji, specialty, keywords)
        
        log(f"✅ Загружено {len(self.agents)} агентов")
    
    def select(self, query: str, max_agents: int = None) -> List[Agent]:
        """Выбор релевантных агентов"""
        max_agents = max_agents or config.MAX_AGENTS
        
        # Оценка каждого агента
        scored = [(a, a.relevance(query)) for a in self.agents.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Обязательно включаем money и researcher
        must_have = ["money", "researcher"]
        selected = [self.agents[k] for k in must_have if k in self.agents]
        
        # Добавляем релевантных
        for agent, score in scored:
            if len(selected) >= max_agents:
                break
            if agent not in selected and score > 0.1:
                selected.append(agent)
        
        return selected[:max_agents]
    
    async def think(self, query: str, context: str = "") -> List[Tuple[str, str, bool]]:
        """Коллективное мышление"""
        agents = self.select(query)
        
        results = []
        for agent in agents:
            response, success = await agent.think(query, context)
            results.append((agent.display, response, success))
        
        return results

swarm = Swarm()

# ═══════════════════════════════════════════════════════════════════════════
# СИНТЕЗАТОР
# ═══════════════════════════════════════════════════════════════════════════

async def synthesize(query: str, responses: List[Tuple[str, str, bool]]) -> str:
    """Синтез ответов агентов"""
    
    valid = [(name, text) for name, text, ok in responses if ok]
    
    if not valid:
        return "⚠️ Не удалось получить ответы. Попробуйте переформулировать вопрос."
    
    agents_text = "\n\n".join([f"[{name}]: {text[:350]}" for name, text in valid])
    
    prompt = f"""Объедини ответы экспертов в полезный ответ.

ВОПРОС: {query}

ЭКСПЕРТЫ:
{agents_text}

ФОРМАТ:

🧠 *СУТЬ* (2-3 предложения)

💰 *КАК ЗАРАБОТАТЬ:*

*1. [Способ]* - $X/мес
• Что делать
• AI помогает: X%
• Шаги: 1, 2, 3

*2. [Способ]* - $X/мес
[аналогично]

🎯 *НАЧНИ СЕЙЧАС:* [конкретное действие]

Кратко!"""
    
    result, success = await ai.generate(prompt)
    
    if not success:
        # Fallback
        return "\n\n---\n\n".join([f"{name}:\n{text[:400]}" for name, text in valid])
    
    return result

# ═══════════════════════════════════════════════════════════════════════════
# ГЕНЕРАТОР ДЕЙСТВИЙ
# ═══════════════════════════════════════════════════════════════════════════

def generate_actions(query: str) -> List[Dict]:
    """Генерация действий на основе запроса"""
    actions = []
    q = query.lower()
    
    if any(w in q for w in ["контент", "текст", "пост"]):
        actions.append({
            "type": "content",
            "name": "✍️ Создать контент",
            "desc": f"Контент по теме: {query[:40]}"
        })
    
    if any(w in q for w in ["код", "бот", "скрипт", "программ"]):
        actions.append({
            "type": "code",
            "name": "💻 Написать код",
            "desc": f"Код: {query[:40]}"
        })
    
    if any(w in q for w in ["план", "стратегия", "как начать"]):
        actions.append({
            "type": "plan",
            "name": "📋 Пошаговый план",
            "desc": f"План: {query[:40]}"
        })
    
    if any(w in q for w in ["идея", "ниша", "что делать"]):
        actions.append({
            "type": "ideas",
            "name": "💡 10 идей",
            "desc": f"Идеи: {query[:40]}"
        })
    
    if any(w in q for w in ["заработ", "доход", "деньги"]):
        actions.append({
            "type": "calc",
            "name": "🧮 Расчёт дохода",
            "desc": "Калькулятор потенциального дохода"
        })
    
    # Дефолтные
    if not actions:
        actions = [
            {"type": "plan", "name": "📋 План действий", "desc": f"План: {query[:40]}"},
            {"type": "ideas", "name": "💡 Идеи", "desc": "Генерация идей"}
        ]
    
    return actions[:config.MAX_ACTIONS]

async def execute_action(action: Dict, context: str) -> str:
    """Выполнение действия"""
    
    action_type = action.get("type", "plan")
    desc = action.get("desc", "")
    
    prompts = {
        "content": f"Создай готовый контент для публикации: {desc}\n\nВключи заголовок, текст 300-500 слов, призыв к действию, хештеги.",
        
        "code": f"Напиши рабочий Python код: {desc}\n\nТребования: рабочий код, комментарии, обработка ошибок.",
        
        "plan": f"Создай пошаговый план: {desc}\n\nФормат:\n📅 ДЕНЬ 1-7: шаги\n📅 НЕДЕЛЯ 2-4: шаги\n💰 Ожидаемый доход",
        
        "ideas": f"Сгенерируй 10 идей: {desc}\n\nДля каждой: название, потенциал $X/мес, первый шаг",
        
        "calc": f"Рассчитай потенциальный доход: {desc}\n\nБазовый сценарий, оптимистичный, консервативный"
    }
    
    prompt = prompts.get(action_type, prompts["plan"])
    prompt += f"\n\nКонтекст: {context[:400]}"
    
    result, _ = await ai.generate(prompt, max_tokens=config.MAX_TOKENS_ACTION)
    return result

# ═══════════════════════════════════════════════════════════════════════════
# МОЗГ
# ═══════════════════════════════════════════════════════════════════════════

class Brain:
    """Главный мозг системы"""
    
    def __init__(self):
        self.queries = 0
        self.tasks = 0
    
    async def think(self, query: str, context: str = "") -> Dict:
        """Глубокий анализ"""
        
        import time
        start = time.time()
        
        self.queries += 1
        
        # Коллективное мышление
        responses = await swarm.think(query, context)
        
        # Синтез
        synthesis = await synthesize(query, responses)
        
        # Действия
        actions = generate_actions(query)
        
        # Агенты которые работали
        agents_used = [name for name, _, ok in responses if ok]
        
        return {
            "response": synthesis,
            "agents": agents_used,
            "actions": actions,
            "time": time.time() - start
        }

brain = Brain()

# ═══════════════════════════════════════════════════════════════════════════
# ХРАНИЛИЩЕ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════

class Storage:
    """Хранилище данных пользователей"""
    
    def __init__(self):
        self.contexts: Dict[int, Dict] = {}
        self.pending_actions: Dict[str, Dict] = {}
    
    def get_context(self, user_id: int) -> Dict:
        if user_id not in self.contexts:
            self.contexts[user_id] = {
                "messages": [],
                "last_query": "",
                "last_response": "",
                "queries": 0
            }
        return self.contexts[user_id]
    
    def add_message(self, user_id: int, role: str, content: str):
        ctx = self.get_context(user_id)
        ctx["messages"].append({"role": role, "content": content[:300]})
        if len(ctx["messages"]) > config.MAX_HISTORY:
            ctx["messages"] = ctx["messages"][-config.MAX_HISTORY:]
    
    def get_summary(self, user_id: int) -> str:
        ctx = self.get_context(user_id)
        if not ctx["messages"]:
            return ""
        recent = ctx["messages"][-3:]
        return "\n".join([f"{m['role']}: {m['content'][:100]}" for m in recent])

storage = Storage()

# ═══════════════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════════════════

class Stats:
    """Статистика"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.queries = 0
        self.tasks = 0
        self.errors = 0
    
    def get_summary(self) -> str:
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        return f"""📊 *СТАТИСТИКА*

⏱ Время работы: {hours:.1f}ч
💬 Запросов: {self.queries}
✅ Задач: {self.tasks}
❌ Ошибок: {self.errors}
🤖 Агентов: {len(swarm.agents)}
🔧 Модель: {ai._get_model().split('/')[-1][:25]}
📡 AI запросов: {ai.requests}"""

stats = Stats()

# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════

class Bot:
    """Telegram бот"""
    
    def __init__(self):
        self.api = config.TELEGRAM_API
    
    async def send(self, chat_id: int, text: str, buttons: Dict = None):
        """Отправка сообщения"""
        async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
            data = {"chat_id": chat_id, "text": text[:4096]}
            
            if buttons:
                data["reply_markup"] = json.dumps(buttons)
            
            # Пробуем с Markdown
            data["parse_mode"] = "Markdown"
            
            try:
                resp = await client.post(f"{self.api}/sendMessage", json=data)
                if resp.status_code == 200:
                    return
            except:
                pass
            
            # Без форматирования
            data.pop("parse_mode", None)
            try:
                await client.post(f"{self.api}/sendMessage", json=data)
            except Exception as e:
                log(f"Send error: {e}", "ERROR")
    
    async def answer_callback(self, callback_id: str):
        """Ответ на callback"""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    f"{self.api}/answerCallbackQuery",
                    json={"callback_query_id": callback_id}
                )
            except:
                pass
    
    async def typing(self, chat_id: int):
        """Статус печатает"""
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(
                    f"{self.api}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"}
                )
            except:
                pass
    
    def make_buttons(self, actions: List[Dict], user_id: int) -> Dict:
        """Создание кнопок"""
        keyboard = []
        
        for i, action in enumerate(actions[:4]):
            keyboard.append([{
                "text": action.get("name", "🤖 Действие")[:28],
                "callback_data": f"act_{i}_{user_id}"
            }])
        
        keyboard.append([
            {"text": "💰 Способы заработка", "callback_data": f"income_{user_id}"},
            {"text": "🔥 Ниши", "callback_data": f"niches_{user_id}"}
        ])
        
        keyboard.append([
            {"text": "⚡ Быстрый старт", "callback_data": f"quick_{user_id}"},
            {"text": "📊 Статистика", "callback_data": f"stats_{user_id}"}
        ])
        
        return {"inline_keyboard": keyboard}
    
    # ═══════════════════════════════════════════════════════════════
    # КОМАНДЫ
    # ═══════════════════════════════════════════════════════════════
    
    async def cmd_start(self, chat_id: int, user_name: str):
        """Команда /start"""
        text = f"""🧠 *DEEPTHINK AUTOHUSTLE v3.0*

Привет, {user_name}! 👋

Я - AI-система для поиска способов заработка.

🤖 *{len(swarm.agents)} АГЕНТОВ* анализируют твои запросы

💰 *Я ПОМОГУ:*
• Найти способ заработка под тебя
• Создать план действий
• Написать код или контент
• Рассчитать потенциальный доход

🚀 *ПРИМЕРЫ:*
• "Как заработать на AI?"
• "Создай Telegram-бота"
• "Топ ниши 2025"
• "План на $1000/мес"

📖 /help - все команды

💡 Просто напиши свой вопрос!"""
        
        await self.send(chat_id, text)
    
    async def cmd_help(self, chat_id: int):
        """Команда /help"""
        text = """📖 *КОМАНДЫ:*

*Основные:*
/start - Начало
/help - Справка

*Заработок:*
/income - Способы заработка
/niches - Горячие ниши
/quick - Быстрый старт

*Система:*
/stats - Статистика
/agents - Агенты

💡 Или просто напиши вопрос!"""
        
        await self.send(chat_id, text)
    
    async def cmd_income(self, chat_id: int):
        """Способы заработка"""
        text = MoneyKnowledge.get_all_models_short()
        
        buttons = {"inline_keyboard": [
            [{"text": "🎨 Фриланс", "callback_data": "bm_freelance"}],
            [{"text": "🔗 Партнёрки", "callback_data": "bm_affiliate"}],
            [{"text": "📱 Цифровые продукты", "callback_data": "bm_digital"}],
            [{"text": "🤖 AI-сервисы", "callback_data": "bm_ai_services"}],
            [{"text": "📝 Контент", "callback_data": "bm_content"}],
            [{"text": "⚙️ Автоматизация", "callback_data": "bm_automation"}],
            [{"text": "🤖 Telegram-боты", "callback_data": "bm_bots"}],
        ]}
        
        await self.send(chat_id, text, buttons)
    
    async def cmd_niches(self, chat_id: int):
        await self.send(chat_id, MoneyKnowledge.get_niches())
    
    async def cmd_quick(self, chat_id: int):
        await self.send(chat_id, MoneyKnowledge.get_quick_wins())
    
    async def cmd_stats(self, chat_id: int):
        await self.send(chat_id, stats.get_summary())
    
    async def cmd_agents(self, chat_id: int):
        text = f"🤖 *{len(swarm.agents)} АГЕНТОВ:*\n\n"
        for agent in swarm.agents.values():
            text += f"{agent.display} - {agent.specialty}\n"
            text += f"  📊 Вызовов: {agent.calls}\n\n"
        await self.send(chat_id, text)
    
    # ═══════════════════════════════════════════════════════════════
    # ОБРАБОТКА СООБЩЕНИЙ
    # ═══════════════════════════════════════════════════════════════
    
    async def handle_message(self, chat_id: int, user_id: int, text: str):
        """Обработка сообщения"""
        
        stats.queries += 1
        
        ctx = storage.get_context(user_id)
        ctx["queries"] += 1
        ctx["last_query"] = text
        storage.add_message(user_id, "user", text)
        
        await self.typing(chat_id)
        
        await self.send(chat_id,
            "🧠 *DEEP THINKING...*\n\n"
            f"🤖 Агенты анализируют...\n"
            "💰 Ищу способы заработка..."
        )
        
        try:
            # Думаем
            result = await brain.think(text, storage.get_summary(user_id))
            
            response = result["response"]
            agents = result["agents"]
            actions = result["actions"]
            think_time = result["time"]
            
            # Сохраняем
            ctx["last_response"] = response
            storage.add_message(user_id, "assistant", response[:300])
            
            # Сохраняем действия
            for i, action in enumerate(actions):
                storage.pending_actions[f"act_{i}_{user_id}"] = {
                    "action": action,
                    "context": text,
                    "response": response[:500]
                }
            
            # Footer
            agents_str = ", ".join(agents[:3])
            footer = f"\n\n---\n👥 _{agents_str}_\n⏱ _{think_time:.1f}с_"
            
            full = response + footer
            buttons = self.make_buttons(actions, user_id)
            
            await self.send(chat_id, full[:4096], buttons)
            
        except Exception as e:
            stats.errors += 1
            log(f"Error: {e}", "ERROR")
            await self.send(chat_id, f"⚠️ Ошибка: {str(e)[:150]}\n\nПопробуй переформулировать.")
    
    async def handle_callback(self, callback_id: str, chat_id: int, user_id: int, data: str):
        """Обработка callback"""
        
        await self.answer_callback(callback_id)
        
        # Команды
        if data.startswith("stats_"):
            await self.cmd_stats(chat_id)
            return
        
        if data.startswith("income_"):
            await self.cmd_income(chat_id)
            return
        
        if data.startswith("niches_"):
            await self.cmd_niches(chat_id)
            return
        
        if data.startswith("quick_"):
            await self.cmd_quick(chat_id)
            return
        
        # Бизнес-модели
        if data.startswith("bm_"):
            key = data[3:]  # Убираем "bm_"
            info = MoneyKnowledge.get_model_info(key)
            await self.send(chat_id, info)
            return
        
        # Действия
        if data.startswith("act_"):
            key = data
            if key in storage.pending_actions:
                action_data = storage.pending_actions[key]
                action = action_data["action"]
                context = f"{action_data['context']}\n{action_data['response']}"
                
                await self.typing(chat_id)
                await self.send(chat_id, f"⚙️ Выполняю: {action.get('name', '')}...")
                
                try:
                    result = await execute_action(action, context)
                    stats.tasks += 1
                    
                    # Разбиваем длинный ответ
                    if len(result) > 4000:
                        parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
                        for i, part in enumerate(parts):
                            header = f"📄 *Часть {i+1}/{len(parts)}*\n\n" if len(parts) > 1 else ""
                            await self.send(chat_id, header + part)
                    else:
                        await self.send(chat_id, f"✅ *Готово!*\n\n{result}")
                
                except Exception as e:
                    await self.send(chat_id, f"⚠️ Ошибка: {str(e)[:150]}")
            else:
                await self.send(chat_id, "⚠️ Действие устарело. Сделай новый запрос.")
    
    async def handle_update(self, update: Dict):
        """Обработка обновления"""
        try:
            # Сообщения
            if "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user = msg.get("from", {})
                user_id = user.get("id", 0)
                user_name = user.get("first_name", "User")
                text = msg["text"]
                
                # Команды
                if text == "/start":
                    await self.cmd_start(chat_id, user_name)
                elif text == "/help":
                    await self.cmd_help(chat_id)
                elif text == "/income":
                    await self.cmd_income(chat_id)
                elif text == "/niches":
                    await self.cmd_niches(chat_id)
                elif text == "/quick":
                    await self.cmd_quick(chat_id)
                elif text == "/stats":
                    await self.cmd_stats(chat_id)
                elif text == "/agents":
                    await self.cmd_agents(chat_id)
                elif text.startswith("/"):
                    await self.send(chat_id, "❓ Неизвестная команда. /help")
                else:
                    await self.handle_message(chat_id, user_id, text)
            
            # Callback
            elif "callback_query" in update:
                cb = update["callback_query"]
                await self.handle_callback(
                    cb["id"],
                    cb["message"]["chat"]["id"],
                    cb["from"]["id"],
                    cb["data"]
                )
                
        except Exception as e:
            stats.errors += 1
            log(f"Update error: {e}", "ERROR")
    
    async def run(self):
        """Запуск бота"""
        
        log("=" * 50)
        log("🧠 DEEPTHINK AUTOHUSTLE v3.0")
        log("=" * 50)
        log(f"🤖 Агентов: {len(swarm.agents)}")
        log(f"🔧 Модель: {config.DEFAULT_MODEL}")
        log("=" * 50)
        
        offset = 0
        
        async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
            log("✅ БОТ ЗАПУЩЕН!")
            
            while True:
                try:
                    resp = await client.get(
                        f"{self.api}/getUpdates",
                        params={"offset": offset, "timeout": config.POLLING_TIMEOUT}
                    )
                    
                    data = resp.json()
                    
                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            offset = update["update_id"] + 1
                            asyncio.create_task(self.handle_update(update))
                    
                except httpx.TimeoutException:
                    continue
                except Exception as e:
                    log(f"Polling error: {e}", "ERROR")
                    stats.errors += 1
                    await asyncio.sleep(5)

# ═══════════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """Главная функция"""
    
    print("\n" + "=" * 60)
    print("🧠 DEEPTHINK AUTOHUSTLE v3.0")
    print("💰 ULTIMATE MONEY EDITION")
    print("🚀 Render.com Ready")
    print("=" * 60 + "\n")
    
    bot = Bot()
    await bot.run()

def run():
    """Точка входа"""
    
    # Запускаем HTTP сервер для health check в отдельном потоке
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
