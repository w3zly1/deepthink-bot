"""
╔══════════════════════════════════════════════════════════════════════════╗
║         DEEPTHINK AUTOHUSTLE v3.0 - ULTIMATE MONEY EDITION               ║
║                                                                          ║
║  🧠 20 специализированных AI-агентов                                     ║
║  💰 Система генерации идей для заработка                                 ║
║  📊 Калькулятор потенциального дохода                                    ║
║  🎯 Готовые бизнес-шаблоны                                               ║
║  ⚡ Автоматическая генерация контента                                    ║
║  🔧 Оптимизация под лимиты API                                           ║
║                                                                          ║
║  Python 3.8+ | Render.com Ready | OpenRouter Optimized                   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import logging

# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ - ОПТИМИЗИРОВАННАЯ ДЛЯ ЭКОНОМИИ ТОКЕНОВ
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # API ключи
    TELEGRAM_TOKEN: str = "8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY"
    OPENROUTER_KEY: str = "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"
    
    # Модели - БЕСПЛАТНЫЕ И ЭКОНОМНЫЕ
    FREE_MODELS: List[str] = field(default_factory=lambda: [
        "google/gemini-2.0-flash-exp:free",      # Бесплатная, быстрая
        "meta-llama/llama-3.1-8b-instruct:free", # Бесплатная Llama
        "google/gemma-2-9b-it:free",             # Бесплатная Gemma
        "mistralai/mistral-7b-instruct:free",   # Бесплатная Mistral
    ])
    
    PREMIUM_MODELS: List[str] = field(default_factory=lambda: [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "google/gemini-pro",
    ])
    
    DEFAULT_MODEL: str = "google/gemini-2.0-flash-exp:free"  # Бесплатная по умолчанию
    
    # ОПТИМИЗИРОВАННЫЕ ЛИМИТЫ ТОКЕНОВ
    MAX_TOKENS_FREE: int = 1000      # Для бесплатных запросов
    MAX_TOKENS_STANDARD: int = 800   # Стандартный ответ
    MAX_TOKENS_SHORT: int = 400      # Короткий ответ
    MAX_TOKENS_ACTION: int = 1200    # Для действий
    
    TEMPERATURE: float = 0.7
    
    # Лимиты агентов
    MAX_AGENTS_PER_QUERY: int = 3    # Меньше агентов = меньше токенов
    MAX_CONTEXT_LENGTH: int = 2000
    MAX_HISTORY_ITEMS: int = 10
    MAX_ACTIONS_PER_RESPONSE: int = 5
    
    # Таймауты
    API_TIMEOUT: int = 60
    POLLING_TIMEOUT: int = 30
    
    # Режим экономии
    ECONOMY_MODE: bool = True  # Использовать бесплатные модели
    
    @property
    def TELEGRAM_API(self) -> str:
        return f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}"

config = Config()

# ═══════════════════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('DeepThink')

# ═══════════════════════════════════════════════════════════════════════════
# ПЕРЕЧИСЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════

class AgentType(Enum):
    """Типы агентов - 20 специализаций"""
    # Основные
    RESEARCHER = "researcher"
    MONEY_EXPERT = "money_expert"
    STRATEGIST = "strategist"
    CONTENT_CREATOR = "content_creator"
    CODER = "coder"
    MARKETER = "marketer"
    
    # Специализированные для заработка
    DROPSHIPPER = "dropshipper"
    AFFILIATE = "affiliate"
    FREELANCER = "freelancer"
    CRYPTO_EXPERT = "crypto_expert"
    ECOMMERCE = "ecommerce"
    SAAS_EXPERT = "saas_expert"
    
    # Аналитика и креатив
    DATA_ANALYST = "data_analyst"
    CREATIVE_DIRECTOR = "creative_director"
    COPYWRITER = "copywriter"
    SEO_EXPERT = "seo_expert"
    
    # Специалисты
    INVESTOR = "investor"
    AUTOMATION = "automation"
    COACH = "coach"
    LEGAL = "legal"

class IncomeLevel(Enum):
    """Уровни дохода"""
    STARTER = "starter"       # $100-500/мес
    GROWING = "growing"       # $500-2000/мес
    SERIOUS = "serious"       # $2000-10000/мес
    SCALING = "scaling"       # $10000+/мес

class BusinessModel(Enum):
    """Бизнес-модели"""
    FREELANCE = "freelance"
    AFFILIATE = "affiliate"
    DROPSHIPPING = "dropshipping"
    DIGITAL_PRODUCTS = "digital_products"
    SAAS = "saas"
    CONTENT = "content"
    CONSULTING = "consulting"
    ECOMMERCE = "ecommerce"
    AUTOMATION = "automation"
    AI_SERVICES = "ai_services"

# ═══════════════════════════════════════════════════════════════════════════
# БАЗА ЗНАНИЙ О СПОСОБАХ ЗАРАБОТКА
# ═══════════════════════════════════════════════════════════════════════════

class MoneyKnowledgeBase:
    """База знаний о способах заработка"""
    
    INCOME_STREAMS = {
        BusinessModel.FREELANCE: {
            "name": "🎨 Фриланс",
            "description": "Продажа своих навыков",
            "income_range": "$500 - $10,000/мес",
            "time_to_profit": "1-4 недели",
            "difficulty": "Средняя",
            "ai_automation": "40-60%",
            "skills_needed": ["Копирайтинг", "Дизайн", "Разработка", "Маркетинг"],
            "platforms": ["Upwork", "Fiverr", "Kwork", "FL.ru"],
            "steps": [
                "Выбрать нишу и навык",
                "Создать портфолио (AI поможет)",
                "Зарегистрироваться на платформах",
                "Создать убедительный профиль",
                "Отправлять 10-20 откликов в день"
            ]
        },
        BusinessModel.AFFILIATE: {
            "name": "🔗 Партнёрский маркетинг",
            "description": "Комиссия за продажи по вашим ссылкам",
            "income_range": "$200 - $50,000/мес",
            "time_to_profit": "1-3 месяца",
            "difficulty": "Средняя",
            "ai_automation": "70-80%",
            "skills_needed": ["Контент", "SEO", "Реклама"],
            "platforms": ["Amazon Associates", "Admitad", "CJ Affiliate"],
            "steps": [
                "Выбрать нишу с высокими комиссиями",
                "Создать контент-площадку",
                "Генерировать контент с AI",
                "Привлекать трафик",
                "Оптимизировать конверсию"
            ]
        },
        BusinessModel.DROPSHIPPING: {
            "name": "📦 Дропшиппинг",
            "description": "Продажа без склада",
            "income_range": "$500 - $30,000/мес",
            "time_to_profit": "2-6 недель",
            "difficulty": "Средняя",
            "ai_automation": "50-70%",
            "skills_needed": ["Маркетинг", "Аналитика", "Реклама"],
            "platforms": ["Shopify", "WooCommerce", "Wildberries", "Ozon"],
            "steps": [
                "Найти winning product",
                "Создать магазин",
                "Настроить рекламу",
                "Автоматизировать обработку заказов",
                "Масштабировать"
            ]
        },
        BusinessModel.DIGITAL_PRODUCTS: {
            "name": "📱 Цифровые продукты",
            "description": "Курсы, шаблоны, гайды",
            "income_range": "$100 - $100,000/мес",
            "time_to_profit": "2-8 недель",
            "difficulty": "Низкая-Средняя",
            "ai_automation": "80-90%",
            "skills_needed": ["Экспертиза в нише", "Маркетинг"],
            "platforms": ["Gumroad", "Notion", "Teachable", "GetCourse"],
            "steps": [
                "Определить боль аудитории",
                "Создать продукт с помощью AI",
                "Настроить воронку продаж",
                "Запустить трафик",
                "Собирать отзывы и улучшать"
            ]
        },
        BusinessModel.SAAS: {
            "name": "💻 SaaS / Микро-SaaS",
            "description": "Программное обеспечение как услуга",
            "income_range": "$500 - $500,000/мес",
            "time_to_profit": "1-6 месяцев",
            "difficulty": "Высокая",
            "ai_automation": "30-50%",
            "skills_needed": ["Программирование", "Маркетинг", "UX"],
            "platforms": ["Stripe", "Paddle", "AWS", "Vercel"],
            "steps": [
                "Найти проблему для решения",
                "MVP за 2-4 недели",
                "Получить первых 10 пользователей",
                "Итерировать на основе фидбэка",
                "Масштабировать маркетинг"
            ]
        },
        BusinessModel.CONTENT: {
            "name": "📝 Контент-бизнес",
            "description": "YouTube, блог, подкаст",
            "income_range": "$100 - $100,000/мес",
            "time_to_profit": "3-12 месяцев",
            "difficulty": "Средняя",
            "ai_automation": "60-80%",
            "skills_needed": ["Контент", "Постоянство", "Маркетинг"],
            "platforms": ["YouTube", "Telegram", "TikTok", "Medium"],
            "steps": [
                "Выбрать нишу и формат",
                "Создать контент-план с AI",
                "Публиковать регулярно",
                "Монетизировать аудиторию",
                "Диверсифицировать доходы"
            ]
        },
        BusinessModel.AI_SERVICES: {
            "name": "🤖 AI-сервисы",
            "description": "Услуги на основе AI",
            "income_range": "$1,000 - $50,000/мес",
            "time_to_profit": "1-4 недели",
            "difficulty": "Низкая-Средняя",
            "ai_automation": "90-95%",
            "skills_needed": ["Промпт-инжиниринг", "Маркетинг"],
            "platforms": ["Собственный бот", "Fiverr", "Telegram"],
            "steps": [
                "Выбрать AI-услугу (тексты, изображения, код)",
                "Создать воронку/бота",
                "Настроить автоматизацию",
                "Привлечь клиентов",
                "Масштабировать"
            ]
        },
        BusinessModel.AUTOMATION: {
            "name": "⚙️ Автоматизация для бизнеса",
            "description": "Боты, интеграции, автоматизации",
            "income_range": "$2,000 - $30,000/мес",
            "time_to_profit": "2-4 недели",
            "difficulty": "Средняя",
            "ai_automation": "60-80%",
            "skills_needed": ["No-code/Low-code", "Логика", "Коммуникация"],
            "platforms": ["Make", "Zapier", "n8n", "Telegram Bots"],
            "steps": [
                "Изучить инструменты автоматизации",
                "Найти бизнесы с рутинными процессами",
                "Предложить автоматизацию",
                "Создать решение",
                "Брать абонентскую плату"
            ]
        }
    }
    
    QUICK_WINS = [
        {
            "name": "AI-копирайтинг на Kwork",
            "income": "$300-1000/мес",
            "time": "3-7 дней до первого заказа",
            "steps": ["Регистрация", "Создать 5 кворков", "AI пишет тексты"]
        },
        {
            "name": "Telegram-бот для бизнеса",
            "income": "$500-3000/проект",
            "time": "1-2 недели",
            "steps": ["Изучить aiogram", "Найти клиента", "Создать бота"]
        },
        {
            "name": "AI-дизайн на Fiverr",
            "income": "$500-2000/мес",
            "time": "1-2 недели",
            "steps": ["Midjourney/DALL-E", "Создать портфолио", "Продавать"]
        },
        {
            "name": "Notion-шаблоны",
            "income": "$100-5000/мес",
            "time": "1 неделя",
            "steps": ["Создать шаблон", "Gumroad", "Продвигать в Twitter/Reddit"]
        },
        {
            "name": "AI-консультации",
            "income": "$1000-5000/мес",
            "time": "Сразу",
            "steps": ["Упаковать экспертизу", "Calendly", "LinkedIn/Telegram"]
        }
    ]
    
    NICHES_2024_2025 = [
        {"niche": "AI-инструменты для бизнеса", "trend": "🔥🔥🔥", "competition": "Средняя"},
        {"niche": "Автоматизация с n8n/Make", "trend": "🔥🔥🔥", "competition": "Низкая"},
        {"niche": "Микро-SaaS", "trend": "🔥🔥🔥", "competition": "Средняя"},
        {"niche": "AI-контент для соцсетей", "trend": "🔥🔥", "competition": "Высокая"},
        {"niche": "Telegram-боты", "trend": "🔥🔥", "competition": "Средняя"},
        {"niche": "No-code разработка", "trend": "🔥🔥", "competition": "Средняя"},
        {"niche": "Образовательные продукты", "trend": "🔥🔥", "competition": "Высокая"},
        {"niche": "E-commerce автоматизация", "trend": "🔥🔥", "competition": "Низкая"},
    ]

    @classmethod
    def get_business_model(cls, model: BusinessModel) -> Dict:
        return cls.INCOME_STREAMS.get(model, {})
    
    @classmethod
    def get_quick_wins(cls) -> List[Dict]:
        return cls.QUICK_WINS
    
    @classmethod
    def get_hot_niches(cls) -> List[Dict]:
        return cls.NICHES_2024_2025
    
    @classmethod
    def format_business_model(cls, model: BusinessModel) -> str:
        data = cls.get_business_model(model)
        if not data:
            return "Информация недоступна"
        
        steps = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(data['steps'])])
        platforms = ", ".join(data['platforms'])
        
        return f"""
{data['name']}

