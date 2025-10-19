# Примеры шаблонов промптов с XML-like разметкой и мультиагентные сценарии

> Владелец: Рудаков В.Р., lefthand67@gmail.com

## 1. Простой промпт для резюме текста

```json
{
  "id": "simple_summary_v1",
  "description": "Промпт для краткого резюме текста",
  "template": "<system><instruction>Сделай краткое резюме следующего текста:</instruction><content>{input_text}</content></system>",
  "parameters": {
    "temperature": 0.3,
    "max_tokens": 400,
    "stop_sequences": ["</system>"]
  },
  "version": "1.0.0"
}
```

## 2. Промпт с требованием уточнений от модели (если нет уверенности)

```json
{
  "id": "clarify_if_needed_v1",
  "description": "Промпт, который заставляет модель задавать уточняющие вопросы при необходимости",
  "template": "<system><instruction>Отвечай на вопросы пользователя. Если не уверен в ответе, задай уточняющий вопрос.</instruction><user_query>{user_input}</user_query></system>",
  "parameters": {
    "temperature": 0.5,
    "max_tokens": 500,
    "stop_sequences": ["</system>"]
  },
  "version": "1.0.0"
}
```

## 3. Мультиагентный промпт с ролями (пример: суммаризатор + критик)

```json
{
  "id": "multi_agent_summary_critic_v1",
  "description": "Система с двумя агентами — суммаризатором и критиком",
  "template": "<system>\n<agent role=\"summarizer\">\n<instruction>Подготовь краткое резюме текста:</instruction>\n<content>{input_text}</content>\n</agent>\n<agent role=\"critic\">\n<instruction>Проверь резюме на ошибки и несоответствия фактам:</instruction>\n<summary>{summarizer_output}</summary>\n</agent>\n</system>",
  "parameters": {
    "temperature": 0.2,
    "max_tokens": 700,
    "stop_sequences": ["</system>"]
  },
  "version": "1.0.0"
}
```
