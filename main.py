"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DEEPTHINK v5.0 - ENTERPRISE EDITION                       ║
║                                                                              ║
║  🧠 НАСТОЯЩИЙ AI-МОЗГ - отвечает на ЛЮБОЙ вопрос                             ║
║  👥 30+ АГЕНТОВ - профессиональная команда                                   ║
║  🌐 WEB SEARCH - поиск информации в интернете                                ║
║  🔄 МУЛЬТИ-АГЕНТНАЯ СИСТЕМА - агенты общаются между собой                    ║
║  📁 ФАЙЛЫ И ССЫЛКИ - источники информации                                    ║
║  ⚡ 99% АВТОМАТИЗАЦИЯ - сами решают проблемы                                 ║
║                                                                              ║
║  Production Ready | Render.com | Commercial Grade                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import threading
import time
import hashlib
import re
import random
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from abc import ABC, abstractmethod
import html

# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        status = {
            "status": "running",
            "version": "5.0",
            "agents": 30,
            "uptime": str(datetime.now())
        }
        self.wfile.write(json.dumps(status).encode())
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"[HEALTH] Port {port} ready")
    server.serve_forever()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    COLORS = {
        'INFO': '\033[92m',
        'WARN': '\033[93m', 
        'ERROR': '\033[91m',
        'DEBUG': '\033[94m',
        'AGENT': '\033[95m',
        'RESET': '\033[0m'
    }
    
    @staticmethod
    def log(msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = Logger.COLORS.get(level, '')
        reset = Logger.COLORS['RESET']
        print(f"[{ts}] {color}[{level}]{reset} {msg}", flush=True)
    
    @staticmethod
    def info(msg): Logger.log(msg, "INFO")
    @staticmethod
    def error(msg): Logger.log(msg, "ERROR")
    @staticmethod
    def warn(msg): Logger.log(msg, "WARN")
    @staticmethod
    def debug(msg): Logger.log(msg, "DEBUG")
    @staticmethod
    def agent(msg): Logger.log(msg, "AGENT")

log = Logger()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # API Keys
    TELEGRAM_TOKEN = os.environ.get(
        'TELEGRAM_TOKEN',
        '8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY'
    )
    
    OPENROUTER_KEY = os.environ.get(
        'OPENROUTER_KEY',
        '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'
    )
    
    # Working FREE models (tested and verified)
    MODELS = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "openchat/openchat-7b:free",
    ]
    
    # Limits
    MAX_TOKENS = 1000
    TIMEOUT = 60
    MAX_RETRIES = 5
    
    # Agent settings
    MAX_AGENTS_PER_TASK = 5
    ENABLE_WEB_SEARCH = True
    
    @property
    def TELEGRAM_API(self):
        return f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}"

cfg = Config()

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

log.info("🚀 DeepThink v5.0 Enterprise загружается...")

try:
    import httpx
    log.info("✅ httpx loaded")
except ImportError:
    log.error("❌ httpx not found")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# WEB SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class WebSearchEngine:
    """Поисковый движок - ищет информацию в интернете"""
    
    def __init__(self):
        self.cache: Dict[str, Tuple[List[Dict], float]] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Поиск в интернете через DuckDuckGo"""
        
        # Проверяем кэш
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.cache:
            results, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                log.debug(f"🔍 Cache hit: {query[:30]}...")
                return results
        
        try:
            # DuckDuckGo Instant Answer API
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Abstract
                    if data.get("Abstract"):
                        results.append({
                            "title": data.get("Heading", "Информация"),
                            "snippet": data["Abstract"],
                            "url": data.get("AbstractURL", ""),
                            "source": data.get("AbstractSource", "DuckDuckGo")
                        })
                    
                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:num_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({
                                "title": topic.get("Text", "")[:100],
                                "snippet": topic.get("Text", ""),
                                "url": topic.get("FirstURL", ""),
                                "source": "DuckDuckGo"
                            })
                    
                    # Кэшируем
                    self.cache[cache_key] = (results, time.time())
                    
                    log.info(f"🌐 Найдено {len(results)} результатов: {query[:30]}...")
                    return results
                    
        except Exception as e:
            log.warn(f"⚠️ Search error: {str(e)[:50]}")
        
        return []
    
    async def get_page_content(self, url: str, max_length: int = 2000) -> Optional[str]:
        """Получить содержимое страницы"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    # Простая очистка HTML
                    text = response.text
                    # Убираем теги
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = html.unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:max_length]
        except:
            pass
        return None

web_search = WebSearchEngine()

# ═══════════════════════════════════════════════════════════════════════════════
# AI ENGINE - DIRECT HTTP REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