📝 {data['description']}
💵 Доход: {data['income_range']}
⏱ До первой прибыли: {data['time_to_profit']}
📊 Сложность: {data['difficulty']}
🤖 AI-автоматизация: {data['ai_automation']}

📋 Шаги:
{steps}

🌐 Платформы: {platforms}
"""

# ═══════════════════════════════════════════════════════════════════════════
# СТРУКТУРЫ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class UserProfile:
    """Профиль пользователя"""
    user_id: int
    username: str = ""
    first_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    total_queries: int = 0
    total_tasks: int = 0
    expertise_level: str = "beginner"
    income_goal: str = "$1000/мес"
    preferred_models: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    completed_actions: List[str] = field(default_factory=list)

@dataclass
class ConversationContext:
    """Контекст разговора"""
    user_id: int
    messages: List[Dict] = field(default_factory=list)
    current_topic: str = ""
    last_query: str = ""
    last_response: str = ""
    last_actions: List[Dict] = field(default_factory=list)
    session_start: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content[:500],  # Лимит для экономии
            "time": datetime.now().isoformat()
        })
        if len(self.messages) > config.MAX_HISTORY_ITEMS:
            self.messages = self.messages[-config.MAX_HISTORY_ITEMS:]
    
    def get_summary(self) -> str:
        if not self.messages:
            return ""
        recent = self.messages[-3:]
        return "\n".join([f"{m['role']}: {m['content'][:150]}" for m in recent])

# ═══════════════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════════════════

class Statistics:
    """Система статистики"""
    
    def __init__(self):
        self.queries_total = 0
        self.tasks_completed = 0
        self.tokens_saved = 0
        self.errors = 0
        self.start_time = datetime.now()
        self.agents_usage: Dict[str, int] = defaultdict(int)
        self.models_usage: Dict[str, int] = defaultdict(int)
        self.popular_topics: Dict[str, int] = defaultdict(int)
    
    def record_query(self, topic: str = "general"):
        self.queries_total += 1
        self.popular_topics[topic] += 1
    
    def record_model_usage(self, model: str):
        self.models_usage[model] += 1
    
    def record_tokens_saved(self, saved: int):
        self.tokens_saved += saved
    
    def record_agent(self, agent: str):
        self.agents_usage[agent] += 1
    
    def record_task(self):
        self.tasks_completed += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_summary(self) -> str:
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        top_agents = sorted(self.agents_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        top_topics = sorted(self.popular_topics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return f"""📊 *СТАТИСТИКА DEEPTHINK v3.0*

