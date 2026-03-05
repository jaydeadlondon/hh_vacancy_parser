## HH Parser

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HH Parser** — это микросервисная система для умного поиска вакансий на HH.ru с использованием AI‑анализа (GigaChat), автоматического парсинга по фильтрам пользователей и удобными уведомлениями в Telegram и веб‑интерфейсе.

Система сама:
- собирает вакансии с HH.ru по индивидуальным фильтрам пользователей;
- отфильтровывает шум на своей стороне (локальные фильтры);
- передаёт вакансии в AI‑анализатор (GigaChat);
- сохраняет результаты анализа;
- отправляет мгновенные уведомления о лучших вакансиях;
- раз в неделю формирует и рассылает Telegram‑дайджест топ‑вакансий.

---

## Архитектура

### Основные компоненты

- **API Gateway (`services/api_gateway`)**
  - FastAPI‑сервис (REST API).
  - Отвечает за:
    - регистрацию и аутентификацию пользователей;
    - управление фильтрами поиска;
    - работу с вакансиями и результатами анализа;
    - health‑чек (`/health`), OpenAPI‑документацию (`/docs`).
  - Подключён к PostgreSQL, Redis.

- **Parser Service (`services/parser_service`)**
  - Асинхронный воркер (`python -m app.worker`).
  - Периодически (раз в `PARSER_INTERVAL_SECONDS` секунд) выполняет цикл:
    1. Получает активных пользователей и их фильтры из БД.
    2. Формирует параметры для HH API (`build_hh_params`).
    3. Загружает вакансии с HH.ru (`HHClient`).
    4. Применяет локальные фильтры (`apply_local_filters`).
    5. Делает дедупликацию по пользователю (`DeduplicationService` + Redis).
    6. Сохраняет новые вакансии в БД (`get_or_create_vacancy`).
    7. Создаёт записи `VacancyAnalysis` со статусом `pending`.
    8. Публикует задания на анализ в RabbitMQ (очередь `vacancies.new`).

- **AI Analyzer (`services/ai_analyzer`)**
  - Асинхронный воркер (`python -m app.worker`), слушает очередь `vacancies.new`.
  - Для каждой вакансии:
    1. Достаёт вакансию и фильтр пользователя из БД.
    2. Собирает промпт (`build_analysis_prompt`).
    3. Запрашивает GigaChat (`GigaChatClient`).
    4. Сохраняет результат анализа в БД (`save_analysis`).
    5. Публикует событие в очередь `vacancies.analyzed` через `RabbitMQPublisher`.

- **Notifier Service (`services/notifier_service`)**
  - Асинхронный воркер (`python -m app.worker`).
  - Делает две вещи:
    - **Мгновенные уведомления**:
      - слушает очередь `vacancies.analyzed`;
      - если `score >= MIN_SCORE_FOR_INSTANT`, формирует сообщение и отправляет в Telegram (`TelegramSender`);
      - сохраняет сущность уведомления и помечает её как `sent/failed`.
    - **Еженедельный дайджест**:
      - раз в неделю (понедельник 9:00) вычисляет топ‑вакансии пользователя (`get_top_vacancies`);
      - формирует дайджест‑сообщение (`format_digest_message`) и отправляет в Telegram;
      - сохраняет и помечает уведомления.

- **Telegram Bot (`services/telegram_bot`)**
  - Aiogram‑бот (`python -m app.main`).
  - Хранит состояние в Redis (`RedisStorage`).
  - Умеет:
    - регистрировать/привязывать Telegram к пользователю (через `AuthMiddleware` и API Gateway);
    - показывать и настраивать фильтры;
    - показывать новые/топ‑вакансии;
    - работать с командами/кнопками (`handlers/start.py`, `handlers/filters.py`, `handlers/vacancies.py`, `keyboards/inline.py`).

- **Frontend (`services/frontend`)**
  - Лёгкий статический фронт на Tailwind CSS + JS (Nginx внутри контейнера).
  - Основные страницы:
    - `index.html` — экран логина/регистрации с современным тёмным UI;
    - `filters.html` — управление фильтрами;
    - `dashboard.html` — дашборд с аналитикой по вакансиям.
  - Подключается к API Gateway через JS (`js/api.js`, `js/auth.js`, `js/filters.js`, `js/dashboard.js`).