class AIEngine:
    """AI движок с прямыми HTTP запросами к OpenRouter"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_index = 0
        self.stats = {"requests": 0, "success": 0, "errors": 0}
        self.last_working_model = None
    
    def _get_model(self) -> str:
        if self.last_working_model:
            return self.last_working_model
        return cfg.MODELS[self.model_index % len(cfg.MODELS)]
    
    def _rotate_model(self):
        self.model_index += 1
        self.last_working_model = None
    
    async def think(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = None,
        temperature: float = 0.7
    ) -> Tuple[str, bool]:
        """Главный метод мышления AI"""
        
        max_tokens = max_tokens or cfg.MAX_TOKENS
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(len(cfg.MODELS)):
            model = self._get_model()
            
            headers = {
                "Authorization": f"Bearer {cfg.OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://deepthink.ai",
                "X-Title": "DeepThink v5.0"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            try:
                self.stats["requests"] += 1
                
                async with httpx.AsyncClient(timeout=cfg.TIMEOUT) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0]["message"]["content"]
                        self.stats["success"] += 1
                        self.last_working_model = model
                        return content, True
                
                elif response.status_code in [402, 429]:
                    self._rotate_model()
                    continue
                else:
                    self._rotate_model()
                    continue
                    
            except Exception as e:
                self.stats["errors"] += 1
                self._rotate_model()
                continue
        
        return None, False

ai = AIEngine()

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT SYSTEM - 30+ SPECIALIZED AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentProfile:
    """Профиль агента"""
    id: str
    name: str
    emoji: str
    role: str
    expertise: List[str]
    personality: str
    thinking_style: str

class BaseAgent(ABC):
    """Базовый класс агента"""
    
    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.calls = 0
        self.successful_calls = 0
    
    @property
    def display_name(self) -> str:
        return f"{self.profile.emoji} {self.profile.name}"
    
    def get_system_prompt(self) -> str:
        """Системный промпт агента"""
        return f"""Ты - {self.profile.name}, {self.profile.role}.

ТВОЯ ЭКСПЕРТИЗА: {', '.join(self.profile.expertise)}

ХАРАКТЕР: {self.profile.personality}

СТИЛЬ МЫШЛЕНИЯ: {self.profile.thinking_style}

ВАЖНЫЕ ПРАВИЛА:
1. Ты ДУМАЕШЬ над каждым вопросом индивидуально
2. НЕ используй шаблонные ответы
3. Анализируй контекст и давай уникальный ответ
4. Приводи конкретные примеры и цифры
5. Если не знаешь - скажи честно, но предложи как узнать
6. Отвечай на русском языке
7. Будь полезным и практичным"""
    
    async def think(self, task: str, context: str = "") -> Tuple[str, bool]:
        """Размышление над задачей"""
        self.calls += 1
        
        prompt = task
        if context:
            prompt = f"КОНТЕКСТ:\n{context}\n\nЗАДАЧА:\n{task}"
        
        result, success = await ai.think(
            prompt=prompt,
            system=self.get_system_prompt(),
            temperature=0.8
        )
        
        if success:
            self.successful_calls += 1
            log.agent(f"{self.display_name} ответил")
        
        return result, success
    
    def relevance_score(self, query: str) -> float:
        """Оценка релевантности агента для запроса"""
        query_lower = query.lower()
        score = 0.0
        
        for expertise in self.profile.expertise:
            if expertise.lower() in query_lower:
                score += 0.3
        
        # Проверяем ключевые слова в роли
        role_words = self.profile.role.lower().split()
        for word in role_words:
            if len(word) > 3 and word in query_lower:
                score += 0.1
        
        return min(score, 1.0)

class ResearchAgent(BaseAgent):
    """Агент-исследователь с поиском в интернете"""
    
    async def research(self, query: str) -> Tuple[str, List[str], bool]:
        """Исследование с поиском в интернете"""
        self.calls += 1
        sources = []
        
        # Поиск в интернете
        search_results = await web_search.search(query, num_results=5)
        
        # Формируем контекст из результатов поиска
        search_context = ""
        if search_results:
            search_context = "\n\n📚 НАЙДЕННАЯ ИНФОРМАЦИЯ:\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"\n{i}. {result['title']}\n"
                search_context += f"   {result['snippet'][:300]}\n"
                if result.get('url'):
                    sources.append(result['url'])
                    search_context += f"   🔗 {result['url']}\n"
        
        prompt = f"""Исследуй тему и дай подробный ответ.

ЗАПРОС: {query}
{search_context}

