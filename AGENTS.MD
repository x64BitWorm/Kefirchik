# AGENTS.MD

Короткая памятка для ИИ-агентов, работающих с Kefirchik.

## Что это

Kefirchik — Python Telegram-бот для учета общих трат в групповых чатах и расчета, кто кому должен. Бот парсит команды, хранит траты в SQLite, считает взаимозачеты и генерирует отчеты.

## Структура

- `Backend/main.py` — точка входа: `Config`, `DbManager`, `TgWrapper`.
- `Backend/config.py` — env-конфиг: `TG_TOKEN`, `PROXY_URL`, `MODE`, путь к SQLite.
- `Backend/tg_wrapper.py` — регистрация Telegram handlers/callbacks и общая обработка ошибок.
- `Backend/facades/handlers_facade.py` — основной сценарный слой команд `/start`, `/add`, `/report`, `/reset` и reply-сообщений.
- `Backend/facades/callbacks_facade.py` — сценарии inline-кнопок: CSV, отмена, reset, подтверждение последнего должника.
- `Backend/handlers/parsers_handler.py` — парсинг `/add`, должников, комментариев и выражений из текста.
- `Backend/handlers/spendings_handler.py` — логика заполнения трат, остатков, `x`, `s`, незаполненных должников.
- `Backend/handlers/reports_handler.py` — отчет, взаимозачеты, CSV, предупреждения о незакрытых тратах.
- `Backend/services/calculations.py` — парсер арифметических выражений и расчет долей.
- `Backend/services/formatters.py`, `constants.py`, `telegram_markups.py` — деньги, тексты и inline-кнопки.
- `Backend/database.py`, `Backend/models/db/` — SQLAlchemy, сессии, модели `Group` и `Spending`.
- `Backend/models/bot_api/` — интерфейс `IMessage` и адаптер Telegram API; через него же работают тесты.
- `Backend/models/dto/` — простые DTO для parser/report/spending.
- `Backend/migrations/` — SQL-миграции SQLite, применяются через `DbManager.applyMigrations()`.
- `Backend/tests/` — `unittest` flow-тесты с эмулятором чата.
- `Deploy/` — Dockerfile и docker-compose.

## Команды

Локально проект запускается через корневой `venv`:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Запуск локально:

```bash
source venv/bin/activate
cd Backend
TG_TOKEN='...' python3 main.py
```

Тесты:

```bash
source venv/bin/activate
cd Backend
python3 tests_runner.py
```

Docker:

```bash
docker compose -f Deploy/docker-compose.yml --env-file Deploy/.env up --build
```

## Как искать нужное место

- Новый Telegram-сценарий: начни с `Backend/facades/handlers_facade.py` или `callbacks_facade.py`, затем вынеси чистую логику в `handlers/` или `services/`.
- Меняется формат команды `/add`: смотри `parsers_handler.ParsedQuery()` и `parseSpendingBody()`.
- Меняются правила `x`, `s`, арифметики или округлений: смотри `services/calculations.py` и `services/formatters.py`.
- Меняется текст ответа бота: найди точную строку в `Backend/tests/main_flow_test.py`, потом правь handler/service.
- Меняется отчет `/report`: смотри `reports_handler.generateReport()`, `calculateTransactions()`, `getReportInfo()`, `generateCsv()`.
- Меняется поведение reply на сообщение бота: смотри `HandlersFacade.reply_command()`.
- Меняется inline-кнопка: смотри `services/telegram_markups.py` и `CallbacksFacade`.
- Меняется хранение данных: смотри `Backend/database.py`, `Backend/models/db/` и добавляй новую миграцию.
- Тестовый путь Telegram API: `tests/chat_emu.py` гоняет те же фасады через `models/bot_api/bot_api_interfaces.py`.

## Правила изменений

- Не коммить и не печатай значения из `.env`, `Deploy/.env`, `TG_TOKEN`, `PROXY_URL`.
- Не трогай пользовательскую SQLite-базу в `Database/`, если задача не про данные/миграции.
- Для изменений схемы добавляй новую SQL-миграцию с числовым префиксом в `Backend/migrations/`.
- Сохраняй текущий стиль: простой Python, `unittest`, без лишних фреймворков и крупных рефакторингов.
- Тексты ответов бота на русском проверяются тестами как точные строки; меняй их осознанно и обновляй тесты.
- Бизнес-логику держи в `handlers/` и `services/`, работу с БД — через `DbManager`/`DbSession`.
- При добавлении сценария бота сначала смотри `Backend/tests/main_flow_test.py` и добавляй похожий flow-тест в `Backend/tests/*_test.py`.
