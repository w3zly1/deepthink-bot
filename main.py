"""
╔══════════════════════════════════════════════════════════════════╗
║          DEEPTHINK AUTOHUSTLE ULTIMATE v2.0                      ║
║          AI Swarm с 15+ агентами для автозаработка               ║
║          Deep Thinking • Auto Execution • Money Making           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ═══════════════════════════════════════════════════════════════════
# ТВОИ КЛЮЧИ - ЗАМЕНИ НА СВОИ
# ═══════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = "8510653021:AAFCsjXyWLweEFBPrZD_wxlUmRe8uRQjQDY"
OPENROUTER_KEY = "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"

# ═══════════════════════════════════════════════════════════════════

print("🚀 Загрузка DeepThink AutoHustle Ultimate...")
print(f"✅ Telegram: {TELEGRAM_TOKEN[:15]}...")
print(f"✅ OpenRouter: {OPENROUTER_KEY[:20]}...")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# AI Клиент
ai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

# ═══════════════════════════════════════════════════════════════════
# СИСТЕМА ПАМЯТИ
# ═══════════════════════════════════════════════════════════════════

class MemoryType(Enum):
    CONVERSATION = "conversation"
    LEARNING = "learning"
    PROJECT = "project"
    INSIGHT = "insight"
    ERROR = "error"

@dataclass
class Memory:
    """Единица памяти"""
    id: str
    type: MemoryType
    content: Dict
    timestamp: datetime = field(default_factory=datetime.now)
    importance: int = 5  # 1-10
    
class MemoryBank:
    """Банк памяти системы"""
    
    def __init__(self):
        self.memories: Dict[str, List[Memory]] = {}
        self.user_profiles: Dict[int, Dict] = {}
        self.global_learnings: List[Dict] = []
        self.projects: List[Dict] = []
        self.statistics = {
            'total_queries': 0,
            'successful_tasks': 0,
            'products_created': 0,
            'money_opportunities_found': 0
        }
    
    def get_user_memory(self, user_id: int) -> List[Memory]:
        return self.memories.get(str(user_id), [])
    
    def add_memory(self, user_id: int, memory_type: MemoryType, content: Dict, importance: int = 5):
        key = str(user_id)
        if key not in self.memories:
            self.memories[key] = []
        
        memory = Memory(
            id=hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:12],
            type=memory_type,
            content=content,
            importance=importance
        )
        
        self.memories[key].append(memory)
        
        # Ограничиваем память (последние 100 записей на юзера)
        if len(self.memories[key]) > 100:
            self.memories[key] = sorted(
                self.memories[key], 
                key=lambda m: m.importance, 
                reverse=True
            )[:100]
    
    def get_user_profile(self, user_id: int) -> Dict:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'id': user_id,
                'interests': [],
                'skill_level': 'unknown',
                'preferred_income_type': 'unknown',
                'completed_tasks': 0,
                'created_at': datetime.now().isoformat()
            }
        return self.user_profiles[user_id]
    
    def update_user_profile(self, user_id: int, updates: Dict):
        profile = self.get_user_profile(user_id)
        profile.update(updates)
    
    def add_learning(self, learning: Dict):
        self.global_learnings.append({
            **learning,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_project(self, project: Dict):
        self.projects.append(project)
        self.statistics['products_created'] += 1
    
    def get_recent_context(self, user_id: int, limit: int = 10) -> str:
        memories = self.get_user_memory(user_id)[-limit:]
        if not memories:
            return "Нет предыдущего контекста."
        
        context_parts = []
        for mem in memories:
            if mem.type == MemoryType.CONVERSATION:
                context_parts.append(f"[{mem.type.value}] {mem.content.get('summary', '')}")
        
        return "\n".join(context_parts) if context_parts else "Начало разговора."

# Глобальный банк памяти
memory_bank = MemoryBank()

# ═══════════════════════════════════════════════════════════════════
# БАЗОВЫЙ КЛАСС АГЕНТА
# ═══════════════════════════════════════════════════════════════════

class BaseAgent:
    """Базовый класс для всех AI агентов"""
    
    def __init__(self, name: str, role: str, expertise: List[str], personality: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.personality = personality
        self.model = "anthropic/claude-3.5-sonnet"
        self.tasks_completed = 0
        self.success_rate = 1.0
    
    async def think(self, task: str, context: str = "", depth: int = 1) -> Dict:
        """Основной метод мышления агента"""
        
        system_prompt = f"""Ты - {self.name}, {self.role}.

ТВОЯ ЭКСПЕРТИЗА: {', '.join(self.expertise)}

ЛИЧНОСТЬ: {self.personality}

ПРИНЦИПЫ РАБОТЫ:
1. Думай глубоко, анализируй многосторонне
2. Давай конкретные, действенные советы
3. Всегда ищи способы монетизации
4. Учитывай риски и сложности
5. Предлагай автоматизацию где возможно

ГЛУБИНА АНАЛИЗА: Уровень {depth}/3 (1=быстрый, 3=максимальный)"""

        user_prompt = f"""КОНТЕКСТ:
{context}

ЗАДАЧА:
{task}