Дай информативный, точный ответ на основе найденной информации.
Если информации недостаточно - используй свои знания.
Указывай факты и цифры где возможно."""

        result, success = await ai.think(
            prompt=prompt,
            system=self.get_system_prompt(),
            max_tokens=1200
        )
        
        if success:
            self.successful_calls += 1
        
        return result, sources, success

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT TEAM - 30 AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

class AgentTeam:
    """Команда из 30+ агентов"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.researcher: ResearchAgent = None
        self._init_agents()
    
    def _init_agents(self):
        """Инициализация всех агентов"""
        
        profiles = [
            # 🧠 МОЗГОВОЙ ЦЕНТР
            AgentProfile("coordinator", "Координатор", "🎯", 
                "Главный координатор команды, распределяет задачи",
                ["управление", "координация", "анализ задач", "планирование"],
                "Организованный, стратегический мыслитель",
                "Сначала анализирует задачу, потом распределяет"),
            
            AgentProfile("analyst", "Главный Аналитик", "📊",
                "Глубокий анализ данных и ситуаций",
                ["аналитика", "данные", "статистика", "исследования", "метрики"],
                "Дотошный, любит цифры и факты",
                "Всегда ищет данные и доказательства"),
            
            AgentProfile("researcher", "Исследователь", "🔬",
                "Поиск и анализ информации из интернета",
                ["исследования", "поиск", "информация", "факты", "источники"],
                "Любознательный, всегда докапывается до истины",
                "Ищет в интернете, проверяет факты"),
            
            # 💰 БИЗНЕС И ДЕНЬГИ
            AgentProfile("business", "Бизнес-стратег", "💼",
                "Бизнес-стратегии и развитие компаний",
                ["бизнес", "стратегия", "компания", "развитие", "рост"],
                "Прагматичный, ориентирован на результат",
                "Думает о прибыли и масштабировании"),
            
            AgentProfile("money", "Эксперт по заработку", "💰",
                "Способы заработка и монетизации",
                ["заработок", "деньги", "доход", "монетизация", "прибыль"],
                "Знает 100 способов заработать",
                "Всегда ищет возможности для дохода"),
            
            AgentProfile("investor", "Инвестор", "📈",
                "Инвестиции, финансы, активы",
                ["инвестиции", "акции", "криптовалюта", "портфель", "риски"],
                "Осторожный, считает риски",
                "Анализирует доходность и риски"),
            
            AgentProfile("startup", "Стартап-эксперт", "🚀",
                "Запуск стартапов и новых проектов",
                ["стартап", "mvp", "запуск", "идея", "венчур"],
                "Энергичный, любит новое",
                "Думает о быстром запуске и проверке гипотез"),
            
            AgentProfile("ecommerce", "E-commerce эксперт", "🛒",
                "Онлайн-торговля и маркетплейсы",
                ["магазин", "товары", "wildberries", "ozon", "продажи"],
                "Практик онлайн-торговли",
                "Знает все о продажах в интернете"),
            
            # 💻 ТЕХНОЛОГИИ
            AgentProfile("developer", "Ведущий разработчик", "💻",
                "Программирование и разработка ПО",
                ["код", "программирование", "python", "javascript", "разработка"],
                "Опытный кодер, пишет чистый код",
                "Сначала архитектура, потом код"),
            
            AgentProfile("architect", "Архитектор систем", "🏗️",
                "Проектирование IT-систем",
                ["архитектура", "система", "база данных", "api", "микросервисы"],
                "Видит картину целиком",
                "Проектирует масштабируемые системы"),
            
            AgentProfile("devops", "DevOps инженер", "⚙️",
                "Инфраструктура и деплой",
                ["devops", "docker", "kubernetes", "ci/cd", "облако"],
                "Автоматизирует всё",
                "Думает о надёжности и автоматизации"),
            
            AgentProfile("ai_expert", "AI/ML эксперт", "🤖",
                "Искусственный интеллект и машинное обучение",
                ["ai", "ml", "нейросеть", "gpt", "машинное обучение", "gemini", "chatgpt"],
                "Живёт в мире AI",
                "Знает все модели и их возможности"),
            
            AgentProfile("security", "Эксперт по безопасности", "🔐",
                "Кибербезопасность и защита данных",
                ["безопасность", "хакер", "защита", "пароль", "шифрование"],
                "Параноик в хорошем смысле",
                "Всегда думает об уязвимостях"),
            
            AgentProfile("blockchain", "Блокчейн эксперт", "🔗",
                "Криптовалюты и блокчейн технологии",
                ["крипто", "блокчейн", "web3", "nft", "биткоин", "ethereum"],
                "Крипто-энтузиаст",
                "Видит будущее в децентрализации"),
            
            AgentProfile("mobile", "Мобильный разработчик", "📱",
                "Разработка мобильных приложений",
                ["мобильное", "ios", "android", "приложение", "flutter"],
                "Любит мобильные технологии",
                "Думает о UX на маленьком экране"),
            
            AgentProfile("automation", "Автоматизатор", "🔄",
                "Автоматизация процессов",
                ["автоматизация", "zapier", "make", "n8n", "бот"],
                "Ненавидит рутину",
                "Автоматизирует всё что можно"),
            
            # 📢 МАРКЕТИНГ
            AgentProfile("marketer", "Маркетолог", "📢",
                "Маркетинг и продвижение",
                ["маркетинг", "реклама", "продвижение", "бренд", "pr"],
                "Креативный, знает тренды",
                "Думает о целевой аудитории"),
            
            AgentProfile("smm", "SMM специалист", "📱",
                "Социальные сети и контент",
                ["instagram", "tiktok", "youtube", "соцсети", "контент"],
                "Живёт в соцсетях",
                "Знает все алгоритмы платформ"),
            
            AgentProfile("seo", "SEO специалист", "🔍",
                "Поисковая оптимизация",
                ["seo", "google", "яндекс", "ключевые слова", "поиск"],
                "Понимает поисковые алгоритмы",
                "Думает о ранжировании"),
            
            AgentProfile("copywriter", "Копирайтер", "✍️",
                "Продающие и информационные тексты",
                ["текст", "копирайтинг", "статья", "продающий", "контент"],
                "Мастер слова",
                "Пишет убедительные тексты"),
            
            AgentProfile("targetolog", "Таргетолог", "🎯",
                "Таргетированная реклама",
                ["таргет", "реклама", "facebook", "vk", "аудитория"],
                "Точно попадает в цель",
                "Анализирует аудитории"),
            
            # 🎨 КРЕАТИВ
            AgentProfile("creative", "Креативный директор", "🎨",
                "Креативные идеи и концепции",
                ["креатив", "идея", "концепция", "дизайн", "бренд"],
                "Генератор идей",
                "Мыслит нестандартно"),
            
            AgentProfile("ux", "UX/UI дизайнер", "🖼️",
                "Дизайн интерфейсов",
                ["дизайн", "ux", "ui", "интерфейс", "figma"],
                "Заботится о пользователе",
                "Думает о удобстве"),
            
            # 📚 ОБРАЗОВАНИЕ
            AgentProfile("teacher", "Преподаватель", "👨‍🏫",
                "Обучение и объяснение сложного",
                ["обучение", "курс", "урок", "объяснить", "научить"],
                "Терпеливый, умеет объяснять",
                "Разбивает сложное на простое"),
            
            AgentProfile("mentor", "Ментор", "🧙‍♂️",
                "Наставничество и развитие",
                ["ментор", "развитие", "карьера", "рост", "навыки"],
                "Мудрый наставник",
                "Помогает найти путь"),
            
            # 🧠 ПСИХОЛОГИЯ
            AgentProfile("psychologist", "Психолог", "🧠",
                "Психология и мотивация",
                ["психология", "мотивация", "привычки", "стресс", "продуктивность"],
                "Понимает людей",
                "Анализирует поведение"),
            
            AgentProfile("coach", "Коуч", "💪",
                "Достижение целей",
                ["цели", "мотивация", "план", "успех", "дисциплина"],
                "Вдохновляет на действия",
                "Помогает достигать целей"),
            
            # ⚖️ ПРАВО И ФИНАНСЫ
            AgentProfile("lawyer", "Юрист", "⚖️",
                "Правовые вопросы",
                ["закон", "договор", "право", "юридический", "суд"],
                "Точный, знает законы",
                "Всегда проверяет риски"),
            
            AgentProfile("accountant", "Финансист", "🧮",
                "Финансы и учёт",
                ["финансы", "налоги", "бухгалтерия", "бюджет", "учёт"],
                "Любит цифры",
                "Считает каждую копейку"),
            
            # 🌍 ЯЗЫКИ
            AgentProfile("translator", "Переводчик", "🌍",
                "Переводы и локализация",
                ["перевод", "английский", "язык", "локализация"],
                "Знает много языков",
                "Передаёт смысл, не только слова"),
            
            # 🔧 SUPPORT
            AgentProfile("support", "Техподдержка", "🛠️",
                "Решение проблем и ошибок",
                ["ошибка", "проблема", "не работает", "помощь", "баг"],
                "Терпеливый решатель проблем",
                "Находит причину и решение"),
            
            AgentProfile("qa", "QA инженер", "🧪",
                "Тестирование и качество",
                ["тест", "баг", "качество", "проверка"],
                "Находит все баги",
                "Тестирует всё"),
        ]
        
        for profile in profiles:
            if profile.id == "researcher":
                agent = ResearchAgent(profile)
                self.researcher = agent
            else:
                agent = BaseAgent(profile)
            self.agents[profile.id] = agent
        
        log.info(f"✅ Загружено {len(self.agents)} агентов")
    
    def select_agents(self, query: str, max_agents: int = None) -> List[BaseAgent]:
        """Умный выбор агентов для задачи"""
        max_agents = max_agents or cfg.MAX_AGENTS_PER_TASK
        
        # Оцениваем релевантность каждого агента
        scored = []
        for agent in self.agents.values():
            score = agent.relevance_score(query)
            scored.append((agent, score))
        
        # Сортируем по релевантности
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Всегда включаем координатора и аналитика
        must_have = ["coordinator", "analyst"]
        selected = [self.agents[aid] for aid in must_have if aid in self.agents]
        
        # Добавляем релевантных
        for agent, score in scored:
            if len(selected) >= max_agents:
                break
            if agent not in selected:
                selected.append(agent)
        
        return selected[:max_agents]
    
    async def collaborative_think(
        self, 
        query: str, 
        use_web_search: bool = True
    ) -> Dict[str, Any]:
        """Коллаборативное мышление команды агентов"""
        
        start_time = time.time()
        
        results = {
            "query": query,
            "responses": [],
            "synthesis": "",
            "sources": [],
            "agents_used": [],
            "thinking_time": 0,
            "success": False
        }
        
        # 1. Исследователь ищет информацию (если нужно)
        research_context = ""
        if use_web_search and self.researcher:
            log.agent("🔬 Исследователь ищет информацию...")
            research_result, sources, success = await self.researcher.research(query)
            if success and research_result:
                research_context = f"\n\n📚 РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:\n{research_result}"
                results["sources"] = sources
                results["responses"].append({
                    "agent": self.researcher.display_name,
                    "response": research_result,
                    "type": "research"
                })
                results["agents_used"].append(self.researcher.display_name)
        
        # 2. Выбираем релевантных агентов
        selected_agents = self.select_agents(query)
        log.agent(f"👥 Выбрано агентов: {len(selected_agents)}")
        
        # 3. Каждый агент думает (параллельно)
        tasks = []
        for agent in selected_agents:
            if agent.profile.id != "researcher":  # Исследователь уже работал
                task = agent.think(query, research_context)
                tasks.append((agent, task))
        
        # Выполняем параллельно
        for agent, task in tasks:
            try:
                response, success = await task
                if success and response:
                    results["responses"].append({
                        "agent": agent.display_name,
                        "response": response,
                        "type": "analysis"
                    })
                    results["agents_used"].append(agent.display_name)
            except Exception as e:
                log.error(f"Agent error {agent.profile.id}: {e}")
        
        # 4. Синтезируем ответы
        if results["responses"]:
            synthesis = await self._synthesize_responses(query, results["responses"], results["sources"])
            results["synthesis"] = synthesis
            results["success"] = True
        
        results["thinking_time"] = time.time() - start_time
        
        return results
    
    async def _synthesize_responses(
        self, 
        query: str, 
        responses: List[Dict],
        sources: List[str]
    ) -> str:
        """Синтез ответов от всех агентов"""
        
        # Собираем ответы
        responses_text = ""
        for r in responses:
            responses_text += f"\n\n[{r['agent']}]:\n{r['response']}"
        
        # Формируем источники
        sources_text = ""
        if sources:
            sources_text = "\n\n📎 ИСТОЧНИКИ:\n" + "\n".join([f"• {s}" for s in sources[:5]])
        
        synthesis_prompt = f"""Ты - главный координатор команды из 30 экспертов.

Твоя задача: объединить ответы экспертов в один ПОЛЕЗНЫЙ, ИНФОРМАТИВНЫЙ ответ.

ИСХОДНЫЙ ЗАПРОС: {query}

ОТВЕТЫ ЭКСПЕРТОВ:
{responses_text}
{sources_text}

ПРАВИЛА СИНТЕЗА:
1. Объедини все ценные мысли в единый структурированный ответ
2. Убери дублирования
3. Сохрани все важные детали, цифры, примеры
4. Добавь практические рекомендации
5. Если есть источники - включи их в конце

ФОРМАТ ОТВЕТА:

🧠 **ОТВЕТ:**
[Подробный, информативный ответ на вопрос]

📊 **КЛЮЧЕВЫЕ ФАКТЫ:**
[Если есть важные цифры/факты]

💡 **РЕКОМЕНДАЦИИ:**
[Практические советы]

🔗 **ИСТОЧНИКИ:**
[Если есть]

Пиши развёрнуто, информативно, без воды!"""

        result, success = await ai.think(
            prompt=synthesis_prompt,
            max_tokens=1500,
            temperature=0.7
        )
        
        if success and result:
            return result
        
        # Fallback - просто объединяем
        return "\n\n---\n\n".join([
            f"**{r['agent']}:**\n{r['response']}" 
            for r in responses
        ])