- **Shared модели (`shared/models`)**
  - Общие SQLAlchemy‑модели для всех сервисов:
    - `User`, `UserFilter`, `Vacancy`, `VacancyAnalysis`, `Notification` и др.
  - Общий логгер (`shared/utils/logger.py`).

- **Инфраструктура**
  - **PostgreSQL** — основная БД.
  - **Redis** — кэш, хранилище состояния бота, дедупликация.
  - **RabbitMQ** — шина событий между воркерами.
  - Миграции Alembic (`migrations`, `alembic.ini`, `services/api_gateway/alembic.ini`).

---

## Стек

- **Backend**: Python 3.12, FastAPI, aiogram, SQLAlchemy, Alembic.
- **Messaging**: RabbitMQ (очереди `vacancies.new`, `vacancies.analyzed` и др.).
- **Хранилища**: PostgreSQL, Redis.
- **AI**: GigaChat API.
- **Frontend**: Tailwind CSS + Nginx.
- **Оркестрация**: Docker, Docker Compose.
- **CI/CD**: GitHub Actions (`.github/workflows/ci.yml`, `.github/workflows/cd.yml`).

---

## Быстрый старт через Docker

### 1. Предварительные требования

- Установлены:
  - **Docker** `>= 24.x`
  - **Docker Compose** (v2 или встроенный в Docker Desktop).
- Есть:
  - учётные данные для **GigaChat API** (`GIGACHAT_CLIENT_ID`, `GIGACHAT_CLIENT_SECRET`);
  - токен **Telegram‑бота** (`TELEGRAM_BOT_TOKEN`), полученный у `@BotFather`.

### 2. Настройка окружения

В корне репозитория есть файл `.env.example`. Создай `.env`:

```bash
cp .env.example .env
```

Отредактируй `.env`, минимум:

- **PostgreSQL**:
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
- **GigaChat**:
  - `GIGACHAT_CLIENT_ID`
  - `GIGACHAT_CLIENT_SECRET`
  - при необходимости `GIGACHAT_SCOPE`
- **Telegram**:
  - `TELEGRAM_BOT_TOKEN`
- **API Gateway**:
  - `API_SECRET_KEY` — замени на сильный секрет;
  - `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` — опционально.
- **Parser**:
  - `PARSER_INTERVAL_SECONDS` — период между циклами парсинга (по умолчанию 3600 c).

При локальном запуске через Docker значения хостов по умолчанию (`POSTGRES_HOST=postgresql`, `REDIS_HOST=redis`, `RABBITMQ_HOST=rabbitmq`) менять не нужно — они совпадают с именами сервисов в `docker-compose.yml`.

### 3. Запуск всех сервисов

Из корня проекта:

```bash
docker compose up -d --build
```

Будут подняты:

- `postgresql` (PostgreSQL, порт `5432`);
- `redis` (Redis, порт `6379`);
- `rabbitmq` (порт `5672`, UI на `15672`);
- `api-gateway` (FastAPI, порт `8000`);
- `parser-service` (воркер парсинга);
- `ai-analyzer` (AI‑анализатор);
- `notifier-service` (уведомления и дайджесты);
- `telegram-bot` (Aiogram‑бот);
- `frontend` (Nginx с фронтом, порт `3000`).

Логи конкретного сервиса:

```bash
docker compose logs -f api-gateway
docker compose logs -f parser-service
docker compose logs -f ai-analyzer
docker compose logs -f notifier-service
docker compose logs -f telegram-bot
docker compose logs -f frontend
```

Остановка:

```bash
docker compose down
```

---

## Доступы после запуска

- **Frontend**: `http://localhost:3000`
  - экраны входа/регистрации;
  - управление фильтрами и просмотр аналитики.

- **API Gateway**:
  - базовый URL: `http://localhost:8000`
  - документация: `http://localhost:8000/docs`
  - корневой эндпоинт: `GET /` возвращает JSON с названием сервиса.

- **RabbitMQ Management UI**:
  - `http://localhost:15672`
  - логин/пароль — из `.env` (`RABBITMQ_USER`, `RABBITMQ_PASSWORD`).