Проведи анализ соответственно своей экспертизе."""

        try:
            response = ai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7 if depth < 3 else 0.5,
                max_tokens=2000 * depth
            )
            
            self.tasks_completed += 1
            
            return {
                'agent': self.name,
                'role': self.role,
                'response': response.choices[0].message.content,
                'success': True
            }
            
        except Exception as e:
            self.success_rate *= 0.95
            return {
                'agent': self.name,
                'role': self.role,
                'response': f"Ошибка: {str(e)}",
                'success': False
            }

# ═══════════════════════════════════════════════════════════════════
# СПЕЦИАЛИЗИРОВАННЫЕ АГЕНТЫ (15 штук)
# ═══════════════════════════════════════════════════════════════════

class ResearchAgent(BaseAgent):
    """Агент глубокого исследования"""
    
    def __init__(self):
        super().__init__(
            name="🔬 Researcher",
            role="Главный исследователь",
            expertise=["market research", "trend analysis", "data synthesis", "competitive analysis"],
            personality="Дотошный, любознательный, объективный. Всегда ищет первоисточники и проверяет факты."
        )
    
    async def deep_research(self, topic: str, context: str = "") -> Dict:
        task = f"""Проведи ГЛУБОКОЕ исследование темы: {topic}

СТРУКТУРА:
1. Что это такое (суть)
2. История и эволюция
3. Текущее состояние рынка (цифры, размер, рост)
4. Ключевые игроки
5. Технологические аспекты
6. Правовые/регуляторные вопросы
7. Будущие тренды (2-5 лет)
8. Возможности для входа

Давай конкретные цифры и примеры."""

        return await self.think(task, context, depth=3)


class MarketAnalyst(BaseAgent):
    """Аналитик рынка"""
    
    def __init__(self):
        super().__init__(
            name="📊 Market Analyst",
            role="Рыночный аналитик",
            expertise=["market sizing", "competition analysis", "pricing strategy", "market entry"],
            personality="Аналитический, прагматичный. Всё переводит в цифры и ROI."
        )
    
    async def analyze_market(self, niche: str, context: str = "") -> Dict:
        task = f"""Проанализируй рынок: {niche}

АНАЛИЗ:
1. TAM/SAM/SOM (с цифрами)
2. Темпы роста (CAGR)
3. Барьеры входа
4. Конкурентная карта
5. Ценообразование в нише
6. Каналы продаж
7. Юнит-экономика типичного бизнеса
8. Окно возможностей

Фокус на возможностях для новичка с минимальным бюджетом."""

        return await self.think(task, context, depth=2)


class MoneyFinder(BaseAgent):
    """Искатель способов заработка"""
    
    def __init__(self):
        super().__init__(
            name="💰 Money Finder",
            role="Эксперт по монетизации",
            expertise=["monetization strategies", "passive income", "side hustles", "business models"],
            personality="Креативный, предприимчивый. Видит деньги там, где другие не видят."
        )
    
    async def find_money_opportunities(self, topic: str, user_profile: Dict, context: str = "") -> Dict:
        skill_level = user_profile.get('skill_level', 'beginner')
        
        task = f"""Найди ВСЕ способы заработка на теме: {topic}

УРОВЕНЬ ПОЛЬЗОВАТЕЛЯ: {skill_level}

НАЙДИ МИНИМУМ 7 СПОСОБОВ:

Категория А: БЕЗ ВЛОЖЕНИЙ (начать сегодня)
- 3 способа с $0 стартом
- Конкретные шаги
- Реалистичный доход

Категория Б: МИНИМАЛЬНЫЕ ВЛОЖЕНИЯ ($10-100)
- 2 способа
- Что купить/настроить
- ROI и сроки

Категория В: МАСШТАБИРОВАНИЕ ($100+)
- 2 способа для роста
- Потенциал x10-x100

Для каждого способа укажи:
- Название
- Потенциал $/месяц
- Время до первых денег
- Что делать (3-5 шагов)
- Что может автоматизировать AI
- Риски"""

        return await self.think(task, context, depth=3)


class StrategyArchitect(BaseAgent):
    """Архитектор стратегий"""
    
    def __init__(self):
        super().__init__(
            name="🏗️ Strategy Architect",
            role="Архитектор бизнес-стратегий",
            expertise=["business strategy", "go-to-market", "growth hacking", "scaling"],
            personality="Системный мыслитель, видит всю картину. Строит долгосрочные планы."
        )
    
    async def create_strategy(self, goal: str, resources: str, context: str = "") -> Dict:
        task = f"""Создай пошаговую стратегию достижения цели.

ЦЕЛЬ: {goal}
РЕСУРСЫ: {resources}

СТРАТЕГИЯ ДОЛЖНА ВКЛЮЧАТЬ:

1. ФАЗА 0: Подготовка (1-3 дня)
   - Что изучить
   - Что настроить
   - Инструменты

2. ФАЗА 1: Запуск (неделя 1-2)
   - MVP действия
   - Первые клиенты/доходы
   - Метрики успеха

3. ФАЗА 2: Оптимизация (неделя 3-4)
   - Анализ результатов
   - Улучшения
   - A/B тесты