# Создаём команду агентов
team = AgentTeam()

# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

class Statistics:
    def __init__(self):
        self.start_time = datetime.now()
        self.queries = 0
        self.tasks = 0
        self.users: Set[int] = set()
        self.popular_topics: Dict[str, int] = defaultdict(int)
    
    def record_query(self, user_id: int, topic: str = "general"):
        self.queries += 1
        self.users.add(user_id)
        self.popular_topics[topic] += 1
    
    def record_task(self):
        self.tasks += 1
    
    def get_summary(self) -> str:
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        top_topics = sorted(self.popular_topics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        agent_stats = "\n".join([
            f"• {a.display_name}: {a.calls} ({a.successful_calls}✓)"
            for a in list(team.agents.values())[:10]
        ])
        
        return f"""📊 **СТАТИСТИКА DEEPTHINK v5.0**

⏱ Работает: {hours:.1f} часов
👥 Пользователей: {len(self.users)}
💬 Запросов: {self.queries}
✅ Задач: {self.tasks}

🤖 **ТОП АГЕНТОВ:**
{agent_stats}

📈 **AI движок:**
• Запросов к API: {ai.stats['requests']}
• Успешных: {ai.stats['success']}
• Текущая модель: {ai._get_model().split('/')[1]}

🔥 **Популярные темы:**
{chr(10).join([f"• {t}: {c}" for t, c in top_topics]) if top_topics else "• Пока нет данных"}"""

stats = Statistics()

# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramBot:
    def __init__(self):
        self.api = cfg.TELEGRAM_API
        self.user_contexts: Dict[int, Dict] = {}
    
    async def _reset_webhook(self):
        """Сброс webhook для избежания конфликта 409"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Удаляем webhook
                await client.get(f"{self.api}/deleteWebhook?drop_pending_updates=true")
                log.info("✅ Webhook сброшен")
                
                # Получаем последние обновления для сброса offset
                await client.get(f"{self.api}/getUpdates?offset=-1&limit=1")
                log.info("✅ Updates очищены")
                
            except Exception as e:
                log.warn(f"Reset webhook error: {e}")
    
    async def send(self, chat_id: int, text: str, buttons: Dict = None, parse_mode: str = "Markdown"):
        """Отправка сообщения"""
        async with httpx.AsyncClient(timeout=30) as client:
            # Разбиваем длинные сообщения
            chunks = self._split_message(text, 4096)
            
            for i, chunk in enumerate(chunks):
                data = {
                    "chat_id": chat_id,
                    "text": chunk,
                }
                
                if parse_mode:
                    data["parse_mode"] = parse_mode
                
                # Кнопки только к последнему сообщению
                if buttons and i == len(chunks) - 1:
                    data["reply_markup"] = json.dumps(buttons)
                
                try:
                    resp = await client.post(f"{self.api}/sendMessage", json=data)
                    
                    # Если ошибка парсинга - отправляем без форматирования
                    if resp.status_code != 200 and parse_mode:
                        data.pop("parse_mode", None)
                        data["text"] = chunk
                        await client.post(f"{self.api}/sendMessage", json=data)
                        
                except Exception as e:
                    log.error(f"Send error: {e}")
    
    def _split_message(self, text: str, max_length: int) -> List[str]:
        """Разбиение длинного сообщения"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            
            # Ищем место для разбиения
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = text.rfind(' ', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            
            chunks.append(text[:split_pos])
            text = text[split_pos:].strip()
        
        return chunks
    
    async def send_document(self, chat_id: int, content: str, filename: str, caption: str = ""):
        """Отправка файла"""
        async with httpx.AsyncClient(timeout=30) as client:
            files = {
                "document": (filename, content.encode('utf-8'), "text/plain")
            }
            data = {
                "chat_id": chat_id,
                "caption": caption[:1024] if caption else ""
            }
            
            try:
                await client.post(
                    f"{self.api}/sendDocument",
                    data=data,
                    files=files
                )
            except Exception as e:
                log.error(f"Send document error: {e}")
    
    async def answer_callback(self, callback_id: str, text: str = None):
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    f"{self.api}/answerCallbackQuery",
                    json={"callback_query_id": callback_id, "text": text}
                )
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
    
    def make_buttons(self, user_id: int) -> Dict:
        """Создание кнопок"""
        return {"inline_keyboard": [
            [
                {"text": "📊 Статистика", "callback_data": f"stats_{user_id}"},
                {"text": "🤖 Агенты", "callback_data": f"agents_{user_id}"}
            ],
            [
                {"text": "❓ Помощь", "callback_data": f"help_{user_id}"}
            ]
        ]}
    
    # ═══════════════════════════════════════════════════════════════
    # HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    async def cmd_start(self, chat_id: int, name: str):
        text = f"""🧠 **DEEPTHINK v5.0 ENTERPRISE**

Привет, {name}! 👋

Я - AI-система нового поколения с командой из **30+ экспертов**.

🤖 **МОИ ВОЗМОЖНОСТИ:**
• Отвечаю на ЛЮБЫЕ вопросы
• Ищу информацию в интернете
• Анализирую, исследую, создаю
• Пишу код, тексты, планы
• Работаю с командой агентов

👥 **МОЯ КОМАНДА:**
🎯 Координатор | 📊 Аналитик | 🔬 Исследователь
💼 Бизнес-стратег | 💰 Эксперт по заработку
💻 Разработчики | 📢 Маркетологи
🎨 Креативщики | 🧠 Психологи
...и ещё 20+ специалистов!

🚀 **ПРИМЕРЫ ЗАПРОСОВ:**
• "Расскажи про нейросеть Gemini"
• "Как работает блокчейн?"
• "Напиши бизнес-план стартапа"
• "Создай код телеграм бота"
• "Как заработать на AI в 2025?"

💡 **Просто напиши любой вопрос!**

/help - все команды"""
        await self.send(chat_id, text)
    
    async def cmd_help(self, chat_id: int):
        text = """📖 **КОМАНДЫ DEEPTHINK v5.0**

**Информация:**
/start - Начало работы
/help - Эта справка
/agents - Список всех агентов
/stats - Статистика системы

**Примеры запросов:**
• Любой вопрос на любую тему
• "Объясни [тема]" - подробное объяснение
• "Сравни [A] и [B]" - сравнительный анализ
• "Напиши код [задача]" - программирование
• "Создай план [тема]" - планирование
• "Проанализируй [тема]" - глубокий анализ

**Как это работает:**
1. Ты пишешь запрос
2. 30+ агентов анализируют его
3. Исследователь ищет в интернете
4. Эксперты дают свои мнения
5. Координатор собирает всё в ответ

💡 Я отвечаю на ЛЮБЫЕ вопросы!"""
        await self.send(chat_id, text)
    
    async def cmd_agents(self, chat_id: int):
        text = f"🤖 **КОМАНДА ИЗ {len(team.agents)} АГЕНТОВ:**\n\n"
        
        categories = {
            "🧠 МОЗГОВОЙ ЦЕНТР": ["coordinator", "analyst", "researcher"],
            "💰 БИЗНЕС": ["business", "money", "investor", "startup", "ecommerce"],
            "💻 ТЕХНОЛОГИИ": ["developer", "architect", "devops", "ai_expert", "security", "blockchain", "mobile", "automation"],
            "📢 МАРКЕТИНГ": ["marketer", "smm", "seo", "copywriter", "targetolog"],
            "🎨 КРЕАТИВ": ["creative", "ux"],
            "📚 ОБРАЗОВАНИЕ": ["teacher", "mentor"],
            "🧠 ПСИХОЛОГИЯ": ["psychologist", "coach"],
            "⚖️ ПРАВО И ФИНАНСЫ": ["lawyer", "accountant"],
            "🔧 ПОДДЕРЖКА": ["support", "qa", "translator"]
        }
        
        for cat_name, agent_ids in categories.items():
            agents_in_cat = [team.agents[aid] for aid in agent_ids if aid in team.agents]
            if agents_in_cat:
                text += f"\n**{cat_name}:**\n"
                for agent in agents_in_cat:
                    text += f"• {agent.display_name} ({agent.calls})\n"
        
        await self.send(chat_id, text)
    
    async def cmd_stats(self, chat_id: int):
        await self.send(chat_id, stats.get_summary())
    
    async def handle_message(self, chat_id: int, user_id: int, text: str, name: str):
        """Обработка любого сообщения - НАСТОЯЩЕЕ МЫШЛЕНИЕ"""
        
        stats.record_query(user_id)
        
        await self.typing(chat_id)
        
        # Отправляем статус
        await self.send(chat_id,
            "🧠 **DEEP THINKING...**\n\n"
            f"📝 Запрос: _{text[:50]}{'...' if len(text) > 50 else ''}_\n\n"
            "🔬 Исследователь ищет информацию...\n"
            "👥 Агенты анализируют запрос...\n"
            "⏳ Это займёт 10-30 секунд..."
        )
        
        try:
            # ГЛАВНАЯ МАГИЯ - коллаборативное мышление команды
            result = await team.collaborative_think(
                query=text,
                use_web_search=True
            )
            
            if result["success"] and result["synthesis"]:
                response = result["synthesis"]
                
                # Добавляем footer
                agents_str = ", ".join(result["agents_used"][:5])
                footer = f"\n\n---\n👥 _{agents_str}_\n⏱ _{result['thinking_time']:.1f}с_"
                
                full_response = response + footer
                
                # Если ответ очень длинный - отправляем файл
                if len(full_response) > 4000:
                    # Отправляем краткую версию
                    short_response = response[:3500] + "\n\n... _(полная версия в файле)_" + footer
                    await self.send(chat_id, short_response, self.make_buttons(user_id))
                    
                    # Отправляем файл с полным ответом
                    await self.send_document(
                        chat_id,
                        response,
                        f"deepthink_response_{int(time.time())}.txt",
                        "📄 Полный ответ в файле"
                    )
                else:
                    await self.send(chat_id, full_response, self.make_buttons(user_id))
                
                # Сохраняем контекст
                self.user_contexts[user_id] = {
                    "last_query": text,
                    "last_response": response[:1000],
                    "timestamp": time.time()
                }
                
            else:
                # Fallback - прямой запрос к AI
                log.warn("⚠️ Team thinking failed, fallback to direct AI")
                
                direct_response, success = await ai.think(
                    prompt=text,
                    system="Ты - умный AI-ассистент. Отвечай подробно, информативно, на русском языке.",
                    max_tokens=1500
                )
                
                if success and direct_response:
                    await self.send(chat_id, direct_response, self.make_buttons(user_id))
                else:
                    await self.send(chat_id, 
                        "⚠️ Произошла ошибка. Попробуй ещё раз через минуту.\n\n"
                        "Возможные причины:\n"
                        "• Перегрузка AI-сервера\n"
                        "• Слишком сложный запрос\n\n"
                        "💡 Попробуй переформулировать вопрос."
                    )
                    
        except Exception as e:
            log.error(f"Handle message error: {e}")
            await self.send(chat_id, f"⚠️ Ошибка: {str(e)[:200]}")
    
    async def handle_callback(self, callback_id: str, chat_id: int, user_id: int, data: str):
        """Обработка callback"""
        await self.answer_callback(callback_id)
        
        if data.startswith("stats_"):
            await self.cmd_stats(chat_id)
        elif data.startswith("agents_"):
            await self.cmd_agents(chat_id)
        elif data.startswith("help_"):
            await self.cmd_help(chat_id)
    
    async def handle_update(self, update: Dict):
        """Обработка обновления"""
        try:
            if "message" in update:
                msg = update["message"]
                
                if "text" not in msg:
                    return
                
                chat_id = msg["chat"]["id"]
                user = msg.get("from", {})
                user_id = user.get("id", 0)
                name = user.get("first_name", "User")
                text = msg["text"]
                
                log.info(f"📩 [{user_id}] {text[:60]}...")
                
                # Команды
                if text == "/start":
                    await self.cmd_start(chat_id, name)
                elif text == "/help":
                    await self.cmd_help(chat_id)
                elif text == "/agents":
                    await self.cmd_agents(chat_id)
                elif text == "/stats":
                    await self.cmd_stats(chat_id)
                elif text.startswith("/"):
                    await self.send(chat_id, "❓ Неизвестная команда. Напиши /help")
                else:
                    # Любое сообщение - ДУМАЕМ
                    await self.handle_message(chat_id, user_id, text, name)
            
            elif "callback_query" in update:
                cb = update["callback_query"]
                await self.handle_callback(
                    cb["id"],
                    cb["message"]["chat"]["id"],
                    cb["from"]["id"],
                    cb["data"]
                )
                
        except Exception as e:
            log.error(f"Update error: {e}")
    
    async def run(self):
        """Запуск бота"""
        
        log.info("=" * 60)
        log.info("🧠 DEEPTHINK v5.0 ENTERPRISE EDITION")
        log.info("=" * 60)
        log.info(f"🤖 Агентов: {len(team.agents)}")
        log.info(f"🌐 Web Search: {'✅' if cfg.ENABLE_WEB_SEARCH else '❌'}")
        log.info(f"🔧 Модель: {ai._get_model()}")
        log.info("=" * 60)
        
        # ВАЖНО: Сбрасываем webhook чтобы избежать 409
        await self._reset_webhook()
        
        offset = 0
        consecutive_errors = 0
        
        async with httpx.AsyncClient(timeout=cfg.TIMEOUT) as client:
            log.info("✅ БОТ ЗАПУЩЕН!")
            
            while True:
                try:
                    resp = await client.get(
                        f"{self.api}/getUpdates",
                        params={
                            "offset": offset,
                            "timeout": 30,
                            "allowed_updates": ["message", "callback_query"]
                        }
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        if data.get("ok"):
                            for update in data.get("result", []):
                                offset = update["update_id"] + 1
                                asyncio.create_task(self.handle_update(update))
                        
                        consecutive_errors = 0
                        
                    elif resp.status_code == 409:
                        # Конфликт - сбрасываем
                        log.warn("⚠️ 409 Conflict - сброс...")
                        await self._reset_webhook()
                        await asyncio.sleep(3)
                        
                    else:
                        log.warn(f"API error: {resp.status_code}")
                        consecutive_errors += 1
                
                except httpx.TimeoutException:
                    continue
                    
                except Exception as e:
                    consecutive_errors += 1
                    log.error(f"Polling error: {e}")
                    
                    if consecutive_errors > 10:
                        log.warn("Много ошибок, пауза 30с...")
                        await asyncio.sleep(30)
                        await self._reset_webhook()
                        consecutive_errors = 0
                    else:
                        await asyncio.sleep(3)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("\n" + "=" * 70)
    print("🧠 DEEPTHINK v5.0 ENTERPRISE EDITION")
    print("👥 30+ AI AGENTS | 🌐 WEB SEARCH | 🔄 COLLABORATIVE THINKING")
    print("=" * 70 + "\n")
    
    bot = TelegramBot()
    await bot.run()

def run():
    # Health check server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Остановлено")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