⏱ Время работы: {hours:.1f} часов
💬 Запросов: {self.queries_total}
✅ Задач выполнено: {self.tasks_completed}
💰 Токенов сэкономлено: ~{self.tokens_saved}
❌ Ошибок: {self.errors}

🤖 *Топ агентов:*
{chr(10).join([f"• {a}: {c}" for a, c in top_agents]) or "• Нет данных"}

📈 *Популярные темы:*
{chr(10).join([f"• {t}: {c}" for t, c in top_topics]) or "• Нет данных"}

💡 Режим экономии: {'✅ ВКЛ' if config.ECONOMY_MODE else '❌ ВЫКЛ'}
"""

stats = Statistics()

# ═══════════════════════════════════════════════════════════════════════════
# AI ДВИЖОК - ОПТИМИЗИРОВАННЫЙ
# ═══════════════════════════════════════════════════════════════════════════

print("🚀 Загрузка системы...")

import httpx

try:
    from openai import OpenAI
    ai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_KEY
    )
    logger.info("✅ AI клиент готов")
except Exception as e:
    logger.error(f"❌ Ошибка AI: {e}")
    ai_client = None

class AIEngine:
    """Оптимизированный AI движок с fallback на бесплатные модели"""
    
    def __init__(self):
        self.client = ai_client
        self.current_model_index = 0
        self.request_count = 0
        self.errors_count = 0
    
    def _get_model(self, prefer_free: bool = True) -> str:
        """Получить модель с учетом режима экономии"""
        if config.ECONOMY_MODE or prefer_free:
            models = config.FREE_MODELS
        else:
            models = config.PREMIUM_MODELS
        
        # Ротация моделей при ошибках
        model = models[self.current_model_index % len(models)]
        return model
    
    def _rotate_model(self):
        """Переключиться на следующую модель"""
        self.current_model_index += 1
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        system_prompt: str = None,
        prefer_free: bool = True
    ) -> Tuple[str, bool]:
        """Генерация с автоматическим fallback"""
        
        max_tokens = max_tokens or config.MAX_TOKENS_STANDARD
        temperature = temperature or config.TEMPERATURE
        
        # Уменьшаем токены если в режиме экономии
        if config.ECONOMY_MODE:
            max_tokens = min(max_tokens, config.MAX_TOKENS_FREE)
            stats.record_tokens_saved(config.MAX_TOKENS_ACTION - max_tokens)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt[:500]})
        messages.append({"role": "user", "content": prompt[:config.MAX_CONTEXT_LENGTH]})
        
        # Пробуем несколько моделей
        attempts = 0
        max_attempts = len(config.FREE_MODELS) + 1
        
        while attempts < max_attempts:
            model = self._get_model(prefer_free)
            
            try:
                self.request_count += 1
                stats.record_model_usage(model)
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                result = response.choices[0].message.content
                logger.info(f"✅ Ответ от {model.split('/')[-1]}")
                return result, True
                
            except Exception as e:
                error_str = str(e)
                logger.warning(f"⚠️ {model}: {error_str[:100]}")
                
                # Если ошибка 402 (нет кредитов) - переключаемся
                if "402" in error_str or "credits" in error_str.lower():
                    self._rotate_model()
                    attempts += 1
                    continue
                
                # Другие ошибки
                self.errors_count += 1
                stats.record_error()
                self._rotate_model()
                attempts += 1
        
        return "⚠️ Все модели недоступны. Попробуйте позже.", False
    
    async def generate_short(self, prompt: str) -> Tuple[str, bool]:
        """Короткий ответ для экономии токенов"""
        return await self.generate(
            prompt=prompt,
            max_tokens=config.MAX_TOKENS_SHORT,
            temperature=0.5
        )
    
    async def generate_json(self, prompt: str) -> Tuple[Any, bool]:
        """Генерация JSON"""
        response, success = await self.generate(
            prompt=prompt + "\n\nВерни ТОЛЬКО JSON!",
            max_tokens=config.MAX_TOKENS_SHORT,
            temperature=0.3
        )
        
        if success:
            try:
                match = re.search(r'[\[\{].*[\]\}]', response, re.DOTALL)
                if match:
                    return json.loads(match.group()), True
            except:
                pass
        
        return None, False

ai_engine = AIEngine()

# ═══════════════════════════════════════════════════════════════════════════
# СИСТЕМА АГЕНТОВ - 20 СПЕЦИАЛИЗАЦИЙ
# ═══════════════════════════════════════════════════════════════════════════

class Agent:
    """Агент с оптимизированными промптами"""
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        emoji: str,
        specialty: str,
        keywords: List[str]
    ):
        self.agent_type = agent_type
        self.name = name
        self.emoji = emoji
        self.specialty = specialty
        self.keywords = keywords
        self.calls = 0
    
    @property
    def display_name(self) -> str:
        return f"{self.emoji} {self.name}"
    
    def matches(self, query: str) -> float:
        """Оценка соответствия запросу"""
        q = query.lower()
        matches = sum(1 for kw in self.keywords if kw in q)
        return min(matches / max(len(self.keywords) * 0.3, 1), 1.0)
    
    async def analyze(self, task: str, context: str = "") -> Tuple[str, bool]:
        """Анализ задачи - ОПТИМИЗИРОВАННЫЙ ПРОМПТ"""
        
        self.calls += 1
        stats.record_agent(self.name)
        
        # Короткий системный промпт для экономии токенов
        system = f"Ты {self.name} - {self.specialty}. Отвечай кратко, по делу, с цифрами."
        
        prompt = f"""Задача: {task}