4. ФАЗА 3: Масштабирование (месяц 2-3)
   - Автоматизация
   - Делегирование
   - Рост x3-x10

5. РИСКИ и ПЛАН Б
   - Что может пойти не так
   - Запасные варианты

Будь максимально конкретным с датами и действиями."""

        return await self.think(task, context, depth=3)


class ContentCreator(BaseAgent):
    """Создатель контента"""
    
    def __init__(self):
        super().__init__(
            name="✍️ Content Creator",
            role="Мастер создания контента",
            expertise=["copywriting", "content marketing", "viral content", "SEO writing"],
            personality="Креативный, убедительный. Пишет тексты которые продают и вовлекают."
        )
    
    async def create_content(self, content_type: str, topic: str, goal: str, context: str = "") -> Dict:
        task = f"""Создай {content_type} на тему: {topic}

ЦЕЛЬ КОНТЕНТА: {goal}

ТРЕБОВАНИЯ:
- Профессиональное качество
- Готов к публикации БЕЗ РЕДАКТИРОВАНИЯ
- Вовлекающий и полезный
- SEO оптимизирован (если применимо)
- Call-to-action включён

СОЗДАЙ ПОЛНОСТЬЮ ГОТОВЫЙ КОНТЕНТ."""

        return await self.think(task, context, depth=2)


class CodeArchitect(BaseAgent):
    """Архитектор кода"""
    
    def __init__(self):
        super().__init__(
            name="💻 Code Architect",
            role="Главный разработчик",
            expertise=["web development", "automation", "APIs", "MVP development"],
            personality="Практичный, эффективный. Пишет чистый, рабочий код."
        )
    
    async def create_code(self, project_type: str, requirements: str, context: str = "") -> Dict:
        task = f"""Напиши ПОЛНЫЙ РАБОЧИЙ КОД.

ТИП ПРОЕКТА: {project_type}
ТРЕБОВАНИЯ: {requirements}

ОБЯЗАТЕЛЬНО:
1. Полностью рабочий код (не псевдокод)
2. Все необходимые импорты
3. Обработка ошибок
4. Комментарии на русском
5. Инструкция по запуску
6. Список зависимостей (requirements.txt)

Код должен работать СРАЗУ после копирования."""

        return await self.think(task, context, depth=3)


class ProductDesigner(BaseAgent):
    """Дизайнер продуктов"""
    
    def __init__(self):
        super().__init__(
            name="🎨 Product Designer",
            role="Дизайнер цифровых продуктов",
            expertise=["product design", "UX/UI", "landing pages", "conversion optimization"],
            personality="Эстетичный, user-centric. Создаёт продукты которые люди хотят использовать."
        )
    
    async def design_product(self, product_type: str, target_audience: str, context: str = "") -> Dict:
        task = f"""Спроектируй цифровой продукт.

ТИП: {product_type}
АУДИТОРИЯ: {target_audience}

СОЗДАЙ:
1. Концепция продукта
2. Ключевые фичи (3-5)
3. User flow
4. Структура страниц/экранов
5. Текст для каждого элемента
6. Pricing стратегия
7. Landing page (полный текст)

Продукт должен решать реальную проблему и быть готов к продаже."""

        return await self.think(task, context, depth=2)


class MarketingExpert(BaseAgent):
    """Эксперт по маркетингу"""
    
    def __init__(self):
        super().__init__(
            name="📢 Marketing Expert",
            role="Эксперт по маркетингу и продвижению",
            expertise=["digital marketing", "social media", "paid ads", "organic growth"],
            personality="Креативный, data-driven. Знает как привлечь внимание и конвертировать."
        )
    
    async def create_marketing_plan(self, product: str, budget: str, context: str = "") -> Dict:
        task = f"""Создай маркетинговый план.

ПРОДУКТ: {product}
БЮДЖЕТ: {budget}

ПЛАН ДОЛЖЕН ВКЛЮЧАТЬ:

1. БЕСПЛАТНЫЕ КАНАЛЫ
   - Reddit (какие сабреддиты, как постить)
   - Twitter/X (стратегия контента)
   - LinkedIn (если B2B)
   - YouTube (темы видео)
   - SEO (ключевые слова)

2. ПЛАТНЫЕ КАНАЛЫ (если бюджет есть)
   - Google Ads
   - Facebook/Instagram
   - Influencers

3. КОНТЕНТ-ПЛАН на месяц
   - 20 готовых постов/твитов
   - 5 идей для длинного контента

4. VIRAL СТРАТЕГИИ
   - Hooks
   - Controversy
   - Социальное доказательство

5. МЕТРИКИ для отслеживания

Всё должно быть готово к копипасте и использованию."""

        return await self.think(task, context, depth=3)


class SalesExpert(BaseAgent):
    """Эксперт по продажам"""
    
    def __init__(self):
        super().__init__(
            name="🤝 Sales Expert",
            role="Эксперт по продажам",
            expertise=["sales funnels", "cold outreach", "negotiation", "closing deals"],
            personality="Убедительный, настойчивый. Превращает лиды в деньги."
        )
    
    async def create_sales_strategy(self, product: str, price: str, audience: str, context: str = "") -> Dict:
        task = f"""Создай стратегию продаж.

