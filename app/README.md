# Voice Sentiment

Учебный веб-сервис принимает голосовые файлы, расшифровывает речь и классифицирует тональность как `positive` или `negative`.

## Как работает

1. При открытии страницы frontend создаёт случайную UUID-сессию.
2. Аудио (`ogg/opus`, `mp3`, `wav`, `m4a`, `webm`, `mp4`) передаётся в FastAPI.
3. `faster-whisper` преобразует речь в текст. Аудиофайл затем удаляется.
4. Русский текст переводится в английский, так как приложенная TF-IDF + Logistic Regression модель обучена на Sentiment140.
5. В базу записываются расшифровка, метка, скор и уверенность.
6. Все операции с записями требуют `X-Session-ID`. Другая сессия не может получить чужую запись.
7. При закрытии страницы `sendBeacon` закрывает сессию, а все её записи получают `is_deleted = true`.

## Запуск в Docker

Из папки `app`:

```bash
docker compose up --build
```

Интерфейс: <http://localhost:8080>  
Swagger: <http://localhost:8000/docs>  
Healthcheck: <http://localhost:8000/api/health>

При первой обработке backend скачает Whisper `small` и переводчик `Helsinki-NLP/opus-mt-ru-en`. Модели кэшируются в Docker volume.

## Локальный запуск backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/api/sessions` | Создать сессию |
| `POST` | `/api/records` | Загрузить `multipart/form-data` поле `audio` |
| `GET` | `/api/records` | Записи текущей сессии |
| `GET` | `/api/records/{id}` | Одна запись текущей сессии |
| `POST` | `/api/sessions/{id}/close` | Soft delete всех записей и закрытие сессии |

## Переменные окружения

- `DATABASE_URL` — SQLite по умолчанию;
- `WHISPER_MODEL_SIZE=small`;
- `WHISPER_LANGUAGE=ru`;
- `WHISPER_DEVICE=cpu`;
- `WHISPER_COMPUTE_TYPE=int8`;
- `MAX_AUDIO_SIZE_MB=25`;
- `SENTIMENT_MODEL_PATH` — путь к `.joblib`;
- `CORS_ALLOWED_ORIGINS` — список origin через запятую.

## Тесты

```bash
cd backend
PYTHONPATH=. pytest -q
```

Интеграционные тесты проверяют создание сессий, изоляцию данных, soft delete и валидацию файлов.