{'Контекст: ' + context[:300] if context else ''}

Дай конкретный ответ с:
- Цифрами и примерами
- Способами заработка
- Конкретными шагами"""
        
        return await ai_engine.generate(
            prompt=prompt,
            system_prompt=system,
            max_tokens=config.MAX_TOKENS_STANDARD
        )

class AgentSwarm:
    """Рой из 20 агентов"""
    
    def __init__(self):
        self.agents: Dict[AgentType, Agent] = {}
        self._init_agents()
    
    def _init_agents(self):
        """Инициализация всех агентов"""
        
        agents_data = [
            # Основные
            (AgentType.RESEARCHER, "Исследователь", "🔬", 
             "анализ рынков и трендов", 
             ["анализ", "исследование", "тренд", "рынок", "статистика"]),
            
            (AgentType.MONEY_EXPERT, "Эксперт заработка", "💰",
             "монетизация и доход",
             ["заработок", "деньги", "доход", "монетизация", "прибыль"]),
            
            (AgentType.STRATEGIST, "Стратег", "🏗️",
             "стратегии и планирование",
             ["план", "стратегия", "roadmap", "масштаб", "развитие"]),
            
            (AgentType.CONTENT_CREATOR, "Контент-мейкер", "✍️",
             "создание контента",
             ["контент", "текст", "пост", "статья", "копирайт"]),
            
            (AgentType.CODER, "Кодер", "💻",
             "программирование и автоматизация",
             ["код", "программа", "бот", "скрипт", "python", "автоматизация"]),
            
            (AgentType.MARKETER, "Маркетолог", "📢",
             "маркетинг и продвижение",
             ["маркетинг", "реклама", "продвижение", "таргет", "трафик"]),
            
            # Специализированные для заработка
            (AgentType.DROPSHIPPER, "Дропшиппер", "📦",
             "дропшиппинг и e-commerce",
             ["дропшиппинг", "товар", "поставщик", "магазин", "wildberries", "ozon"]),
            
            (AgentType.AFFILIATE, "Партнёрщик", "🔗",
             "партнёрский маркетинг",
             ["партнёрка", "affiliate", "реферал", "ссылка", "комиссия"]),
            
            (AgentType.FREELANCER, "Фрилансер", "🎯",
             "фриланс и услуги",
             ["фриланс", "заказ", "клиент", "услуга", "kwork", "fiverr"]),
            
            (AgentType.CRYPTO_EXPERT, "Крипто-эксперт", "🪙",
             "криптовалюты и web3",
             ["крипто", "биткоин", "блокчейн", "nft", "web3", "токен"]),
            
            (AgentType.ECOMMERCE, "E-commerce", "🛒",
             "интернет-торговля",
             ["магазин", "товар", "продажа", "маркетплейс", "склад"]),
            
            (AgentType.SAAS_EXPERT, "SaaS-эксперт", "☁️",
             "SaaS и подписочные модели",
             ["saas", "подписка", "сервис", "приложение", "стартап"]),
            
            # Аналитика и креатив
            (AgentType.DATA_ANALYST, "Аналитик данных", "📊",
             "аналитика и метрики",
             ["данные", "метрика", "аналитика", "kpi", "отчёт"]),
            
            (AgentType.CREATIVE_DIRECTOR, "Креативщик", "🎨",
             "креатив и идеи",
             ["идея", "креатив", "бренд", "концепция", "уникальный"]),
            
            (AgentType.COPYWRITER, "Копирайтер", "📝",
             "продающие тексты",
             ["текст", "продающий", "заголовок", "письмо", "лендинг"]),
            
            (AgentType.SEO_EXPERT, "SEO-эксперт", "🔍",
             "поисковая оптимизация",
             ["seo", "поиск", "google", "ключевые", "оптимизация"]),
            
            # Специалисты
            (AgentType.INVESTOR, "Инвестор", "📈",
             "инвестиции и финансы",
             ["инвестиция", "вложение", "актив", "портфель", "риск"]),
            
            (AgentType.AUTOMATION, "Автоматизатор", "⚙️",
             "автоматизация процессов",
             ["автоматизация", "интеграция", "zapier", "make", "n8n"]),
            
            (AgentType.COACH, "Коуч", "🎯",
             "мотивация и развитие",
             ["мотивация", "цель", "рост", "привычка", "продуктивность"]),
            
            (AgentType.LEGAL, "Юрист", "⚖️",
             "правовые вопросы",
             ["закон", "договор", "право", "налог", "юридический"]),
        ]
        
        for data in agents_data:
            agent = Agent(*data)
            self.agents[data[0]] = agent
        
        logger.info(f"✅ Загружено {len(self.agents)} агентов")
    
    def select_for_query(self, query: str, max_agents: int = None) -> List[Agent]:
        """Умный выбор агентов"""
        max_agents = max_agents or config.MAX_AGENTS_PER_QUERY
        
        # Оценка каждого агента
        scored = [(agent, agent.matches(query)) for agent in self.agents.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Обязательные агенты
        must_have = {AgentType.MONEY_EXPERT, AgentType.RESEARCHER}
        selected = []
        
        for agent_type in must_have:
            if agent_type in self.agents:
                selected.append(self.agents[agent_type])
        
        # Добавляем релевантных
        for agent, score in scored:
            if len(selected) >= max_agents:
                break
            if agent not in selected and score > 0.1:
                selected.append(agent)
        
        return selected[:max_agents]
    
    async def think_together(
        self,
        query: str,
        context: str = ""
    ) -> List[Tuple[str, str, bool]]:
        """Коллективное мышление"""
        
        agents = self.select_for_query(query)
        
        tasks = [agent.analyze(query, context) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                responses.append((agent.display_name, f"Ошибка: {result}", False))
            else:
                text, success = result
                responses.append((agent.display_name, text, success))
        
        return responses

swarm = AgentSwarm()

# ═══════════════════════════════════════════════════════════════════════════
# СИНТЕЗАТОР ОТВЕТОВ - ОПТИМИЗИРОВАННЫЙ
# ═══════════════════════════════════════════════════════════════════════════

class ResponseSynthesizer:
    """Синтезатор с экономией токенов"""
    
    @staticmethod
    async def synthesize(
        query: str,
        agent_responses: List[Tuple[str, str, bool]],
        user_profile: UserProfile = None
    ) -> str:
        """Синтез ответов в единый"""
        
        # Собираем успешные ответы
        valid_responses = [
            f"[{name}]: {text[:400]}"
            for name, text, success in agent_responses if success
        ]
        
        if not valid_responses:
            return "⚠️ Не удалось получить ответы от агентов. Попробуйте переформулировать вопрос."
        
        agents_input = "\n\n".join(valid_responses)
        
        # Короткий промпт для синтеза
        prompt = f"""Объедини ответы экспертов в полезный ответ.