ПРОДУКТ: {product}
ЦЕНА: {price}
АУДИТОРИЯ: {audience}

СТРАТЕГИЯ:

1. ВОРОНКА ПРОДАЖ
   - Этапы
   - Конверсия на каждом этапе
   - Автоматизация

2. СКРИПТЫ
   - Cold email (3 варианта)
   - DM скрипт
   - Звонок (если применимо)
   - Обработка возражений (10 типичных)

3. ЦЕНООБРАЗОВАНИЕ
   - Anchor pricing
   - Тарифы
   - Upsells/Downsells

4. СОЦИАЛЬНОЕ ДОКАЗАТЕЛЬСТВО
   - Как получить первые отзывы
   - Case studies формат

5. АВТОМАТИЗАЦИЯ ПРОДАЖ
   - Email sequences
   - Chatbot скрипты"""

        return await self.think(task, context, depth=2)


class AutomationEngineer(BaseAgent):
    """Инженер автоматизации"""
    
    def __init__(self):
        super().__init__(
            name="🤖 Automation Engineer",
            role="Инженер автоматизации",
            expertise=["workflow automation", "no-code tools", "APIs", "bots"],
            personality="Ленивый в хорошем смысле - автоматизирует всё что можно."
        )
    
    async def create_automation(self, task_to_automate: str, tools_available: str, context: str = "") -> Dict:
        task = f"""Создай автоматизацию.

ЧТО АВТОМАТИЗИРОВАТЬ: {task_to_automate}
ДОСТУПНЫЕ ИНСТРУМЕНТЫ: {tools_available}

СОЗДАЙ:

1. СХЕМА АВТОМАТИЗАЦИИ
   - Триггеры
   - Действия
   - Условия

2. ПОШАГОВАЯ НАСТРОЙКА
   - Для no-code (Zapier, Make, n8n)
   - ИЛИ код (Python)

3. ГОТОВЫЕ КОНФИГУРАЦИИ
   - JSON/YAML если нужно
   - Код если нужно

4. МОНИТОРИНГ
   - Как отслеживать работу
   - Как исправлять ошибки

5. ЭКОНОМИЯ ВРЕМЕНИ
   - Сколько часов экономит
   - ROI автоматизации

Автоматизация должна быть готова к внедрению."""

        return await self.think(task, context, depth=2)


class RiskAnalyst(BaseAgent):
    """Аналитик рисков"""
    
    def __init__(self):
        super().__init__(
            name="⚠️ Risk Analyst",
            role="Аналитик рисков",
            expertise=["risk assessment", "mitigation strategies", "scenario planning"],
            personality="Осторожный, реалистичный. Видит проблемы до того как они случатся."
        )
    
    async def analyze_risks(self, plan: str, context: str = "") -> Dict:
        task = f"""Проанализируй риски плана.

ПЛАН: {plan}

АНАЛИЗ РИСКОВ:

1. КРИТИЧЕСКИЕ РИСКИ (могут убить проект)
   - Риск
   - Вероятность
   - Последствия
   - Митигация

2. ВЫСОКИЕ РИСКИ
   [аналогично]

3. СРЕДНИЕ РИСКИ
   [аналогично]

4. PLAN B для каждого критического риска

5. RED FLAGS на которые смотреть

6. KILL SWITCHES (когда пора остановиться)

Будь реалистичным но не пессимистичным."""

        return await self.think(task, context, depth=2)


class LegalAdvisor(BaseAgent):
    """Юридический советник"""
    
    def __init__(self):
        super().__init__(
            name="⚖️ Legal Advisor",
            role="Юридический советник",
            expertise=["business law", "intellectual property", "contracts", "compliance"],
            personality="Осторожный, точный. Защищает от юридических проблем."
        )
    
    async def legal_check(self, business_idea: str, jurisdiction: str = "РФ", context: str = "") -> Dict:
        task = f"""Проведи юридический анализ.

ИДЕЯ: {business_idea}
ЮРИСДИКЦИЯ: {jurisdiction}

ПРОВЕРЬ:

1. ЛЕГАЛЬНОСТЬ
   - Законно ли это?
   - Нужны ли лицензии?
   - Возрастные ограничения?

2. НАЛОГИ
   - Как оформить доход?
   - Какой режим выбрать?
   - Примерная нагрузка

3. ЗАЩИТА
   - Что защитить (бренд, код, контент)?
   - Как защитить?

4. ДОГОВОРЫ
   - Какие нужны?
   - Основные пункты

5. RED FLAGS
   - Чего избегать?

Давай практичные советы, не общие фразы."""

        return await self.think(task, context, depth=2)


class PersonalCoach(BaseAgent):
    """Персональный коуч"""
    
    def __init__(self):
        super().__init__(
            name="🎯 Personal Coach",
            role="Персональный бизнес-коуч",
            expertise=["goal setting", "motivation", "productivity", "mindset"],
            personality="Поддерживающий, вдохновляющий. Помогает преодолевать препятствия."
        )
    
    async def coach(self, situation: str, user_profile: Dict, context: str = "") -> Dict:
        task = f"""Дай персональный совет.

