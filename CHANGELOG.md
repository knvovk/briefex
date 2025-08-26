# Changelog

Все значимые изменения в этом проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
и проект следует [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added

- (пример) Новый парсер для дополнительного источника.
- (пример) Поддержка альтернативного LLM-провайдера.

### Changed

- (пример) Переработка структуры моделей в `storage`.

### Fixed

- (пример) Исправление зависаний Celery-тасков при ретраях.

---

## [1.0.0] — 2025-08-26

Первый публичный релиз BriefEx.

### Added

- **Модуль `crawler/`**:
    - Фабрики `FetcherFactory`, `ParserFactory`, `CrawlerFactory`.
    - Реализации fetchers (`html`, `rss`): `HTMLFetcher`, `RSSFetcher`.
    - Реализация parsers (`html`, `rss`) `RT(HTMLParser)`, `GenericRSSParser`.
    - Модели для представления источников и постов.
- **Модуль `intelligence/summarization/`**:
    - Базовый summarizer и фабрика.
    - Поддержка нескольких провайдеров LLM для суммаризации.
- **Модуль `llm/`**:
    - Поддержка YandexGPT.
    - Поддержка SberGPT.
    - Общая фабрика и registry.
- **Модуль `storage/`**:
    - SQLAlchemy модели (`post`, `source` и др.).
    - Репозитории для работы с БД (`PostStorage`, `SourceStorage`).
- **Модуль `workflow/`**:
    - `crawl.py`, `summarize.py`, `clean.py` — пайплайны для задач.
    - `bootstrap.py` для инициализации системы.
- **Модуль `worker/`**:
    - Настройка Celery.
    - Планировщик (beat schedule).
    - Набор Celery-тасков для пайплайнов.
- **Конфигурация**:
    - Единый модуль `config/config.py` с загрузкой переменных окружения.
- **Инфраструктура**:
    - Dockerfile (multi-stage, dev/prod).
    - `docker-compose.dev.yml` и `docker-compose.prod.yml`.
    - Alembic миграции (`migrations/`).
    - Скрипт `scripts/seed.py` для инициализации данных.
    - Makefile: команды для up/down, миграций и публикации образа.
    - CI через GitHub Actions (`.github/workflows/ci.yml`).
    - Настройка pre-commit (Ruff lint + format).

### Changed

- Приняты единые соглашения:
    - `snake_case` для кода и БД.
    - `created_at`, `updated_at` во всех таблицах.
    - Разделение dev/prod окружений в docker-compose.

### Fixed

- Обработаны ошибки парсинга RSS/HTML (устойчивость к 404/таймаутам).
- Устранены дубли публикаций при повторном запуске workflow.
- Добавлена обработка исключений при работе с LLM-провайдерами.

### Security

- Использование встроенного `${{ secrets.GITHUB_TOKEN }}` в CI.
- Маскирование секретов в логах.
- Минимизация окружений: разные env-файлы для dev и prod.

### Docs

- README.md: запуск локально и через Docker.
- Документация разработчика: структура каталогов и описание пайплайнов.
- Комментарии в коде по ключевым классам и функциям.

---

## Ссылки

[Unreleased]: https://github.com/knvovk/briefex/compare/v1.0.0...HEAD

[1.0.0]: https://github.com/knvovk/briefex/releases/tag/v1.0.0
