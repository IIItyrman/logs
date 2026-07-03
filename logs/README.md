# 🪵 Система логирования микросервисов (учебный проект)

Простая система централизованного сбора логов с двух микросервисов: `user-service` и `order-service`. Логи пишутся в **JSON-формате** в stdout, собираются **Docker Loki Driver** и визуализируются в **Grafana**.

## 🏗️ Архитектура

```
┌──────────────┐      HTTP       ┌───────────────┐
│ user-service │ ───────────────→ │ order-service │
│   :8001      │   X-Trace-Id    │    :8002       │
└──────┬───────┘                  └──────┬────────┘
       │ JSON stdout                     │ JSON stdout
       ▼                                 ▼
┌─────────────────────────────────────────────────┐
│              Docker Loki Driver                 │
└─────────────────────┬───────────────────────────┘
                      ▼
              ┌──────────────┐
              │    Loki      │  ← хранилище логов
              │   :3100      │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │   Grafana    │  ← дашборды и поиск
              │   :3000      │
              └──────────────┘
```

- **user-service** — отдаёт профили пользователей, вызывает `order-service` для создания заказов
- **order-service** — создаёт заказы, имитирует ошибки (10% шанс), отдаёт статус заказов

## 🚀 Быстрый старт

### 1. Запустить всё

```bash
docker compose up -d
```

### 2. Проверить, что всё работает

```bash
# Здоровье сервисов
curl http://localhost:8001/health
curl http://localhost:8002/health

# Получить пользователя
curl http://localhost:8001/users/1

# Создать заказ (user-service → order-service)
curl -X POST "http://localhost:8001/users/1/order?item=laptop&quantity=2"

# Посмотреть статус заказа (замени ORDER_ID на реальный)
curl http://localhost:8002/orders/{ORDER_ID}

# Нагрузить систему (сгенерировать больше логов)
for i in $(seq 1 20); do curl -s -X POST "http://localhost:8001/users/1/order?item=laptop&quantity=2" & done
```

### 3. Открыть Grafana

Перейди на **http://localhost:3000** (логин не требуется, анонимный доступ включён).

Источник данных **Loki** уже добавлен автоматически.

## 📊 LogQL — поиск по логам

В Grafana перейди в **Explore** → выбери источник **Loki** и попробуй:

### Все логи сервиса
```logql
{service="user-service"}
```

### Только ошибки
```logql
{service="order-service"} | level="ERROR"
```

### Логи по trace_id (отследить всю цепочку одного запроса)
```logql
{env="dev"} | json | trace_id="<вставь trace_id из ответа API>"
```

### Самые медленные запросы (> 100 ms)
```logql
{env="dev"} | json | duration_ms > 100
```

### Количество запросов в минуту по сервисам
```logql
rate({env="dev"} | json | path!~"/health" |= "method"[1m])
```
*(В Grafana выбери визуализацию «Time series»)*

## 📁 Структура проекта

```
logs/
├── docker-compose.yml              # Все сервисы
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI: /users, /users/{id}/order
│       └── logger.py               # JSON-логгер
├── order-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI: /orders
│       └── logger.py               # JSON-логгер
├── loki/
│   └── local-config.yaml           # Конфиг Loki
├── grafana/
│   └── datasources/
│       └── loki.yml                # Автонастройка источника Loki
└── README.md
```

## 🛑 Остановка

```bash
docker compose down
```

## 🔑 Ключевые концепции для обучения

1. **Структурированные логи** — каждый лог в JSON содержит: `timestamp`, `level`, `service`, `trace_id`, `message`, `method`, `path`, `status_code`, `duration_ms`
2. **Trace ID** — пробрасывается через `X-Trace-Id` между сервисами, позволяет найти все логи одного запроса
3. **Docker Loki Driver** — собирает stdout контейнеров без агентов
4. **LogQL** — язык запросов Loki, похож на PromQL
5. **Graceful degradation** — order-service иногда падает, user-service логирует ошибку (HTTP 502)

## 🧪 Учебные задания

- Найди в Grafana все запросы, которые завершились с ошибкой (status_code >= 500)
- Построй график количества запросов в минуту для каждого сервиса
- Найди самый медленный запрос за всё время
- Возьми trace_id из ответа API и проследи всю цепочку от user-service до order-service
- Настрой Alert в Grafana на количество ошибок (>5 за 5 минут)