СИТУАЦИЯ: {situation}
ПРОФИЛЬ: {json.dumps(user_profile, ensure_ascii=False)}

ТВОЙ ОТВЕТ:

1. ПОНИМАНИЕ (покажи что понял ситуацию)

2. ЧЕСТНАЯ ОЦЕНКА
   - Что хорошо
   - Что можно улучшить

3. КОНКРЕТНЫЕ ДЕЙСТВИЯ (3-5)
   - Что делать СЕГОДНЯ
   - Что делать НА ЭТОЙ НЕДЕЛЕ
   - Что делать В ЭТОМ МЕСЯЦЕ

4. МОТИВАЦИЯ
   - Почему это реально
   - Примеры успеха

5. ПРЕДОСТЕРЕЖЕНИЕ
   - От чего воздержаться
   - Типичные ошибки новичков

Будь как друг который хочет чтобы человек преуспел."""

        return await self.think(task, context, depth=2)


class TrendHunter(BaseAgent):
    """Охотник за трендами"""
    
    def __init__(self):
        super().__init__(
            name="🔥 Trend Hunter",
            role="Охотник за трендами",
            expertise=["trend spotting", "viral content", "emerging markets", "early adoption"],
            personality="Всегда в курсе, быстро реагирует. Видит возможности раньше других."
        )
    
    async def find_trends(self, industry: str, context: str = "") -> Dict:
        task = f"""Найди горячие тренды в индустрии: {industry}

НАЙДИ:

1. ГОРЯЧИЕ ТРЕНДЫ (прямо сейчас)
   - Что взрывается
   - Цифры роста
   - Окно возможности

2. РАСТУЩИЕ ТРЕНДЫ (следующие 3-6 месяцев)
   - Что набирает обороты
   - Сигналы роста

3. ФОРМИРУЮЩИЕСЯ ТРЕНДЫ (6-12 месяцев)
   - Что появляется
   - Почему станет большим

4. ДЛЯ КАЖДОГО ТРЕНДА:
   - Как на нём заработать
   - Что создать/сделать
   - Кто уже зарабатывает
   - Сложность входа

5. АНТИТРЕНДЫ (что умирает)
   - Чего избегать

Фокус на том что можно монетизировать БЕЗ больших вложений."""

        return await self.think(task, context, depth=2)


class Synthesizer(BaseAgent):
    """Синтезатор информации"""
    
    def __init__(self):
        super().__init__(
            name="🧬 Synthesizer",
            role="Синтезатор информации",
            expertise=["information synthesis", "decision making", "recommendation systems"],
            personality="Объективный, ясный. Превращает хаос в порядок и действия."
        )
    
    async def synthesize(self, inputs: List[Dict], user_goal: str, context: str = "") -> Dict:
        inputs_text = "\n\n".join([
            f"[{inp.get('agent', 'Unknown')}]: {inp.get('response', '')[:500]}..."
            for inp in inputs
        ])
        
        task = f"""Синтезируй информацию от разных агентов.

ЦЕЛЬ ПОЛЬЗОВАТЕЛЯ: {user_goal}

ВХОДНЫЕ ДАННЫЕ:
{inputs_text}

СОЗДАЙ:

1. EXECUTIVE SUMMARY (3-5 предложений)

2. КЛЮЧЕВЫЕ ИНСАЙТЫ
   - Топ-5 важных выводов

3. РЕКОМЕНДОВАННЫЕ ДЕЙСТВИЯ
   - Приоритет 1 (сделать сегодня)
   - Приоритет 2 (сделать на неделе)
   - Приоритет 3 (сделать в месяце)

4. ЛУЧШИЙ ПУТЬ К ЦЕЛИ
   - Пошаговый план

5. QUICK WINS
   - Что даст быстрый результат

6. ПРЕДУПРЕЖДЕНИЯ
   - На что обратить внимание