ВОПРОС: {query}

ОТВЕТЫ ЭКСПЕРТОВ:
{agents_input}

ФОРМАТ ОТВЕТА:

🧠 *СУТЬ* (2-3 предложения)

💰 *КАК ЗАРАБОТАТЬ:*

*1. [Способ]* - $X/мес
• Делаем: ...
• AI помогает: X%
• Шаги: 1, 2, 3

*2. [Способ]* - $X/мес
• Делаем: ...

*3. [Способ]* - $X/мес
• Делаем: ...

🎯 *НАЧНИ СЕЙЧАС:* [конкретное действие]

Кратко и по делу!"""
        
        response, success = await ai_engine.generate(
            prompt=prompt,
            max_tokens=config.MAX_TOKENS_FREE
        )
        
        if not success:
            # Fallback - простое объединение
            return "\n\n---\n\n".join([
                f"{name}:\n{text[:500]}"
                for name, text, s in agent_responses if s
            ])
        
        return response

# ═══════════════════════════════════════════════════════════════════════════
# ГЕНЕРАТОР ДЕЙСТВИЙ
# ═══════════════════════════════════════════════════════════════════════════

class ActionGenerator:
    """Генератор автоматических действий"""
    
    ACTION_TEMPLATES = {
        "create_content": ("✍️", "Создать контент"),
        "create_code": ("💻", "Написать код"),
        "create_plan": ("📋", "Составить план"),
        "create_template": ("📄", "Создать шаблон"),
        "brainstorm": ("💡", "Генерировать идеи"),
        "analyze": ("📊", "Провести анализ"),
        "find_niches": ("🔍", "Найти ниши"),
        "calculate_income": ("🧮", "Рассчитать доход"),
    }
    
    @classmethod
    async def generate(cls, query: str, analysis: str) -> List[Dict]:
        """Генерация действий"""
        
        # Быстрая генерация без AI для экономии
        actions = []
        q = query.lower()
        
        if any(w in q for w in ["контент", "текст", "пост"]):
            actions.append({
                "type": "create_content",
                "name": "✍️ Создать контент",
                "description": f"Готовый контент по теме: {query[:50]}"
            })
        
        if any(w in q for w in ["код", "бот", "скрипт", "автоматизация"]):
            actions.append({
                "type": "create_code",
                "name": "💻 Написать код",
                "description": f"Рабочий код: {query[:50]}"
            })
        
        if any(w in q for w in ["план", "стратегия", "как начать"]):
            actions.append({
                "type": "create_plan",
                "name": "📋 Пошаговый план",
                "description": f"Детальный план: {query[:50]}"
            })
        
        if any(w in q for w in ["идея", "ниша", "что делать"]):
            actions.append({
                "type": "brainstorm",
                "name": "💡 10 идей",
                "description": f"Идеи для заработка: {query[:50]}"
            })
        
        if any(w in q for w in ["заработ", "доход", "деньги"]):
            actions.append({
                "type": "calculate_income",
                "name": "🧮 Расчёт дохода",
                "description": "Калькулятор потенциального дохода"
            })
        
        # Дефолтные действия если ничего не подошло
        if not actions:
            actions = [
                {
                    "type": "create_plan",
                    "name": "📋 План действий",
                    "description": f"План по теме: {query[:50]}"
                },
                {
                    "type": "brainstorm",
                    "name": "💡 Идеи",
                    "description": "Генерация идей"
                }
            ]
        
        return actions[:config.MAX_ACTIONS_PER_RESPONSE]
    
    @classmethod
    async def execute(cls, action: Dict, context: str) -> str:
        """Выполнение действия"""
        
        action_type = action.get("type", "create_plan")
        desc = action.get("description", "")
        
        prompts = {
            "create_content": f"""Создай готовый контент: {desc}

Включи:
- Заголовок
- Основной текст (300-500 слов)
- Призыв к действию
- Хештеги

Контент должен быть готов к публикации!""",

            "create_code": f"""Напиши рабочий Python код: {desc}

Требования:
- Полностью рабочий код
- Комментарии на русском
- Обработка ошибок
- Пример использования""",

            "create_plan": f"""Создай пошаговый план: {desc}

Формат:
📅 ДЕНЬ 1-7:
• Конкретные действия
• Ожидаемые результаты

📅 НЕДЕЛЯ 2-4:
• Следующие шаги
• Метрики успеха

💰 Ожидаемый доход: $X/мес""",

            "brainstorm": f"""Сгенерируй 10 идей: {desc}

Для каждой идеи:
1. [Название]
   💰 Потенциал: $X/мес
   ⏱ Время до результата
   🎯 Первый шаг""",

            "calculate_income": f"""Рассчитай потенциальный доход: {desc}

КАЛЬКУЛЯТОР ДОХОДА:

📊 Базовый сценарий:
• Часов в неделю: X
• Ставка/цена: $X
• Доход: $X/мес

📈 Оптимистичный:
• При масштабировании: $X/мес

⚠️ Консервативный:
• Минимум: $X/мес

🎯 Рекомендация: ...""",

            "analyze": f"""Проведи анализ: {desc}

SWOT:
✅ Сильные стороны:
❌ Слабые стороны:
🚀 Возможности:
⚠️ Угрозы:

