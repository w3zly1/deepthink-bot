"""
╔══════════════════════════════════════════════════════════════════════════╗
║         DEEPTHINK AUTOHUSTLE v4.0 - BULLETPROOF EDITION                  ║
║                                                                          ║
║  🛡️ Исправлены ВСЕ ошибки                                                ║
║  🔄 Прямые HTTP запросы (без openai библиотеки)                          ║
║  💾 Надёжное хранение действий                                           ║
║  🤖 Fallback ответы если AI недоступен                                   ║
║  📊 Детальное логирование                                                ║
║                                                                          ║
║  Python 3.8+ | Render.com Ready                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import threading
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK HTTP SERVER
# ═══════════════════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"[HEALTH] Server on port {port}")
    server.serve_forever()

# ═══════════════════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════

class Logger:
    @staticmethod
    def log(msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{level}] {msg}", flush=True)
    
    @staticmethod
    def info(msg: str): Logger.log(msg, "INFO")
    
    @staticmethod
    def error(msg: str): Logger.log(msg, "ERROR")
    
    @staticmethod
    def warn(msg: str): Logger.log(msg, "WARN")
    
    @staticmethod
    def debug(msg: str): Logger.log(msg, "DEBUG")

log = Logger()

# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

class Config:
    # API
    TELEGRAM_TOKEN = os.environ.get(
        'TELEGRAM_TOKEN',
        '8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY'
    )
    
    OPENROUTER_KEY = os.environ.get(
        'OPENROUTER_KEY',
        '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'
    )
    
    # Актуальные рабочие бесплатные модели OpenRouter (проверено)
    MODELS = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-8b-instruct:free", 
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "openchat/openchat-7b:free",
    ]
    
    # Лимиты
    MAX_TOKENS = 700
    TIMEOUT = 45
    MAX_RETRIES = 3
    
    @property
    def TELEGRAM_API(self):
        return f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}"

cfg = Config()

# ═══════════════════════════════════════════════════════════════════════════
# ИМПОРТ HTTPX
# ═══════════════════════════════════════════════════════════════════════════

log.info("🚀 Запуск DeepThink v4.0...")

try:
    import httpx
    log.info("✅ httpx загружен")
except ImportError:
    log.error("❌ httpx не найден!")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# AI КЛИЕНТ - ПРЯМЫЕ HTTP ЗАПРОСЫ (БЕЗ OPENAI БИБЛИОТЕКИ)
# ═══════════════════════════════════════════════════════════════════════════

class AIClient:
    """AI клиент с прямыми HTTP запросами к OpenRouter"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_index = 0
        self.stats = {"requests": 0, "success": 0, "errors": 0}
        self.last_working_model = None
    
    def _get_model(self) -> str:
        """Получить модель"""
        if self.last_working_model:
            return self.last_working_model
        return cfg.MODELS[self.model_index % len(cfg.MODELS)]
    
    def _rotate_model(self):
        """Следующая модель"""
        self.model_index += 1
        self.last_working_model = None
        model = cfg.MODELS[self.model_index % len(cfg.MODELS)]
        log.warn(f"🔄 Смена модели → {model.split('/')[1][:20]}")
    
    async def generate(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = None,
        temperature: float = 0.7
    ) -> Tuple[str, bool]:
        """Генерация ответа"""
        
        max_tokens = max_tokens or cfg.MAX_TOKENS
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system[:400]})
        messages.append({"role": "user", "content": prompt[:1500]})
        
        # Пробуем все модели
        for attempt in range(len(cfg.MODELS)):
            model = self._get_model()
            
            headers = {
                "Authorization": f"Bearer {cfg.OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/deepthink",
                "X-Title": "DeepThink Bot"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            try:
                self.stats["requests"] += 1
                log.debug(f"📤 Запрос к {model.split('/')[1][:15]}...")
                
                async with httpx.AsyncClient(timeout=cfg.TIMEOUT) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                
                # Проверяем статус
                if response.status_code == 200:
                    data = response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        self.stats["success"] += 1
                        self.last_working_model = model
                        log.info(f"✅ Ответ от {model.split('/')[1][:15]} ({len(content)} символов)")
                        return content, True
                    else:
                        log.warn(f"⚠️ Пустой ответ от {model.split('/')[1][:15]}")
                        self._rotate_model()
                        continue
                
                elif response.status_code == 402:
                    log.warn(f"💳 402 - Нет кредитов для {model.split('/')[1][:15]}")
                    self._rotate_model()
                    continue
                
                elif response.status_code == 429:
                    log.warn(f"⏳ 429 - Rate limit для {model.split('/')[1][:15]}")
                    self._rotate_model()
                    await asyncio.sleep(2)
                    continue
                
                else:
                    error_text = response.text[:200]
                    log.warn(f"❌ {response.status_code}: {error_text}")
                    self._rotate_model()
                    continue
                    
            except httpx.TimeoutException:
                log.warn(f"⏰ Timeout для {model.split('/')[1][:15]}")
                self._rotate_model()
                continue
                
            except Exception as e:
                log.error(f"💥 Ошибка: {str(e)[:100]}")
                self.stats["errors"] += 1
                self._rotate_model()
                continue
        
        # Если все модели не сработали
        log.error("❌ Все модели недоступны!")
        return None, False
    
    def get_stats(self) -> str:
        return f"📊 AI: {self.stats['requests']} запросов, {self.stats['success']} успешных, {self.stats['errors']} ошибок"

ai = AIClient()

# ═══════════════════════════════════════════════════════════════════════════
# БАЗА ЗНАНИЙ - ГОТОВЫЕ ОТВЕТЫ (FALLBACK)
# ═══════════════════════════════════════════════════════════════════════════

class KnowledgeBase:
    """База готовых ответов на случай если AI недоступен"""
    
    # Способы заработка
    INCOME_METHODS = {
        "freelance": {
            "title": "🎨 Фриланс",
            "income": "$500 - $10,000/мес",
            "time": "1-4 недели до первых денег",
            "ai_help": "60%",
            "description": "Продавай свои навыки: копирайтинг, дизайн, программирование, переводы",
            "platforms": "Kwork, Fiverr, Upwork, FL.ru",
            "steps": [
                "Определи свой навык (пиши тексты, рисуй, кодь)",
                "Создай портфолио из 3-5 работ",
                "Зарегистрируйся на 2-3 платформах",
                "Создай привлекательный профиль",
                "Отправляй 10-20 откликов в день",
                "Бери первые заказы дешевле для отзывов",
                "Повышай цены каждые 5-10 заказов"
            ],
            "first_step": "Зайди на Kwork.ru и создай аккаунт прямо сейчас"
        },
        "ai_services": {
            "title": "🤖 AI-услуги",
            "income": "$1,000 - $50,000/мес",
            "time": "1-2 недели",
            "ai_help": "95%",
            "description": "Продавай услуги на основе AI: тексты, картинки, код, переводы",
            "platforms": "Telegram-бот, Kwork, Fiverr",
            "steps": [
                "Выбери услугу: AI-тексты, AI-картинки, AI-код",
                "Создай простого Telegram-бота или профиль на Kwork",
                "AI делает 95% работы, ты только продаёшь",
                "Цена: $5-50 за задачу, себестоимость ~$0",
                "Масштабируй через рекламу"
            ],
            "first_step": "Зайди на Kwork и создай услугу 'Напишу текст с помощью AI'"
        },
        "digital": {
            "title": "📱 Цифровые продукты",
            "income": "$100 - $100,000/мес",
            "time": "2-4 недели",
            "ai_help": "90%",
            "description": "Создавай и продавай: курсы, гайды, шаблоны, чек-листы",
            "platforms": "Gumroad, Boosty, Telegram",
            "steps": [
                "Найди боль аудитории (что люди спрашивают?)",
                "Создай продукт с помощью AI (гайд, курс, шаблон)",
                "Упакуй красиво (Canva + AI)",
                "Размести на Gumroad или Boosty",
                "Продвигай в соцсетях"
            ],
            "first_step": "Напиши 'создай гайд по [твоя тема]' и получи готовый продукт"
        },
        "content": {
            "title": "📝 Контент-бизнес",
            "income": "$500 - $50,000/мес",
            "time": "2-6 месяцев",
            "ai_help": "70%",
            "description": "Веди канал/блог и монетизируй через рекламу, донаты, продажи",
            "platforms": "Telegram, YouTube, TikTok, Дзен",
            "steps": [
                "Выбери нишу (деньги, саморазвитие, tech, юмор)",
                "Создай канал/аккаунт",
                "Публикуй 1-3 поста в день (AI помогает)",
                "Расти аудиторию",
                "Монетизируй: реклама, партнёрки, свои продукты"
            ],
            "first_step": "Создай Telegram-канал на тему которая тебе интересна"
        },
        "bots": {
            "title": "🤖 Telegram-боты",
            "income": "$500 - $20,000/мес",
            "time": "1-3 недели",
            "ai_help": "80%",
            "description": "Создавай ботов на заказ или свои SaaS-боты",
            "platforms": "Telegram, Python/aiogram",
            "steps": [
                "Изучи основы Python + aiogram (AI поможет)",
                "Сделай первого простого бота",
                "Найди клиентов (чаты, биржи)",
                "Бери $300-3000 за бота",
                "Или создай своего бота с подпиской"
            ],
            "first_step": "Попроси меня написать код простого бота"
        },
        "automation": {
            "title": "⚙️ Автоматизация",
            "income": "$2,000 - $30,000/мес",
            "time": "2-4 недели",
            "ai_help": "70%",
            "description": "Автоматизируй процессы для бизнесов за деньги",
            "platforms": "Make, Zapier, n8n, Python",
            "steps": [
                "Изучи Make.com или n8n (no-code)",
                "Найди бизнесы с рутинными процессами",
                "Предложи автоматизацию",
                "Бери $500-5000 за проект + абонплату"
            ],
            "first_step": "Зарегистрируйся на Make.com и пройди их туториал"
        },
        "affiliate": {
            "title": "🔗 Партнёрский маркетинг", 
            "income": "$200 - $50,000/мес",
            "time": "1-3 месяца",
            "ai_help": "80%",
            "description": "Получай комиссию за продажи по своим ссылкам",
            "platforms": "Admitad, Amazon, партнёрки курсов",
            "steps": [
                "Выбери нишу с высокими комиссиями",
                "Создай площадку (Telegram канал, блог)",
                "Регистрируйся в партнёрках",
                "Создавай контент с партнёрскими ссылками",
                "Гони трафик"
            ],
            "first_step": "Создай Telegram-канал в прибыльной нише"
        },
        "dropshipping": {
            "title": "📦 Дропшиппинг",
            "income": "$500 - $30,000/мес",
            "time": "2-6 недель",
            "ai_help": "50%",
            "description": "Продавай товары без склада - поставщик отправляет напрямую",
            "platforms": "Wildberries, Ozon, Shopify",
            "steps": [
                "Найди trending товар",
                "Найди поставщика",
                "Создай карточку товара",
                "Запусти рекламу",
                "Масштабируй"
            ],
            "first_step": "Изучи топ товаров на Wildberries"
        }
    }
    
    # Горячие ниши
    HOT_NICHES = [
        {"name": "AI-инструменты для бизнеса", "trend": "🔥🔥🔥", "competition": "Средняя", "potential": "$5-50k/мес"},
        {"name": "Автоматизация (Make/n8n)", "trend": "🔥🔥🔥", "competition": "Низкая", "potential": "$3-30k/мес"},
        {"name": "Telegram-боты", "trend": "🔥🔥🔥", "competition": "Средняя", "potential": "$1-20k/мес"},
        {"name": "Микро-SaaS", "trend": "🔥🔥", "competition": "Средняя", "potential": "$1-100k/мес"},
        {"name": "No-code разработка", "trend": "🔥🔥", "competition": "Низкая", "potential": "$2-15k/мес"},
        {"name": "AI-контент", "trend": "🔥🔥", "competition": "Высокая", "potential": "$0.5-10k/мес"},
        {"name": "Онлайн-образование", "trend": "🔥🔥", "competition": "Высокая", "potential": "$1-50k/мес"},
        {"name": "Крипто/Web3", "trend": "🔥", "competition": "Высокая", "potential": "$1-100k/мес"},
    ]
    
    # Быстрые победы
    QUICK_WINS = [
        {
            "name": "AI-копирайтинг на Kwork",
            "income": "$300-1000/мес",
            "time": "3-7 дней",
            "steps": "1. Регистрация на Kwork → 2. Создай 5 услуг → 3. AI пишет тексты за тебя"
        },
        {
            "name": "Продажа Notion-шаблонов",
            "income": "$100-3000/мес", 
            "time": "1 неделя",
            "steps": "1. Создай шаблон в Notion → 2. Размести на Gumroad → 3. Продвигай в Twitter/Reddit"
        },
        {
            "name": "AI-дизайн на Fiverr",
            "income": "$500-2000/мес",
            "time": "1 неделя",
            "steps": "1. Освой Midjourney → 2. Создай портфолио → 3. Продавай на Fiverr"
        },
        {
            "name": "Telegram-бот на заказ",
            "income": "$500-3000/проект",
            "time": "1-2 недели",
            "steps": "1. Изучи aiogram → 2. Найди клиента → 3. Сделай бота (AI поможет с кодом)"
        },
        {
            "name": "AI-консультации",
            "income": "$1000-5000/мес",
            "time": "Сразу",
            "steps": "1. Упакуй свою экспертизу → 2. Calendly для записи → 3. LinkedIn/Telegram для клиентов"
        }
    ]
    
    @classmethod
    def get_income_method(cls, key: str) -> str:
        """Получить информацию о способе заработка"""
        data = cls.INCOME_METHODS.get(key)
        if not data:
            return None
        
        steps = "\n".join([f"   {i+1}. {s}" for i, s in enumerate(data["steps"])])
        
        return f"""{data['title']}

💰 *Доход:* {data['income']}
⏱ *Время до денег:* {data['time']}
🤖 *AI делает:* {data['ai_help']}

📝 *Описание:*
{data['description']}

🌐 *Платформы:* {data['platforms']}

📋 *Пошаговый план:*
{steps}

🎯 *ПЕРВЫЙ ШАГ:* {data['first_step']}"""
    
    @classmethod
    def get_all_methods_short(cls) -> str:
        """Краткий список всех способов"""
        text = "💰 *8 СПОСОБОВ ЗАРАБОТКА:*\n\n"
        for key, data in cls.INCOME_METHODS.items():
            text += f"*{data['title']}*\n"
            text += f"💵 {data['income']} | ⏱ {data['time']}\n"
            text += f"🤖 AI помогает на {data['ai_help']}\n\n"
        return text
    
    @classmethod
    def get_niches(cls) -> str:
        """Горячие ниши"""
        text = "🔥 *ГОРЯЧИЕ НИШИ 2024-2025:*\n\n"
        for n in cls.HOT_NICHES:
            text += f"*{n['name']}* {n['trend']}\n"
            text += f"   Конкуренция: {n['competition']}\n"
            text += f"   Потенциал: {n['potential']}\n\n"
        return text
    
    @classmethod
    def get_quick_wins(cls) -> str:
        """Быстрые победы"""
        text = "⚡ *БЫСТРЫЙ СТАРТ (деньги за 1-2 недели):*\n\n"
        for i, qw in enumerate(cls.QUICK_WINS, 1):
            text += f"*{i}. {qw['name']}*\n"
            text += f"💰 {qw['income']} | ⏱ {qw['time']}\n"
            text += f"📋 {qw['steps']}\n\n"
        return text
    
    @classmethod
    def generate_fallback_response(cls, query: str) -> str:
        """Генерация ответа без AI на основе ключевых слов"""
        q = query.lower()
        
        # Определяем тему
        if any(w in q for w in ["фриланс", "услуг", "навык"]):
            return cls.get_income_method("freelance")
        
        if any(w in q for w in ["бот", "telegram", "телеграм"]):
            return cls.get_income_method("bots")
        
        if any(w in q for w in ["ai", "ии", "нейросет", "искусственн"]):
            return cls.get_income_method("ai_services")
        
        if any(w in q for w in ["контент", "канал", "блог", "youtube"]):
            return cls.get_income_method("content")
        
        if any(w in q for w in ["автоматизац", "make", "zapier", "n8n"]):
            return cls.get_income_method("automation")
        
        if any(w in q for w in ["курс", "обучен", "инфопродукт", "гайд"]):
            return cls.get_income_method("digital")
        
        if any(w in q for w in ["партнёр", "affiliate", "реферал"]):
            return cls.get_income_method("affiliate")
        
        if any(w in q for w in ["товар", "dropship", "дропшип", "wildberries", "ozon"]):
            return cls.get_income_method("dropshipping")
        
        if any(w in q for w in ["ниша", "тренд", "что выбрать"]):
            return cls.get_niches()
        
        if any(w in q for w in ["быстро", "срочно", "неделю", "сейчас"]):
            return cls.get_quick_wins()
        
        # Дефолтный ответ - обзор всех способов
        return cls.get_all_methods_short() + "\n💡 _Напиши название способа для подробностей!_"

kb = KnowledgeBase()

# ═══════════════════════════════════════════════════════════════════════════
# СИСТЕМА АГЕНТОВ
# ═══════════════════════════════════════════════════════════════════════════

class Agent:
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
        q = query.lower()
        matches = sum(1 for kw in self.keywords if kw in q)
        return min(matches / max(len(self.keywords) * 0.25, 1), 1.0)
    
    async def analyze(self, task: str) -> Tuple[str, bool]:
        """Анализ задачи"""
        self.calls += 1
        
        system = f"Ты {self.name}, эксперт по {self.specialty}. Отвечай кратко, конкретно, с цифрами и примерами. Фокус на заработке."
        
        prompt = f"""Задача: {task}

Дай практичный ответ:
- Конкретные способы заработка
- Реальные цифры дохода  
- Пошаговые действия
- Первый шаг прямо сейчас"""
        
        result, success = await ai.generate(prompt, system=system)
        return result, success

class AgentSwarm:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._init_agents()
    
    def _init_agents(self):
        agents = [
            ("money", "Эксперт заработка", "💰", "монетизация и доход",
             ["заработок", "деньги", "доход", "монетизация", "прибыль", "бизнес"]),
            ("researcher", "Исследователь", "🔬", "анализ рынков",
             ["анализ", "исследование", "тренд", "рынок", "статистика"]),
            ("strategist", "Стратег", "🏗️", "стратегии",
             ["план", "стратегия", "roadmap", "этап", "развитие"]),
            ("content", "Контент-мейкер", "✍️", "создание контента",
             ["контент", "текст", "пост", "статья", "копирайт"]),
            ("coder", "Кодер", "💻", "программирование",
             ["код", "программа", "бот", "скрипт", "python", "автоматизация"]),
            ("marketer", "Маркетолог", "📢", "маркетинг",
             ["маркетинг", "реклама", "продвижение", "таргет", "трафик"]),
        ]
        
        for key, name, emoji, specialty, keywords in agents:
            self.agents[key] = Agent(name, emoji, specialty, keywords)
        
        log.info(f"✅ Загружено {len(self.agents)} агентов")
    
    def select(self, query: str, max_agents: int = 2) -> List[Agent]:
        """Выбор релевантных агентов"""
        scored = [(a, a.relevance(query)) for a in self.agents.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Всегда включаем money эксперта
        selected = [self.agents["money"]]
        
        for agent, score in scored:
            if len(selected) >= max_agents:
                break
            if agent not in selected and score > 0:
                selected.append(agent)
        
        return selected
    
    async def think(self, query: str) -> Tuple[str, List[str], bool]:
        """Коллективное мышление"""
        agents = self.select(query)
        
        responses = []
        agent_names = []
        any_success = False
        
        for agent in agents:
            response, success = await agent.analyze(query)
            if success and response:
                responses.append(f"[{agent.display}]: {response}")
                agent_names.append(agent.display)
                any_success = True
        
        if not any_success or not responses:
            # Fallback на базу знаний
            log.warn("⚠️ AI не ответил, используем базу знаний")
            fallback = kb.generate_fallback_response(query)
            return fallback, ["📚 База знаний"], True
        
        # Если только один агент ответил - возвращаем его ответ
        if len(responses) == 1:
            return responses[0].split("]: ", 1)[1], agent_names, True
        
        # Синтезируем ответы
        synthesis = await self._synthesize(query, responses)
        return synthesis, agent_names, True
    
    async def _synthesize(self, query: str, responses: List[str]) -> str:
        """Синтез ответов"""
        
        prompt = f"""Объедини ответы экспертов в один полезный ответ.

ВОПРОС: {query}

ОТВЕТЫ:
{chr(10).join(responses)}

Формат ответа:

🧠 *СУТЬ* (2-3 предложения)

💰 *КАК ЗАРАБОТАТЬ:*

*1. [Способ]* - $X/мес
• Что делаем
• AI помогает: X%  
• Первый шаг

*2. [Способ]* - $X/мес
• Аналогично

🎯 *НАЧНИ СЕЙЧАС:* [конкретное действие]

Кратко и по делу!"""
        
        result, success = await ai.generate(prompt, max_tokens=600)
        
        if success and result:
            return result
        
        # Fallback - просто объединяем
        return "\n\n---\n\n".join([r.split("]: ", 1)[1] if "]: " in r else r for r in responses])

swarm = AgentSwarm()

# ═══════════════════════════════════════════════════════════════════════════
# ГЕНЕРАТОР ДЕЙСТВИЙ
# ═══════════════════════════════════════════════════════════════════════════

class ActionGenerator:
    """Генератор действий с надёжным хранением"""
    
    def __init__(self):
        # Хранение с более длинным сроком жизни
        self.actions_store: Dict[str, Dict] = {}
        self.user_last_query: Dict[int, str] = {}
        self.user_last_response: Dict[int, str] = {}
    
    def generate(self, query: str, user_id: int) -> List[Dict]:
        """Генерация действий"""
        actions = []
        q = query.lower()
        
        # Всегда добавляем план
        actions.append({
            "type": "plan",
            "name": "📋 Пошаговый план",
            "desc": f"Детальный план: {query[:40]}"
        })
        
        if any(w in q for w in ["контент", "текст", "пост", "статья"]):
            actions.append({
                "type": "content",
                "name": "✍️ Создать контент",
                "desc": f"Готовый контент: {query[:35]}"
            })
        
        if any(w in q for w in ["код", "бот", "скрипт", "программ", "python"]):
            actions.append({
                "type": "code",
                "name": "💻 Написать код",
                "desc": f"Рабочий код: {query[:35]}"
            })
        
        if any(w in q for w in ["идея", "ниша", "придумай", "что делать"]):
            actions.append({
                "type": "ideas",
                "name": "💡 10 идей",
                "desc": f"Идеи: {query[:40]}"
            })
        
        if any(w in q for w in ["заработ", "доход", "деньги", "$", "долларов"]):
            actions.append({
                "type": "calc",
                "name": "🧮 Расчёт дохода",
                "desc": "Калькулятор потенциального дохода"
            })
        
        return actions[:4]
    
    def save_context(self, user_id: int, query: str, response: str, actions: List[Dict]):
        """Сохранение контекста"""
        self.user_last_query[user_id] = query
        self.user_last_response[user_id] = response
        
        # Создаём уникальные ключи для действий
        for i, action in enumerate(actions):
            key = f"act_{i}_{user_id}"
            self.actions_store[key] = {
                "action": action,
                "query": query,
                "response": response[:800],
                "timestamp": time.time()
            }
        
        # Чистим старые действия (старше 1 часа)
        self._cleanup()
    
    def get_action(self, key: str) -> Optional[Dict]:
        """Получение действия"""
        return self.actions_store.get(key)
    
    def _cleanup(self):
        """Очистка старых действий"""
        now = time.time()
        old_keys = [
            k for k, v in self.actions_store.items()
            if now - v.get("timestamp", 0) > 3600  # 1 час
        ]
        for k in old_keys:
            del self.actions_store[k]
    
    async def execute(self, key: str) -> Tuple[str, bool]:
        """Выполнение действия"""
        data = self.get_action(key)
        
        if not data:
            return "⚠️ Действие не найдено. Задай новый вопрос.", False
        
        action = data["action"]
        query = data["query"]
        response = data["response"]
        
        action_type = action.get("type", "plan")
        desc = action.get("desc", "")
        
        prompts = {
            "plan": f"""Создай детальный пошаговый план.

Тема: {desc}
Контекст: {query}

Формат:

📅 *НЕДЕЛЯ 1:*
День 1-2: [конкретные действия]
День 3-4: [конкретные действия]
День 5-7: [конкретные действия]

📅 *НЕДЕЛЯ 2-4:*
[следующие шаги]

💰 *ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:*
- Доход: $X/мес
- Сроки: когда первые деньги

🎯 *НАЧНИ СЕЙЧАС:* [первое действие]""",

            "content": f"""Создай готовый контент для публикации.

Тема: {desc}

Включи:
1. Заголовок (цепляющий)
2. Текст (300-500 слов)
3. Призыв к действию
4. 5-7 хештегов

Контент должен быть готов к публикации!""",

            "code": f"""Напиши рабочий Python код.

Задача: {desc}
Контекст: {query}

Требования:
- Полностью рабочий код
- Комментарии на русском
- Обработка ошибок
- Пример использования

Код:""",

            "ideas": f"""Сгенерируй 10 идей для заработка.

Тема: {desc}
Контекст: {query}

Для каждой идеи:

*1. [Название идеи]*
💰 Потенциал: $X/мес
⏱ Время до результата: X недель
🎯 Первый шаг: [конкретное действие]

[И так далее для всех 10 идей]""",

            "calc": f"""Рассчитай потенциальный доход.

Тема: {query}

📊 *РАСЧЁТ ДОХОДА:*

*Консервативный сценарий:*
- Часов в неделю: X
- Ставка: $X/час
- Месячный доход: $X

*Реалистичный сценарий:*
- При масштабировании: $X/мес
- Время достижения: X месяцев

*Оптимистичный сценарий:*
- Потолок: $X/мес
- Что нужно: [условия]

🎯 *РЕКОМЕНДАЦИЯ:* [что делать]"""
        }
        
        prompt = prompts.get(action_type, prompts["plan"])
        
        result, success = await ai.generate(prompt, max_tokens=800)
        
        if success and result:
            return result, True
        
        # Fallback
        return kb.generate_fallback_response(query), True

actions = ActionGenerator()

# ═══════════════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════════════════

class Statistics:
    def __init__(self):
        self.start_time = datetime.now()
        self.queries = 0
        self.tasks = 0
        self.errors = 0
        self.users = set()
    
    def record_query(self, user_id: int):
        self.queries += 1
        self.users.add(user_id)
    
    def record_task(self):
        self.tasks += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_summary(self) -> str:
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        return f"""📊 *СТАТИСТИКА DEEPTHINK v4.0*

⏱ Время работы: {hours:.1f} часов
👥 Пользователей: {len(self.users)}
💬 Запросов: {self.queries}
✅ Задач выполнено: {self.tasks}
❌ Ошибок: {self.errors}

🤖 *Агенты:*
{chr(10).join([f"• {a.display}: {a.calls} вызовов" for a in swarm.agents.values()])}

{ai.get_stats()}
🔧 Модель: {ai._get_model().split('/')[1][:25]}"""

stats = Statistics()

# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════

class TelegramBot:
    def __init__(self):
        self.api = cfg.TELEGRAM_API
    
    async def send(self, chat_id: int, text: str, buttons: Dict = None):
        """Отправка сообщения"""
        async with httpx.AsyncClient(timeout=30) as client:
            data = {
                "chat_id": chat_id,
                "text": text[:4096],
                "parse_mode": "Markdown"
            }
            
            if buttons:
                data["reply_markup"] = json.dumps(buttons)
            
            try:
                resp = await client.post(f"{self.api}/sendMessage", json=data)
                if resp.status_code != 200:
                    # Попробуем без Markdown
                    data.pop("parse_mode")
                    await client.post(f"{self.api}/sendMessage", json=data)
            except Exception as e:
                log.error(f"Send error: {e}")
    
    async def answer_callback(self, callback_id: str, text: str = None):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                payload = {"callback_query_id": callback_id}
                if text:
                    payload["text"] = text[:200]
                await client.post(f"{self.api}/answerCallbackQuery", json=payload)
            except:
                pass
    
    async def typing(self, chat_id: int):
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(
                    f"{self.api}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"}
                )
            except:
                pass
    
    def make_buttons(self, action_list: List[Dict], user_id: int) -> Dict:
        """Создание кнопок"""
        keyboard = []
        
        for i, act in enumerate(action_list):
            keyboard.append([{
                "text": act.get("name", "🤖 Действие")[:30],
                "callback_data": f"act_{i}_{user_id}"
            }])
        
        # Быстрые команды
        keyboard.append([
            {"text": "💰 Все способы", "callback_data": f"income_{user_id}"},
            {"text": "🔥 Ниши", "callback_data": f"niches_{user_id}"}
        ])
        keyboard.append([
            {"text": "⚡ Быстрый старт", "callback_data": f"quick_{user_id}"},
            {"text": "📊 Статистика", "callback_data": f"stats_{user_id}"}
        ])
        
        return {"inline_keyboard": keyboard}
    
    def make_income_buttons(self) -> Dict:
        """Кнопки способов заработка"""
        keyboard = []
        for key, data in kb.INCOME_METHODS.items():
            keyboard.append([{
                "text": data["title"],
                "callback_data": f"method_{key}"
            }])
        return {"inline_keyboard": keyboard}
    
    # ═══════════════════════════════════════════════════════════════
    # КОМАНДЫ
    # ═══════════════════════════════════════════════════════════════
    
    async def cmd_start(self, chat_id: int, name: str):
        text = f"""🧠 *DEEPTHINK AUTOHUSTLE v4.0*

Привет, {name}! 👋

Я - AI-система для поиска способов заработка.

🤖 *6 AI-АГЕНТОВ* анализируют запросы
📚 *8 СПОСОБОВ* заработка в базе
💰 *$100 - $100,000/мес* потенциал

🚀 *ПРИМЕРЫ ЗАПРОСОВ:*
• "Как заработать на AI?"
• "Создай Telegram-бота"
• "План на $1000/мес"
• "Идеи для пассивного дохода"

📖 /help - все команды

💡 *Просто напиши свой вопрос!*"""
        await self.send(chat_id, text)
    
    async def cmd_help(self, chat_id: int):
        text = """📖 *КОМАНДЫ:*

*Заработок:*
/income - 8 способов заработка
/niches - Горячие ниши 2024-2025
/quick - Быстрый старт (деньги за неделю)

*Инструменты:*
/plan [тема] - Пошаговый план
/ideas [тема] - 10 идей
/code [задача] - Написать код

*Система:*
/stats - Статистика бота
/agents - Список агентов

💡 *Или просто напиши вопрос!*"""
        await self.send(chat_id, text)
    
    async def cmd_income(self, chat_id: int):
        text = kb.get_all_methods_short()
        text += "\n_Нажми на способ для подробностей:_"
        buttons = self.make_income_buttons()
        await self.send(chat_id, text, buttons)
    
    async def cmd_niches(self, chat_id: int):
        await self.send(chat_id, kb.get_niches())
    
    async def cmd_quick(self, chat_id: int):
        await self.send(chat_id, kb.get_quick_wins())
    
    async def cmd_stats(self, chat_id: int):
        await self.send(chat_id, stats.get_summary())
    
    async def cmd_agents(self, chat_id: int):
        text = f"🤖 *{len(swarm.agents)} AI-АГЕНТОВ:*\n\n"
        for agent in swarm.agents.values():
            text += f"{agent.display}\n"
            text += f"   Специализация: {agent.specialty}\n"
            text += f"   Вызовов: {agent.calls}\n\n"
        await self.send(chat_id, text)
    
    # ═══════════════════════════════════════════════════════════════
    # ОБРАБОТКА СООБЩЕНИЙ
    # ═══════════════════════════════════════════════════════════════
    
    async def handle_message(self, chat_id: int, user_id: int, text: str, name: str):
        """Обработка сообщения"""
        stats.record_query(user_id)
        
        # Обработка команд с параметрами
        if text.startswith("/plan "):
            query = text[6:].strip()
            if query:
                text = f"Создай план: {query}"
        elif text.startswith("/ideas "):
            query = text[7:].strip()
            if query:
                text = f"Придумай 10 идей: {query}"
        elif text.startswith("/code "):
            query = text[6:].strip()
            if query:
                text = f"Напиши код: {query}"
        
        await self.typing(chat_id)
        
        # Отправляем статус
        await self.send(chat_id,
            "🧠 *ДУМАЮ...*\n\n"
            "🤖 Агенты анализируют запрос...\n"
            "💰 Ищу способы заработка..."
        )
        
        start_time = time.time()
        
        try:
            # Думаем
            response, agent_names, success = await swarm.think(text)
            
            if not success or not response:
                # Fallback на базу знаний
                response = kb.generate_fallback_response(text)
                agent_names = ["📚 База знаний"]
            
            # Генерируем действия
            action_list = actions.generate(text, user_id)
            
            # Сохраняем контекст
            actions.save_context(user_id, text, response, action_list)
            
            elapsed = time.time() - start_time
            
            # Формируем ответ
            agents_str = ", ".join(agent_names[:3]) if agent_names else "📚 База знаний"
            footer = f"\n\n---\n👥 _{agents_str}_\n⏱ _{elapsed:.1f}с_"
            
            full_response = response + footer
            buttons = self.make_buttons(action_list, user_id)
            
            await self.send(chat_id, full_response[:4096], buttons)
            
        except Exception as e:
            stats.record_error()
            log.error(f"Handle error: {str(e)}")
            
            # Fallback ответ
            fallback = kb.generate_fallback_response(text)
            await self.send(chat_id, fallback)
    
    async def handle_callback(self, callback_id: str, chat_id: int, user_id: int, data: str):
        """Обработка callback"""
        await self.answer_callback(callback_id)
        
        # Способы заработка
        if data.startswith("income_"):
            await self.cmd_income(chat_id)
            return
        
        if data.startswith("niches_"):
            await self.cmd_niches(chat_id)
            return
        
        if data.startswith("quick_"):
            await self.cmd_quick(chat_id)
            return
        
        if data.startswith("stats_"):
            await self.cmd_stats(chat_id)
            return
        
        # Конкретный способ заработка
        if data.startswith("method_"):
            method_key = data[7:]
            info = kb.get_income_method(method_key)
            if info:
                await self.send(chat_id, info)
            else:
                await self.send(chat_id, "⚠️ Способ не найден")
            return
        
        # Выполнение действия
        if data.startswith("act_"):
            await self.typing(chat_id)
            
            action_data = actions.get_action(data)
            
            if not action_data:
                # Пробуем получить из последнего запроса пользователя
                last_query = actions.user_last_query.get(user_id)
                if last_query:
                    await self.send(chat_id, 
                        "🔄 Действие устарело, но я помню твой запрос!\n\n"
                        "Отправляю новый анализ..."
                    )
                    await self.handle_message(chat_id, user_id, last_query, "User")
                else:
                    await self.send(chat_id, 
                        "⚠️ Действие устарело.\n\n"
                        "💡 Задай новый вопрос или выбери способ заработка:",
                        self.make_income_buttons()
                    )
                return
            
            action = action_data["action"]
            await self.send(chat_id, f"⚙️ Выполняю: {action.get('name', 'действие')}...")
            
            try:
                result, success = await actions.execute(data)
                
                if success:
                    stats.record_task()
                
                # Разбиваем длинный ответ
                if len(result) > 4000:
                    parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
                    for i, part in enumerate(parts):
                        prefix = f"📄 *Часть {i+1}/{len(parts)}:*\n\n" if len(parts) > 1 else "✅ *Готово!*\n\n"
                        await self.send(chat_id, prefix + part)
                else:
                    await self.send(chat_id, f"✅ *Готово!*\n\n{result}")
                    
            except Exception as e:
                log.error(f"Action error: {e}")
                await self.send(chat_id, f"⚠️ Ошибка выполнения. Попробуй ещё раз.")
    
    async def handle_update(self, update: Dict):
        """Обработка обновления"""
        try:
            # Сообщения
            if "message" in update:
                msg = update["message"]
                
                if "text" not in msg:
                    return
                
                chat_id = msg["chat"]["id"]
                user = msg.get("from", {})
                user_id = user.get("id", 0)
                name = user.get("first_name", "User")
                text = msg["text"]
                
                log.info(f"📩 [{user_id}] {text[:50]}...")
                
                # Команды
                if text == "/start":
                    await self.cmd_start(chat_id, name)
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
                    # Команды с параметрами или неизвестные
                    if any(text.startswith(cmd) for cmd in ["/plan ", "/ideas ", "/code "]):
                        await self.handle_message(chat_id, user_id, text, name)
                    else:
                        await self.send(chat_id, "❓ Неизвестная команда. Напиши /help")
                else:
                    await self.handle_message(chat_id, user_id, text, name)
            
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
            stats.record_error()
            log.error(f"Update error: {str(e)}")
    
    async def run(self):
        """Запуск бота"""
        log.info("=" * 50)
        log.info("🧠 DEEPTHINK AUTOHUSTLE v4.0")
        log.info("🛡️ BULLETPROOF EDITION")
        log.info("=" * 50)
        log.info(f"🤖 Агентов: {len(swarm.agents)}")
        log.info(f"📚 Способов заработка: {len(kb.INCOME_METHODS)}")
        log.info(f"🔧 Модель: {ai._get_model()}")
        log.info("=" * 50)
        
        offset = 0
        consecutive_errors = 0
        
        async with httpx.AsyncClient(timeout=cfg.TIMEOUT) as client:
            log.info("✅ БОТ ЗАПУЩЕН!")
            
            while True:
                try:
                    resp = await client.get(
                        f"{self.api}/getUpdates",
                        params={"offset": offset, "timeout": 30}
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        if data.get("ok") and data.get("result"):
                            for update in data["result"]:
                                offset = update["update_id"] + 1
                                asyncio.create_task(self.handle_update(update))
                        
                        consecutive_errors = 0
                    else:
                        log.warn(f"Telegram API error: {resp.status_code}")
                        consecutive_errors += 1
                
                except httpx.TimeoutException:
                    # Timeout это нормально для long polling
                    continue
                    
                except Exception as e:
                    consecutive_errors += 1
                    log.error(f"Polling error: {e}")
                    
                    if consecutive_errors > 10:
                        log.error("Слишком много ошибок, перезапуск через 30с...")
                        await asyncio.sleep(30)
                        consecutive_errors = 0
                    else:
                        await asyncio.sleep(5)

# ═══════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    print("\n" + "=" * 60)
    print("🧠 DEEPTHINK AUTOHUSTLE v4.0")
    print("🛡️ BULLETPROOF EDITION")
    print("💰 ULTIMATE MONEY MACHINE")
    print("=" * 60 + "\n")
    
    bot = TelegramBot()
    await bot.run()

def run():
    # Health check сервер в отдельном потоке
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