Ответ должен быть чётким и actionable."""

        return await self.think(task, context, depth=3)

# ═══════════════════════════════════════════════════════════════════
# ОРКЕСТРАТОР - КООРДИНИРУЕТ ВСЕХ АГЕНТОВ
# ═══════════════════════════════════════════════════════════════════

class SwarmOrchestrator:
    """Дирижёр роя агентов"""
    
    def __init__(self):
        # Инициализация всех агентов
        self.agents = {
            'researcher': ResearchAgent(),
            'market_analyst': MarketAnalyst(),
            'money_finder': MoneyFinder(),
            'strategy_architect': StrategyArchitect(),
            'content_creator': ContentCreator(),
            'code_architect': CodeArchitect(),
            'product_designer': ProductDesigner(),
            'marketing_expert': MarketingExpert(),
            'sales_expert': SalesExpert(),
            'automation_engineer': AutomationEngineer(),
            'risk_analyst': RiskAnalyst(),
            'legal_advisor': LegalAdvisor(),
            'personal_coach': PersonalCoach(),
            'trend_hunter': TrendHunter(),
            'synthesizer': Synthesizer()
        }
        
        print(f"✅ Инициализировано {len(self.agents)} агентов")
    
    async def process_query(self, query: str, user_id: int) -> Dict:
        """Обработка запроса с привлечением нужных агентов"""
        
        user_profile = memory_bank.get_user_profile(user_id)
        context = memory_bank.get_recent_context(user_id)
        
        # Определяем какие агенты нужны
        agents_needed = await self._select_agents(query)
        
        # Параллельно запускаем агентов
        tasks = []
        for agent_name in agents_needed:
            agent = self.agents.get(agent_name)
            if agent:
                if agent_name == 'researcher':
                    tasks.append(agent.deep_research(query, context))
                elif agent_name == 'market_analyst':
                    tasks.append(agent.analyze_market(query, context))
                elif agent_name == 'money_finder':
                    tasks.append(agent.find_money_opportunities(query, user_profile, context))
                elif agent_name == 'trend_hunter':
                    tasks.append(agent.find_trends(query, context))
                else:
                    tasks.append(agent.think(query, context, depth=2))
        
        # Собираем результаты
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные
        successful_results = [
            r for r in results 
            if isinstance(r, dict) and r.get('success', False)
        ]
        
        # Синтезируем
        final_response = await self.agents['synthesizer'].synthesize(
            successful_results,
            query,
            context
        )
        
        # Генерируем автоматические действия
        actions = await self._generate_smart_actions(query, final_response, user_profile)
        
        # Сохраняем в память
        memory_bank.add_memory(
            user_id,
            MemoryType.CONVERSATION,
            {'query': query, 'summary': final_response.get('response', '')[:200]},
            importance=7
        )
        
        memory_bank.statistics['total_queries'] += 1
        memory_bank.statistics['money_opportunities_found'] += len(actions)
        
        return {
            'response': final_response.get('response', ''),
            'agents_used': agents_needed,
            'actions': actions,
            'insights_count': len(successful_results)
        }
    
    async def _select_agents(self, query: str) -> List[str]:
        """Выбор нужных агентов на основе запроса"""
        
        query_lower = query.lower()
        
        agents = ['money_finder']  # Всегда ищем способы заработка
        
        # Логика выбора агентов
        if any(word in query_lower for word in ['рынок', 'анализ', 'конкурент', 'ниша']):
            agents.extend(['researcher', 'market_analyst'])
        
        if any(word in query_lower for word in ['тренд', 'новое', 'хайп', 'взлет']):
            agents.append('trend_hunter')
        
        if any(word in query_lower for word in ['план', 'стратегия', 'как начать', 'пошаговый']):
            agents.append('strategy_architect')
        
        if any(word in query_lower for word in ['код', 'сайт', 'бот', 'автоматизация', 'приложение']):
            agents.extend(['code_architect', 'automation_engineer'])
        
        if any(word in query_lower for word in ['контент', 'статья', 'пост', 'видео', 'текст']):
            agents.append('content_creator')
        
        if any(word in query_lower for word in ['продукт', 'курс', 'сервис', 'saas']):
            agents.append('product_designer')
        
        if any(word in query_lower for word in ['маркетинг', 'реклама', 'продвижение', 'клиенты']):
            agents.append('marketing_expert')
        
        if any(word in query_lower for word in ['продажа', 'клиент', 'воронка', 'конверсия']):
            agents.append('sales_expert')
        
        if any(word in query_lower for word in ['риск', 'опасн', 'провал', 'ошибк']):
            agents.append('risk_analyst')
        
        if any(word in query_lower for word in ['закон', 'легаль', 'налог', 'юридич']):
            agents.append('legal_advisor')
        
        # Всегда добавляем researcher для глубины
        if 'researcher' not in agents:
            agents.insert(0, 'researcher')
        
        return list(set(agents))[:6]  # Максимум 6 агентов
    
    async def _generate_smart_actions(self, query: str, response: Dict, user_profile: Dict) -> List[Dict]:
        """Генерация умных автоматических действий"""
        
        prompt = f"""На основе анализа предложи 3-5 автоматических действий.

ЗАПРОС: {query}
АНАЛИЗ: {response.get('response', '')[:1500]}

ТИПЫ ДЕЙСТВИЙ:
- create_content: Создать готовый контент
- create_code: Написать рабочий код
- create_product: Создать продукт для продажи  
- create_plan: Создать детальный план
- create_marketing: Создать маркетинговые материалы
- create_automation: Создать автоматизацию

JSON формат:
[
  {{
    "type": "тип",
    "name": "Название (кратко)",
    "description": "Что будет создано",
    "value": "Ценность для пользователя",
    "time_to_profit": "Когда начнёт приносить деньги",
    "ai_automation": "95%/80%/60%"
  }}
]