📊 Вывод: ...""",
        }
        
        prompt = prompts.get(action_type, prompts["create_plan"])
        prompt += f"\n\nКонтекст: {context[:500]}"
        
        response, success = await ai_engine.generate(
            prompt=prompt,
            max_tokens=config.MAX_TOKENS_ACTION
        )
        
        if success:
            stats.record_task()
        
        return response

# ═══════════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ МОЗГ
# ═══════════════════════════════════════════════════════════════════════════

class DeepThinkBrain:
    """Главный мозг системы"""
    
    def __init__(self):
        self.knowledge = MoneyKnowledgeBase()
        self.synthesizer = ResponseSynthesizer()
        self.action_gen = ActionGenerator()
    
    async def think(
        self,
        query: str,
        context: ConversationContext = None,
        user_profile: UserProfile = None
    ) -> Dict:
        """Глубокий анализ"""
        
        import time
        start = time.time()
        
        stats.record_query(self._detect_topic(query))
        
        # Контекст разговора
        ctx_summary = context.get_summary() if context else ""
        
        # Коллективное мышление агентов
        responses = await swarm.think_together(query, ctx_summary)
        
        # Синтез
        synthesis = await self.synthesizer.synthesize(
            query, responses, user_profile
        )
        
        # Генерация действий
        actions = await self.action_gen.generate(query, synthesis)
        
        # Агенты которые работали
        agents_used = [name for name, _, success in responses if success]
        
        total_time = time.time() - start
        
        return {
            "response": synthesis,
            "agents": agents_used[:4],
            "actions": actions,
            "time": total_time
        }
    
    def _detect_topic(self, query: str) -> str:
        """Определение темы"""
        q = query.lower()
        if any(w in q for w in ["заработ", "деньги", "доход"]):
            return "money"
        if any(w in q for w in ["код", "бот", "программ"]):
            return "tech"
        if any(w in q for w in ["контент", "текст"]):
            return "content"
        if any(w in q for w in ["маркетинг", "реклама"]):
            return "marketing"
        return "general"

brain = DeepThinkBrain()

# ═══════════════════════════════════════════════════════════════════════════
# МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЕЙ
# ═══════════════════════════════════════════════════════════════════════════

class UserManager:
    """Менеджер пользователей"""
    
    def __init__(self):
        self.profiles: Dict[int, UserProfile] = {}
        self.contexts: Dict[int, ConversationContext] = {}
    
    def get_profile(self, user_data: Dict) -> UserProfile:
        uid = user_data.get("id")
        if uid not in self.profiles:
            self.profiles[uid] = UserProfile(
                user_id=uid,
                username=user_data.get("username", ""),
                first_name=user_data.get("first_name", "User")
            )
        profile = self.profiles[uid]
        profile.last_active = datetime.now()
        return profile
    
    def get_context(self, user_id: int) -> ConversationContext:
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id=user_id)
        return self.contexts[user_id]

user_manager = UserManager()

# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════

class TelegramBot:
    """Telegram бот с расширенным функционалом"""
    
    def __init__(self):
        self.api = config.TELEGRAM_API
        self.pending_actions: Dict[str, Dict] = {}
    
    async def send(
        self,
        chat_id: int,
        text: str,
        buttons: Dict = None,
        parse_mode: str = "Markdown"
    ):
        """Отправка сообщения"""
        async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
            data = {"chat_id": chat_id, "text": text[:4096]}
            
            if parse_mode:
                data["parse_mode"] = parse_mode
            if buttons:
                data["reply_markup"] = json.dumps(buttons)
            
            try:
                await client.post(f"{self.api}/sendMessage", json=data)
            except:
                # Без форматирования
                data.pop("parse_mode", None)
                try:
                    await client.post(f"{self.api}/sendMessage", json=data)
                except Exception as e:
                    logger.error(f"Send error: {e}")
    
    async def answer_callback(self, callback_id: str, text: str = None):
        """Ответ на callback"""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    f"{self.api}/answerCallbackQuery",
                    json={"callback_query_id": callback_id, "text": text}
                )
            except:
                pass
    
    async def send_typing(self, chat_id: int):
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
        
        for i, action in enumerate(actions[:5]):
            keyboard.append([{
                "text": action.get("name", "🤖 Действие")[:30],
                "callback_data": f"act_{i}_{user_id}"
            }])
        
        # Дополнительные кнопки
        keyboard.append([
            {"text": "💰 Способы заработка", "callback_data": f"income_{user_id}"},
            {"text": "🔥 Горячие ниши", "callback_data": f"niches_{user_id}"}
        ])
        
        keyboard.append([
            {"text": "⚡ Быстрый старт", "callback_data": f"quickwin_{user_id}"},
            {"text": "📊 Статистика", "callback_data": f"stats_{user_id}"}
        ])
        
        keyboard.append([
            {"text": "⚙️ Настройки", "callback_data": f"settings_{user_id}"},
            {"text": "❓ Помощь", "callback_data": f"help_{user_id}"}
        ])
        
        return {"inline_keyboard": keyboard}
    
    # ═══════════════════════════════════════════════════════════════
    # КОМАНДЫ
    # ═══════════════════════════════════════════════════════════════
    
    async def cmd_start(self, chat_id: int, user_data: Dict):
        """Команда /start"""
        profile = user_manager.get_profile(user_data)
        
        text = f"""🧠 *DEEPTHINK AUTOHUSTLE v3.0*
_Ultimate Money Edition_

Привет, {profile.first_name}! 👋

Я - AI-система для поиска способов заработка.

🤖 *{len(swarm.agents)} АГЕНТОВ:*
• Эксперт заработка, Стратег, Маркетолог
• Кодер, Копирайтер, SEO-специалист
• Криптоэксперт, SaaS-эксперт и другие

💰 *ЧТО Я УМЕЮ:*
• Найти способы заработка под тебя
• Создать бизнес-план за минуты
• Написать код, контент, стратегию
• Рассчитать потенциальный доход

🚀 *БЫСТРЫЙ СТАРТ:*
• "Как заработать на AI?"
• "Создай Telegram-бота для бизнеса"
• "Топ ниши 2025 для новичка"
• "План заработка $1000/мес"

💡 Просто напиши свой вопрос!

/help - все команды
/income - способы заработка
/niches - горячие ниши"""
        
        await self.send(chat_id, text)
    
    async def cmd_help(self, chat_id: int):
        """Команда /help"""
        text = """📖 *КОМАНДЫ DEEPTHINK v3.0*

*ОСНОВНЫЕ:*
/start - Начало работы
/help - Эта справка