- **PostgreSQL**:
  - хост: `localhost`
  - порт: `5432`
  - логин/пароль/БД: см. `.env`.

---

## Типичный пользовательский сценарий

1. **Регистрация**
   - Пользователь заходит на `http://localhost:3000`.
   - Регистрирует аккаунт через форму регистрации (или через API Gateway напрямую).

2. **Привязка Telegram**
   - Пользователь запускает Telegram‑бота.
   - Проходит авторизацию/линковку аккаунта через команды бота (AuthMiddleware проверяет токен/пользователя через API Gateway).

3. **Настройка фильтров**
   - Через веб‑интерфейс или Telegram задаёт фильтры поиска (по должности, зарплате, региону и т.д.).

4. **Фоновый парсинг**
   - `parser-service` по расписанию забирает вакансии с HH.ru по фильтрам.
   - Результаты публикуются в RabbitMQ (`vacancies.new`) для AI‑анализа.

5. **AI‑анализ**
   - `ai-analyzer` получает задания, вызывает GigaChat и сохраняет скор и рекомендации.

6. **Уведомления**
   - `notifier-service`:
     - моментально уведомляет о вакансиях выше порога привлекательности (instant);
     - раз в неделю отправляет дайджест лучших вакансий за период.

---

## Структура проекта

Основные директории:

- `services/api_gateway` — API Gateway (FastAPI, Alembic, схемы, роутеры).
- `services/parser_service` — воркер парсинга HH.ru.
- `services/ai_analyzer` — AI‑анализатор с GigaChat.
- `services/notifier_service` — уведомления и еженедельные дайджесты.
- `services/telegram_bot` — Telegram‑бот на aiogram.
- `services/frontend` — статический фронтенд (HTML + Tailwind + JS + Nginx).
- `shared/models` — общие модели и утилиты.
- `migrations` — миграции БД (основная схема).
- `.github/workflows` — пайплайны CI/CD.
- `docker-compose.yml` — оркестрация всех сервисов.

---

## Локальная разработка (по сервисам)

> Для большинства задач достаточно Docker‑запуска. Ниже — общая схема, если нужно отлаживать конкретный сервис локально.

Пример: запуск только `api_gateway` локально (остальные — в Docker):

1. Поднять инфраструктуру и, при желании, воркеры:

```bash
docker compose up -d postgresql redis rabbitmq
```

2. Установить зависимости для `api_gateway`:

```bash
cd services/api_gateway
pip install -r requirements.txt
```

3. Экспортировать переменные окружения (или использовать `.env` через `python-dotenv`).

4. Запустить:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Аналогично можно поднимать и отлаживать `parser_service`, `ai_analyzer`, `notifier_service` и `telegram_bot`, используя их `requirements.txt` и точки входа (`app.worker` / `app.main`.

---

## Миграции БД

Для работы используются Alembic‑миграции.

Пример (для основного набора миграций в корне):

```bash
alembic upgrade head
```

Миграции для API Gateway (если запускается отдельно):

```bash
cd services/api_gateway
alembic upgrade head
```

---

## Переменные окружения

Список основных переменных смотри в файле `.env.example`. Кратко:

- **PostgreSQL**
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
- **Redis**
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- **RabbitMQ**
  - `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_HOST`, `RABBITMQ_PORT`
- **API Gateway**
  - `API_SECRET_KEY`, `API_HOST`, `API_PORT`,
  - `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- **HH.ru API**
  - `HH_API_BASE_URL`, `HH_USER_AGENT`
- **GigaChat**
  - `GIGACHAT_CLIENT_ID`, `GIGACHAT_CLIENT_SECRET`, `GIGACHAT_SCOPE`
- **Telegram**
  - `TELEGRAM_BOT_TOKEN`
- **Parser**
  - `PARSER_INTERVAL_SECONDS`
- **Общее**
  - `ENVIRONMENT` (`development` / `production`),
  - `DEBUG` (`true` / `false`).

---

## CI/CD

В проекте настроены GitHub Actions:

- `.github/workflows/ci.yml` — сборка, тесты, базовая проверка кода.
- `.github/workflows/cd.yml` — развёртывание (детали зависят от целевой инфраструктуры).

## License

MIT License