Только JSON!"""

        try:
            response = ai.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content
            
            # Парсинг JSON
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
    
    async def execute_action(self, action: Dict, context: str, user_id: int) -> str:
        """Выполнение автоматического действия"""
        
        action_type = action.get('type', 'create_plan')
        description = action.get('description', '')
        
        # Выбираем подходящего агента
        agent_map = {
            'create_content': 'content_creator',
            'create_code': 'code_architect',
            'create_product': 'product_designer',
            'create_plan': 'strategy_architect',
            'create_marketing': 'marketing_expert',
            'create_automation': 'automation_engineer'
        }
        
        agent_name = agent_map.get(action_type, 'strategy_architect')
        agent = self.agents.get(agent_name)
        
        if not agent:
            return "Агент не найден"
        
        # Специальные методы для разных типов
        if action_type == 'create_content':
            result = await agent.create_content("статья/пост", description, "монетизация", context)
        elif action_type == 'create_code':
            result = await agent.create_code("web/automation", description, context)
        elif action_type == 'create_product':
            result = await agent.design_product(description, "целевая аудитория из контекста", context)
        elif action_type == 'create_marketing':
            result = await agent.create_marketing_plan(description, "$0 (organic)", context)
        elif action_type == 'create_automation':
            result = await agent.create_automation(description, "Python, Zapier, Make", context)
        else:
            user_profile = memory_bank.get_user_profile(user_id)
            result = await agent.create_strategy(description, "минимальные", context)
        
        if result.get('success'):
            memory_bank.statistics['successful_tasks'] += 1
            memory_bank.add_project({
                'type': action_type,
                'description': description,
                'user_id': user_id,
                'created_at': datetime.now().isoformat()
            })
        
        return result.get('response', 'Ошибка выполнения')

# Создаём оркестратора
orchestrator = SwarmOrchestrator()

# ═══════════════════════════════════════════════════════════════════
# TELEGRAM BOT HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка любого сообщения"""
    
    user_id = update.effective_user.id
    message = update.message.text
    
    # Статус мышления
    thinking_msg = await update.message.reply_text(
        "🧠 **DEEP THINKING АКТИВИРОВАН**\n\n"
        "⚙️ Анализирую запрос...\n"
        "🔬 Запускаю исследование...\n"
        "📊 Анализирую рынок...\n"
        "💰 Ищу способы заработка...\n"
        "🤖 Привлекаю специалистов...\n\n"
        f"👥 Работает: 6+ AI агентов",
        parse_mode='Markdown'
    )
    
    try:
        # Главная обработка
        result = await orchestrator.process_query(message, user_id)
        
        response_text = result['response']
        actions = result['actions']
        agents_used = result['agents_used']
        
        # Добавляем информацию об агентах
        agents_info = f"\n\n---\n👥 **Работали:** {', '.join([orchestrator.agents[a].name for a in agents_used if a in orchestrator.agents])}"
        
        full_response = response_text + agents_info
        
        # Кнопки действий
        keyboard = []
        if actions:
            for i, action in enumerate(actions[:5]):
                name = action.get('name', 'Действие')[:28]
                keyboard.append([
                    InlineKeyboardButton(
                        f"🤖 {name}",
                        callback_data=f"action_{i}_{user_id}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{user_id}"),
            InlineKeyboardButton("💡 Ещё идеи", callback_data=f"more_{user_id}")
        ])
        
        # Отправка ответа
        if len(full_response) > 4096:
            parts = [full_response[i:i+4000] for i in range(0, len(full_response), 4000)]
            await thinking_msg.delete()
            
            for idx, part in enumerate(parts):
                if idx == len(parts) - 1:
                    await update.message.reply_text(
                        part,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text(part)
        else:
            await thinking_msg.edit_text(
                full_response,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Сохраняем действия
        if actions:
            context.user_data[f'actions_{user_id}'] = actions
            context.user_data[f'context_{user_id}'] = message
            
    except Exception as e:
        await thinking_msg.edit_text(
            f"⚠️ Ошибка: {str(e)}\n\n"
            "Попробуй переформулировать запрос."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('action_'):
        parts = data.split('_')
        action_idx = int(parts[1])
        user_id = int(parts[2])
        
        actions = context.user_data.get(f'actions_{user_id}', [])
        user_context = context.user_data.get(f'context_{user_id}', '')
        
        if action_idx < len(actions):
            action = actions[action_idx]
            
            await query.message.edit_text(
                f"🤖 **АВТОМАТИЧЕСКОЕ ВЫПОЛНЕНИЕ**\n\n"
                f"📌 Задача: {action.get('name', 'Действие')}\n"
                f"📝 {action.get('description', '')}\n\n"
                f"⏱ Время: 1-3 минуты\n"
                f"🔄 Работаю...",
                parse_mode='Markdown'
            )
            
            result = await orchestrator.execute_action(action, user_context, user_id)
            
            result_text = f"✅ **ГОТОВО!**\n\n**{action.get('name', '')}**\n\n{result[:3700]}"
            
            if len(result) > 3700:
                result_text += f"\n\n_[Текст обрезан: {len(result)} символов]_"
            
            # Разбиваем если нужно
            if len(result_text) > 4096:
                parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
                for part in parts:
                    await query.message.reply_text(part)
            else:
                await query.message.reply_text(result_text)
    
    elif data.startswith('stats_'):
        stats = memory_bank.statistics
        stats_text = (
            f"📊 **СТАТИСТИКА СИСТЕМЫ**\n\n"
            f"💬 Всего запросов: {stats['total_queries']}\n"
            f"✅ Успешных задач: {stats['successful_tasks']}\n"
            f"📦 Продуктов создано: {stats['products_created']}\n"
            f"💰 Найдено возможностей: {stats['money_opportunities_found']}\n\n"
            f"👥 Агентов в системе: {len(orchestrator.agents)}\n"
            f"🧠 Режим: Deep Thinking"
        )
        await query.message.reply_text(stats_text, parse_mode='Markdown')
    
    elif data.startswith('more_'):
        user_id = int(data.split('_')[1])
        user_context = context.user_data.get(f'context_{user_id}', '')
        
        await query.message.reply_text(
            f"💡 Хочешь больше идей?\n\n"
            f"Напиши конкретнее:\n"
            f"• 'тренды в [твоя сфера]'\n"
            f"• 'как заработать на [тема] без вложений'\n"
            f"• 'создай план заработка $1000 в месяц'\n"
            f"• 'автоматизация для [задача]'"
        )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    
    user_id = update.effective_user.id
    memory_bank.get_user_profile(user_id)  # Создаём профиль
    
    await update.message.reply_text(
        "🧠 **DEEPTHINK AUTOHUSTLE ULTIMATE**\n\n"
        "Я - система из **15 AI агентов** которые работают вместе чтобы помочь тебе заработать.\n\n"
        "**МОИ АГЕНТЫ:**\n"
        "🔬 Исследователь - глубокий анализ\n"
        "📊 Рыночный аналитик - цифры и тренды\n"
        "💰 Искатель денег - способы заработка\n"
        "🏗️ Стратег - пошаговые планы\n"
        "✍️ Контент-мейкер - тексты и посты\n"
        "💻 Кодер - рабочий код\n"
        "🎨 Дизайнер продуктов - курсы, сервисы\n"
        "📢 Маркетолог - продвижение\n"
        "🤝 Продажник - воронки и скрипты\n"
        "🤖 Автоматизатор - боты и автоматизация\n"
        "⚠️ Риск-аналитик - защита от ошибок\n"
        "⚖️ Юрист - легальность\n"
        "🎯 Коуч - мотивация\n"
        "🔥 Трендхантер - горячие темы\n"
        "🧬 Синтезатор - объединяет всё\n\n"
        "**КАК ПОЛЬЗОВАТЬСЯ:**\n"
        "Просто напиши что интересует:\n"
        "• 'расскажи про криптовалюты'\n"
        "• 'как заработать на AI без вложений'\n"
        "• 'тренды 2025 для заработка'\n"
        "• 'создай курс про [тема]'\n\n"
        "🚀 **Начни прямо сейчас!**",
        parse_mode='Markdown'
    )

async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /agents - информация об агентах"""
    
    text = "👥 **ВСЕ АГЕНТЫ СИСТЕМЫ**\n\n"
    
    for name, agent in orchestrator.agents.items():
        text += f"{agent.name}\n"
        text += f"├ Роль: {agent.role}\n"
        text += f"├ Задач выполнено: {agent.tasks_completed}\n"
        text += f"└ Экспертиза: {', '.join(agent.expertise[:2])}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    
    stats = memory_bank.statistics
    
    await update.message.reply_text(
        f"📊 **СТАТИСТИКА**\n\n"
        f"💬 Запросов: {stats['total_queries']}\n"
        f"✅ Выполнено: {stats['successful_tasks']}\n"
        f"📦 Продуктов: {stats['products_created']}\n"
        f"💰 Возможностей: {stats['money_opportunities_found']}\n\n"
        f"👥 Агентов: {len(orchestrator.agents)}\n"
        f"🧠 Память: {sum(len(m) for m in memory_bank.memories.values())} записей",
        parse_mode='Markdown'
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    
    await update.message.reply_text(
        "📖 **СПРАВКА**\n\n"
        "**Команды:**\n"
        "/start - Начало работы\n"
        "/agents - Список агентов\n"
        "/stats - Статистика\n"
        "/help - Эта справка\n\n"
        "**Примеры запросов:**\n\n"
        "🔍 **Исследование:**\n"
        "'анализ рынка NFT'\n"
        "'что такое DeFi'\n\n"
        "💰 **Заработок:**\n"
        "'как заработать на фрилансе'\n"
        "'способы пассивного дохода'\n"
        "'заработок без вложений'\n\n"
        "🏗️ **Создание:**\n"
        "'создай курс по Python'\n"
        "'напиши лендинг для SaaS'\n"
        "'сделай чат-бота'\n\n"
        "📈 **Тренды:**\n"
        "'горячие тренды 2025'\n"
        "'что сейчас в хайпе'\n\n"
        "📋 **Планы:**\n"
        "'план заработка $5000/мес'\n"
        "'стратегия запуска стартапа'\n\n"
        "💡 Просто пиши что интересует - я пойму!",
        parse_mode='Markdown'
    )

# ═══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*60)
    print("🧠 DEEPTHINK AUTOHUSTLE ULTIMATE v2.0")
    print("="*60)
    print(f"\n👥 Агентов: {len(orchestrator.agents)}")
    print("🧠 Режим: Deep Thinking")
    print("💰 Цель: Автозаработок")
    print("🤖 Автоматизация: 95%+\n")
    print("="*60 + "\n")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("agents", cmd_agents))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ БОТ АКТИВЕН!")
    print("📱 Проверяй в Telegram\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