*ЗАРАБОТОК:*
/income - 8 способов заработка
/niches - Горячие ниши 2024-2025
/quickwin - Быстрые победы (деньги за неделю)
/calc - Калькулятор дохода

*СОЗДАНИЕ:*
/plan [тема] - Бизнес-план
/content [тема] - Готовый контент
/code [описание] - Написать код
/ideas [тема] - 10 идей

*СИСТЕМА:*
/stats - Статистика бота
/agents - Список агентов
/settings - Настройки
/mode - Переключить режим экономии

*СОВЕТЫ:*
✅ Чем конкретнее запрос - тем лучше ответ
✅ Указывай бюджет, сроки, цели
✅ Используй кнопки для действий"""
        
        await self.send(chat_id, text)
    
    async def cmd_income(self, chat_id: int):
        """Способы заработка"""
        text = "💰 *8 СПОСОБОВ ЗАРАБОТКА С AI*\n\n"
        
        for model, data in MoneyKnowledgeBase.INCOME_STREAMS.items():
            text += f"*{data['name']}*\n"
            text += f"💵 {data['income_range']}\n"
            text += f"⏱ {data['time_to_profit']}\n"
            text += f"🤖 AI: {data['ai_automation']}\n\n"
        
        text += "_Нажми на кнопку для подробностей_"
        
        buttons = {"inline_keyboard": [
            [{"text": "🎨 Фриланс", "callback_data": "bm_freelance"}],
            [{"text": "🔗 Партнёрки", "callback_data": "bm_affiliate"}],
            [{"text": "📦 Дропшиппинг", "callback_data": "bm_dropshipping"}],
            [{"text": "📱 Цифровые продукты", "callback_data": "bm_digital"}],
            [{"text": "☁️ SaaS", "callback_data": "bm_saas"}],
            [{"text": "🤖 AI-сервисы", "callback_data": "bm_ai"}],
        ]}
        
        await self.send(chat_id, text, buttons)
    
    async def cmd_niches(self, chat_id: int):
        """Горячие ниши"""
        text = "🔥 *ГОРЯЧИЕ НИШИ 2024-2025*\n\n"
        
        for niche in MoneyKnowledgeBase.NICHES_2024_2025:
            text += f"• *{niche['niche']}*\n"
            text += f"  Тренд: {niche['trend']} | Конкуренция: {niche['competition']}\n\n"
        
        text += "_Выбери нишу и спроси подробнее!_"
        
        await self.send(chat_id, text)
    
    async def cmd_quickwin(self, chat_id: int):
        """Быстрые победы"""
        text = "⚡ *БЫСТРЫЕ ПОБЕДЫ - ДЕНЬГИ ЗА НЕДЕЛЮ*\n\n"
        
        for i, qw in enumerate(MoneyKnowledgeBase.QUICK_WINS, 1):
            text += f"*{i}. {qw['name']}*\n"
            text += f"💰 {qw['income']}\n"
            text += f"⏱ {qw['time']}\n"
            text += f"📋 {' → '.join(qw['steps'])}\n\n"
        
        text += "_Напиши номер для подробного плана!_"
        
        await self.send(chat_id, text)
    
    async def cmd_stats(self, chat_id: int):
        """Статистика"""
        await self.send(chat_id, stats.get_summary())
    
    async def cmd_agents(self, chat_id: int):
        """Список агентов"""
        text = f"🤖 *{len(swarm.agents)} АГЕНТОВ DEEPTHINK*\n\n"
        
        for agent in swarm.agents.values():
            text += f"{agent.display_name}\n"
            text += f"  _{agent.specialty}_\n"
            text += f"  📊 Вызовов: {agent.calls}\n\n"
        
        await self.send(chat_id, text)
    
    async def cmd_settings(self, chat_id: int, user_id: int):
        """Настройки"""
        profile = user_manager.profiles.get(user_id)
        
        text = f"""⚙️ *НАСТРОЙКИ*

👤 ID: `{user_id}`
📊 Запросов: {profile.total_queries if profile else 0}
🎯 Уровень: {profile.expertise_level if profile else 'beginner'}

💡 *Режим экономии:* {'✅ ВКЛ' if config.ECONOMY_MODE else '❌ ВЫКЛ'}
_(бесплатные модели для экономии токенов)_

🔧 Выбери настройку:"""
        
        buttons = {"inline_keyboard": [
            [
                {"text": "🌱 Новичок", "callback_data": f"lvl_beginner_{user_id}"},
                {"text": "📈 Средний", "callback_data": f"lvl_intermediate_{user_id}"},
                {"text": "🎓 Эксперт", "callback_data": f"lvl_expert_{user_id}"}
            ],
            [
                {"text": "💰 Экономия ВКЛ" if not config.ECONOMY_MODE else "🚀 Экономия ВЫКЛ", 
                 "callback_data": f"toggle_economy_{user_id}"}
            ]
        ]}
        
        await self.send(chat_id, text, buttons)
    
    async def cmd_mode(self, chat_id: int):
        """Переключение режима"""
        config.ECONOMY_MODE = not config.ECONOMY_MODE
        status = "✅ ВКЛЮЧЁН" if config.ECONOMY_MODE else "❌ ВЫКЛЮЧЕН"
        await self.send(chat_id, f"💡 Режим экономии токенов: {status}")
    
    # ═══════════════════════════════════════════════════════════════
    # ОБРАБОТКА СООБЩЕНИЙ
    # ═══════════════════════════════════════════════════════════════
    
    async def handle_message(self, chat_id: int, user_data: Dict, text: str):
        """Обработка сообщения"""
        user_id = user_data.get("id")
        profile = user_manager.get_profile(user_data)
        context = user_manager.get_context(user_id)
        
        # Сохраняем в контекст
        context.add_message("user", text)
        context.last_query = text
        profile.total_queries += 1
        
        await self.send_typing(chat_id)
        
        # Статус
        await self.send(chat_id,
            "🧠 *DEEP THINKING...*\n\n"
            f"🤖 Собираю {config.MAX_AGENTS_PER_QUERY} экспертов...\n"
            "⚡ Анализирую...\n"
            "💰 Ищу способы заработка..."
        )
        
        try:
            # Думаем
            result = await brain.think(text, context, profile)
            
            response = result["response"]
            agents_used = result["agents"]
            actions = result["actions"]
            think_time = result["time"]
            
            # Сохраняем в контекст
            context.add_message("assistant", response[:300])
            context.last_actions = actions
            context.last_response = response
            
            # Сохраняем действия для callback
            for i, action in enumerate(actions):
                self.pending_actions[f"act_{i}_{user_id}"] = {
                    "action": action,
                    "context": text,
                    "response": response[:1000]
                }
            
            # Footer
            agents_str = ", ".join(agents_used[:3])
            footer = f"\n\n---\n👥 _{agents_str}_\n⏱ _{think_time:.1f}с_"
            
            full_response = response + footer
            
            # Кнопки
            buttons = self.make_buttons(actions, user_id)
            
            await self.send(chat_id, full_response[:4096], buttons)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            stats.record_error()
            await self.send(chat_id, f"⚠️ Ошибка: {str(e)[:200]}\n\nПопробуй переформулировать.")
    
    async def handle_callback(self, callback_id: str, chat_id: int, user_id: int, data: str):
        """Обработка callback"""
        
        await self.answer_callback(callback_id)
        
        # Статистика
        if data.startswith("stats_"):
            await self.cmd_stats(chat_id)
            return
        
        # Помощь
        if data.startswith("help_"):
            await self.cmd_help(chat_id)
            return
        
        # Настройки
        if data.startswith("settings_"):
            await self.cmd_settings(chat_id, user_id)
            return
        
        # Способы заработка
        if data.startswith("income_"):
            await self.cmd_income(chat_id)
            return
        
        # Ниши
        if data.startswith("niches_"):
            await self.cmd_niches(chat_id)
            return
        
        # Быстрые победы
        if data.startswith("quickwin_"):
            await self.cmd_quickwin(chat_id)
            return
        
        # Бизнес-модели
        if data.startswith("bm_"):
            model_map = {
                "bm_freelance": BusinessModel.FREELANCE,
                "bm_affiliate": BusinessModel.AFFILIATE,
                "bm_dropshipping": BusinessModel.DROPSHIPPING,
                "bm_digital": BusinessModel.DIGITAL_PRODUCTS,
                "bm_saas": BusinessModel.SAAS,
                "bm_ai": BusinessModel.AI_SERVICES,
            }
            model = model_map.get(data)
            if model:
                info = MoneyKnowledgeBase.format_business_model(model)
                await self.send(chat_id, info)
            return
        
        # Уровень
        if data.startswith("lvl_"):
            parts = data.split("_")
            level = parts[1]
            if user_id in user_manager.profiles:
                user_manager.profiles[user_id].expertise_level = level
            await self.send(chat_id, f"✅ Уровень: *{level}*")
            return
        
        # Переключение экономии
        if data.startswith("toggle_economy_"):
            config.ECONOMY_MODE = not config.ECONOMY_MODE
            status = "✅ ВКЛ" if config.ECONOMY_MODE else "❌ ВЫКЛ"
            await self.send(chat_id, f"💡 Режим экономии: {status}")
            return
        
        # Выполнение действия
        if data.startswith("act_"):
            key = data
            if key in self.pending_actions:
                action_data = self.pending_actions[key]
                action = action_data["action"]
                context = action_data.get("context", "")
                response = action_data.get("response", "")
                
                await self.send_typing(chat_id)
                await self.send(chat_id, f"⚙️ Выполняю: {action.get('name', '')}...")
                
                try:
                    result = await ActionGenerator.execute(
                        action, 
                        f"{context}\n\n{response}"
                    )
                    
                    profile = user_manager.profiles.get(user_id)
                    if profile:
                        profile.total_tasks += 1
                    
                    # Разбиваем длинный ответ
                    if len(result) > 4000:
                        parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
                        for i, part in enumerate(parts):
                            header = f"📄 *Часть {i+1}/{len(parts)}*\n\n" if len(parts) > 1 else ""
                            await self.send(chat_id, header + part)
                    else:
                        await self.send(chat_id, f"✅ *Готово!*\n\n{result}")
                        
                except Exception as e:
                    await self.send(chat_id, f"⚠️ Ошибка: {str(e)[:200]}")
            else:
                await self.send(chat_id, "⚠️ Действие устарело. Сделай новый запрос.")
            return
    
    async def handle_update(self, update: Dict):
        """Обработка обновления"""
        try:
            # Сообщения
            if "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user_data = msg.get("from", {})
                text = msg["text"]
                
                # Команды
                commands = {
                    "/start": lambda: self.cmd_start(chat_id, user_data),
                    "/help": lambda: self.cmd_help(chat_id),
                    "/income": lambda: self.cmd_income(chat_id),
                    "/niches": lambda: self.cmd_niches(chat_id),
                    "/quickwin": lambda: self.cmd_quickwin(chat_id),
                    "/stats": lambda: self.cmd_stats(chat_id),
                    "/agents": lambda: self.cmd_agents(chat_id),
                    "/settings": lambda: self.cmd_settings(chat_id, user_data.get("id")),
                    "/mode": lambda: self.cmd_mode(chat_id),
                }
                
                if text in commands:
                    await commands[text]()
                elif text.startswith("/"):
                    await self.send(chat_id, "❓ Неизвестная команда. /help")
                else:
                    await self.handle_message(chat_id, user_data, text)
            
            # Callbacks
            elif "callback_query" in update:
                cb = update["callback_query"]
                await self.handle_callback(
                    cb["id"],
                    cb["message"]["chat"]["id"],
                    cb["from"]["id"],
                    cb["data"]
                )
                
        except Exception as e:
            logger.error(f"Update error: {e}")
            stats.record_error()
    
    async def run(self):
        """Запуск бота"""
        
        logger.info("=" * 60)
        logger.info("🧠 DEEPTHINK AUTOHUSTLE v3.0 - ULTIMATE MONEY EDITION")
        logger.info("=" * 60)
        logger.info(f"🤖 Агентов: {len(swarm.agents)}")
        logger.info(f"💡 Режим экономии: {'ВКЛ' if config.ECONOMY_MODE else 'ВЫКЛ'}")
        logger.info(f"🔧 Модель: {config.DEFAULT_MODEL}")
        logger.info("=" * 60)
        
        offset = 0
        
        async with httpx.AsyncClient(timeout=config.API_TIMEOUT) as client:
            logger.info("✅ БОТ ЗАПУЩЕН!")
            
            while True:
                try:
                    response = await client.get(
                        f"{self.api}/getUpdates",
                        params={"offset": offset, "timeout": config.POLLING_TIMEOUT}
                    )
                    
                    data = response.json()
                    
                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            offset = update["update_id"] + 1
                            asyncio.create_task(self.handle_update(update))
                    
                except httpx.TimeoutException:
                    continue
                except Exception as e:
                    logger.error(f"Polling error: {e}")
                    stats.record_error()
                    await asyncio.sleep(5)

# ═══════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """Главная функция"""
    print("\n" + "═" * 60)
    print("🧠 DEEPTHINK AUTOHUSTLE v3.0")
    print("💰 ULTIMATE MONEY EDITION")
    print("═" * 60 + "\n")
    
    bot = TelegramBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
