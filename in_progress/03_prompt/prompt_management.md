# Стандарты, хранение и автоматизация промптов в AI CI/CD

> Владелец: Вадим Рудаков, lefthand67@gmail.com
> Версия: 0.1.0

Статья посвящена методам формализации и стандартизации промптов как ключевых разработческих артефактов. Рассмотрены принципы хранения промптов в структурированных форматах JSON и YAML с применением внутренней XML-подобной разметки для семантической организации. Описаны подходы декларативного дизайна, семантического версионирования и автоматической проверки (валидации) с помощью схем и Pydantic. Показана организация статических и динамических частей промптов для масштабируемого и безопасного использования в пайплайнах AI CI/CD с сопровождением юнит-тестами. Статья служит фундаментом для качественного промышленного prompt management.

**ВНИМАНИЕ!** В статье описаны ручные способы генерации и валидации промптов, в то время как на сентябрь 2025 г. в мире существует несколько развитых фреймворков, автоматизируюших и упрошающих эту работу. Ручная проверка JSON/YAML + схемы — это метод начального уровня, но он всё ещё актуален. Данная статья должна рассматриваться как низко-уровневое учебное пособие: базовые навыки по-прежнему важны, потому что производственные фреймворки — это абстракции, построенные именно на этих примитивах (структурированные файлы, проверка схемы, возможность сравнения и т. д.). Команды, которые не владеют базовыми концепциями, часто неправильно используют фреймворки более высокого уровня.

**ВНИМАНИЕ!** В статье описаны базовые, «ручные» подходы к генерации, хранению и валидации промптов. На сентябрь 2025 г. в индустрии применяются развитые фреймворки (Prompt Flow, LangChain PromptHub, Semantic Kernel,  и др.), которые автоматизируют хранение, валидацию, аудит, A/B‑тестирование и оптимизацию промптов. Материал ниже стоит рассматривать как низкоуровневый фундамент, необходимый для понимания принципов, на которых строятся такие системы. В промышленных пайплайнах рекомендуется использовать готовые фреймворки, сочетая их с ручными методами там, где требуется тонкая настройка или интеграция.

---

> *Промпт ≠ код, но это артефакт разработки, который тоже должен иметь стандарты.*

# 1. Хранение и версионирование промптов  

All prompts, templates, and their metadata should be stored in **structured formats** (JSON or YAML). This means 

> you don’t just dump text in files or copy-paste inline prompts into your code, but instead treat prompts as **first-class configuration artifacts**.
  
## 1.1 Why JSON/YAML?

Такой подход обеспечивает:

1. **Integration with version control (Git)**
   - When prompts are stored as structured files, Git can easily diff them and track changes over time.
   - Example: If tomorrow you tweak the “temperature” from `0.3` to `0.4`, a Git diff shows exactly that – useful for audits and reproducibility.

2. **Machine readability & automatic validation**
   - Structured formats let you write validators / linters (e.g., JSON Schema, `pydantic`, or OpenAPI-like checks).
   - This prevents errors like missing placeholders (`{text}`), invalid parameter values, or inconsistent naming.

3. **Ease of generating variations & test suites**
   - Because prompts are data, you can programmatically generate **A/B/C variants** (e.g., different tones for summarization).
   - You can also automatically assemble benchmark prompt-test sets to ensure new model versions behave consistently.

> **Pitfall warning**: If you keep prompts as free-form strings scattered across codebases or in wikis, you lose change tracking and won’t know *exactly* what version of a prompt produced some system output. This becomes a serious problem once your system is deployed in production and you need reproducibility.

## 1.2 Внешний и внутренний слои промпта

- **Внешний слой**: все промпты, шаблоны, метаданные хранятся в формате JSON или YAML.
    - Это облегчает версионирование, автоматическую обработку, интеграцию с CI/CD и совместную работу через Git.
    - Формат легко читается и поддерживается всеми инструментами разработки.
- **Внутренний слой** (внутри самого промпта): для семантической структуризации текста промпта (ролей, инструкций, этапов) использовать XML-like разметку.
    - Это помогает модели чётко понимать разные блоки, снижает риск неправильного понимания или смешения команд.
    - Такой подход признан best practice у ведущих LLM-провайдеров.

### Пример разделения хранения промптов и внутренней разметки (JSON/YAML + XML-like внутри)

**Идея**
  
- Промпты **хранятся** как структурированные данные в JSON (или YAML). Эта структура — «контейнер», который удобно версионировать, искать, валидировать.  
- **Внутри** программного поля `template` находится текст промпта с **XML-подобной семантической разметкой** для точного структурирования контента, понятного модели.

> Внимание! XML — один из вариантов структурирования данных, но в зависимости от поставщика JSON или блоки Markdown могут работать лучше.

**Пример на JSON (хранение)**

```json
{
  "id": "example_prompt_v1",
  "description": "Промпт для суммаризатора с внутренней XML-разметкой",
  "version": "1.0.0",
  "template": "<system><instruction>Сделайте краткое резюме текста ниже.</instruction><content>{input_text}</content></system>",
  "parameters": {
    "temperature": 0.2,
    "max_tokens": 512
  }
}
```

**Объяснение**

- Внешний JSON — машиночитаемый и легко обрабатывается CI/CD.  
- Внутренний текст — отслеживается как одна строка с XML-разметкой для семантики.  
- Промпт может динамически подставлять переменные, например, `{input_text}`.  
- Все изменения — коммитятся и отслеживаются как JSON-файлы, не ломая структуру.

# 2. Выбор формата хранения промпта

## Prefer declarative design

You should **store your prompt definitions purely as data or configuration files**, separating the "what" (the prompt and its parameters) from the "how" (the business logic that uses or manipulates the prompt).

**Explanation**

- **Declarative design** focuses on describing *what* you want, not *how* to do it.
- In this case, you declare the prompt text, placeholders, and parameters (like `max_tokens`, `temperature`) as simple data structures (for example, YAML or JSON).
- This is opposed to embedding the prompt text and its logic as code, e.g., hardcoding prompt strings directly in your functions or mixing business logic with prompt generation.

**Benefits of declarative design in prompt engineering**

1. **Reusability and consistency:**  
   The same prompt definition can be loaded and reused across different components — for example, training pipelines, validation scripts, and inference servers. This enforces consistent behavior.

2. **Separation of concerns:**  
   You keep business logic (data flow, decision making) separate from prompt content. This simplifies maintenance and evolution of both parts independently.

3. **Validation and automation:**  
   Because the prompt is data-only, you can automatically validate it against schemas (checking required fields, placeholders) and automate tasks like placeholder substitution without custom parsing.

4. **Easier collaboration:**  
   Non-developers (prompt designers, linguists) can review and edit prompt configs easily without digging into code.

Example YAML prompt template usable by training and serving systems:

```yaml
id: summarizer_v1.1.0
description: Generic summarizer prompt
template: |
  <instruction>Summarize the following text:</instruction>
  <content>{text}</content>
parameters:
  max_tokens: 512
  temperature: 0.3
```

Because this is declarative (data-only), pipelines can load, validate, substitute placeholders, and use it consistently:
- This YAML is *only data*: no embedded logic about how to use it or how to substitute `{text}`.  
- Code pipelines load this YAML, validate its correctness, substitute `{text}` dynamically, and provide parameters when calling the model.  
- This approach makes prompt management far more scalable and less error-prone.

## YAML over JSON?

You don’t have to strictly prefer YAML over JSON, but YAML often offers practical advantages for prompt configuration in AI projects, especially when you emphasize declarative design:

**Why YAML can be preferable for prompt definitions**

- **More human-readable:** YAML is less cluttered, using indentation instead of braces and quotes, making it easier to read and maintain by humans and teams.
- **Supports comments:** You can include inline comments in YAML files, which is very helpful for explaining prompt purpose, parameters, or usage notes right next to the data. JSON lacks native comment support.
- **Token efficiency:** When prompts or configurations are sent to language models as context, YAML generally consumes fewer tokens due to simpler syntax, thus potentially lowering cost or improving performance.
- **Better version diffing:** YAML files are easier to scan for changes at a glance in Git because of line-based structure and lack of brackets or commas.
- **Supports complex data types:** YAML can express nested lists and mappings more naturally.

**When JSON might still be better**

- **Broader native tooling and integration:** JSON parsing is natively supported in almost every language without extra libraries. YAML parsing often requires third-party libraries.
- **Simplicity for machines:** JSON’s strict and minimal syntax is easier and faster for machines to parse and generate reliably, with fewer edge cases.
- **API compatibility:** Many APIs and web services expect JSON payloads.

**Summary**

| Aspect               | YAML                                   | JSON                           |
|----------------------|---------------------------------------|--------------------------------|
| Readability          | Easier for humans, supports comments  | Less readable, no comments      |
| Token usage with LLM  | Generally lower (better for cost)     | Slightly higher                 |
| Parsing support      | Requires libraries                    | Native in most languages        |
| Use in practice      | Better for config/prompt files handled by teams | Better for API data exchange    |
| Version control diff | Cleaner diffs                         | Cluttered diffs with brackets  |

For **declarative prompt/configuration files** that are edited, reviewed, and version-controlled by humans, **YAML is often the better choice**. For **machine-to-machine direct API payloads or simple tooling without dependencies, JSON may be preferred**.

> Совет: Ведите промпты в формате YAML, но перед отправкой в LLM генерируйте из них JSON.

> Внимание! Преобразование YAML в JSON для отправки в LLM может сопровождаться дрейфом при переносе строки/токенизации. Это приводило к проблемам при реальном развертывании.

# 3. Структура внешнего слоя промпта

- **Add metadata fields such as `author`, `created_at`, `last_modified`** → makes auditing easier.
- **Version IDs should be explicit and immutable** → never silently edit `summarizer_v1`. If it changes logically, bump to v2.
- **Prefer declarative design** → the same JSON/YAML file should be loadable by both training pipelines and serving systems.
- **Schema validation** → define a JSON Schema (or use `pydantic` in Python) so that broken prompts (missing placeholders, invalid params) get caught in CI/CD.
- **Unit test prompts** → yes, prompts can (and should) be tested with golden inputs/outputs in your repo. This prevents regression.

## Пример

### Шаблон

```yaml
---
id: {{ id }}
version: {{ version }}
description: {{ description }}
author: {{ author }}
created_at: {{ created }}
last_modified: {{ _modified }}
---

parameters: {{ parameters }}
system: {{ system_prompt }}
user: {{ user_prompt }}
examples: {{ examples }}
```

где:

1. **id**: Уникальный идентификатор промпта. Используется для группировки всех версий одной и той же логической сущности (например, `summarizer`).

2. **version**: Семантическая версия (`1.2.3`), которая описывает совместимость:
   * `1` — мажорная версия (несовместимые изменения).
   * `2` — минорная версия (новый функционал, совместимый с предыдущим).
   * `3` — патч (исправления и уточнения без изменения логики).

3. **description**: Человекочитаемое описание назначения промпта.

4. **author / created\_at / last\_modified**: Метаданные для аудита: кто создал, когда, и когда последний раз изменял.

5. **parameters**: Настройки LLM (например, `max_tokens`, `temperature`). Подставляются динамически.

6. **system\_prompt**: Базовые инструкции, определяющие поведение модели (её «роль»).

8. **user\_prompt**: Шаблон для ввода пользователя, содержащий плейсхолдеры (например, `{text}`).

9. **examples**: Примеры входов и ожидаемых выходов (few-shot). Удобны для тестирования и обучения.
   
**Валидация схемы в CI**:
- YAML → JSON → проверка через JSON Schema.

> `system` → роль, правила поведения, ограничения.
> 
> `user` → конкретный ввод, шаблон (может быть сгенерирован из блоков).
> 
> `examples` → отдельный блок, подставляемый по необходимости (few-shot или тесты).

### Результат генерации

```yaml
---
id: summarizer
version: "1.2.3"
description: "Промпт для модели-суммаризатора"
author: "team-a"
created_at: "2025-09-12"
last_modified: "2025-09-12"
---

parameters:
  max_tokens: 512
  temperature: 0.3

system: |
  Ты — ассистент, который делает краткие и точные резюме.

user: |
  Сделайте краткое резюме текста:
  "Вчера в Берлине состоялась конференция по вопросам устойчивого развития..."

examples:
  - input: "Текст статьи про изменение климата"
    output: "Краткое резюме: ..."

```

### Реальные примеры

**[Microsoft's Prompt Flow](https://microsoft.github.io/promptflow/how-to-guides/quick-start.html)**:  

```yaml
---
name: Minimal Chat
model:
  api: chat
  configuration:
    type: azure_openai
    azure_deployment: gpt-35-turbo
  parameters:
    temperature: 0.2
    max_tokens: 1024
inputs:
  question:
    type: string
sample:
  question: "What is Prompt flow?"
---

system:
You are a helpful assistant.

user:
{{question}}
```

## Статические (system) vs динамические (user) части промпта

**Системный промпт** — это уровень, где задаются ключевые параметры вычислительной логики: определяются персона (роль модели), рабочий процесс, действующие ограничения и формат выходных данных с высокой структурной сложностью. Его можно рассматривать как «операционную систему» для взаимодействия.

**Промпт пользователя**, напротив, должен оставаться лёгким и минималистичным: в нём фиксируется только конкретная задача и входные данные для текущего запуска. Ваш пример служит корректным и практически применимым шаблоном такого промпта.

- **Static parts (system)** of a prompt are the **fixed, unchanging instructions or context** that define the task, model behavior, or overall settings.  
  For example, this can be the system message that sets the AI's role, global rules, or formatting instructions. This part usually stays the same across many uses.

- **Dynamic parts (user)** are the **variable inputs or data** provided at runtime that change for each specific request or session.  
  Examples: the user’s query, specific content to summarize, or contextual details unique to each call.

Separating these parts:

- Makes prompts **easier to adapt** because you can change user input without rewriting the whole prompt.
- Improves **reusability**, since the same static framework can serve many different requests.
- Enhances clarity in prompt management and facilitates automation in pipelines, as static and dynamic sections can be maintained, validated, and updated independently.

**Example structure in practice:**

```yaml
system:
  id: {{ id }}
  version: {{ version }}
  content: {{ content }}
```

```yaml
user:
  id: {{ id }}
  version: {{ version }}
  template: {{ prompt_text }}
```

- The **system** part defines the assistant role and rules once.  
- The **user** part is plugged in with actual variable input (`{text}`) at runtime.

This is a widely used pattern in conversational AI APIs like OpenAI’s chat completions, where you pass separate `system` and `user` messages, reflecting static and dynamic prompt parts respectively.

```yaml
system_prompt:
  id: system_instructions_v1
  content: |
    You are a helpful assistant. Always respond politely and concisely.
    Follow JSON format in output.
```

```yaml
user_prompt:
  id: user_prompt_v1
  template: |
    Summarize the following text:
    {{ text }}
```

где `{{ text }}` также является внешним блоком, который подставляется в данный пользовательский промпт.

### Пример более продвинутого шаблона

```yaml
---
system:
    id: {{id}}
    version: {{version}}
    description: {{description}}
    metadata:
      author: {{author}}
      created_at: {{created_at}}
      domain: {{domain_description}}
      tech_stack: {{tech_stack_list}}
      last_validated: {{validation_date}}
      validation_notes: {{validation_notes}}

  # Core prompt components
  prompt_components:
    role:
      description: "AI persona definition and expertise domain"
      content: {{role_content}}

    context:
      description: "How to handle provided background information"
      content: {{context_handling_instructions}}

    process:
      description: "Step-by-step reasoning approach"
      content: {{step_by_step_process}}

    constraints:
      description: "Limitations and boundaries for responses"
      content: {{constraints_list}}

    examples:
      description: "Input-output pairs demonstrating desired behavior"
      content: {{few_shot_examples}}

    output_format:
      description: "Required structure and format for responses"
      content: {{format_specification}}

  # Inference parameters
  inference_parameters:
    temperature: {{temperature_setting}}
    max_tokens: {{max_output_length}}
    stop_sequences: {{stop_sequences}}

  # Validation framework
  validation:
    test_cases: {{test_case_references}}
    evaluation_metrics: {{metric_definitions}}
    compliance_requirements: {{compliance_rules}}
```

- `validation notes` - That line is a concise testament to the prompt's quality, reliability, and the domains where it has proven effective. It's a best-practice piece of metadata that should be included in any serious, production-level system prompt. **In simple terms**, it means: The creators of this system prompt didn't just assume it would work. They rigorously tested it on realistic example scenarios from two different domains (e-commerce and AI agents) to ensure it produces high-quality, reliable results before declaring it ready for use.

- `stop_sequences` - This is a specific instruction for the Language Learning Model (LLM) itself, telling it when to stop generating text.When the model generates text and encounters one of these exact sequences, it immediately stops generating any further text. The purpose is to give the AI a clear, unambiguous signal that it has reached the end of its assigned task and should not continue.

#### Max tokens

Remember that your prompt is also taking the tokens, for example:

Your prompt has tokens: 1,246
Your max_tokens: 4096 
The AI response may use: 4096 - 1246 = 2850 tokens.

For models with a **4k context window** (e.g., older GPT-3.5 models): 
- 4096 is the absolute maximum you can ask for. You must be very conservative with your system prompt and user input length to leave enough room for the output. This is tight and risky.

For models with a **16k context window** (e.g., gpt-3.5-turbo-16k, claude-3-sonnet): 
- You can safely increase this to max_tokens: 12288 to leave ample headroom for large outputs.

For models with a **128k context window** (e.g., gpt-4-turbo, claude-3-opus): 
- You can set this much higher, e.g., max_tokens: 32768, with no issues.

# 4. Schema validation

> Требуется проработка и валидация информации

Define a JSON Schema (or Pydantic model in Python, or XML) to validate prompt files automatically. Example:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "description", "template", "parameters"],
  "properties": {
    "id": { "type": "string" },
    "description": { "type": "string" },
    "template": { "type": "string" },
    "parameters": {
      "type": "object",
      "properties": {
        "max_tokens": { "type": "integer", "minimum": 1 },
        "temperature": { "type": "number", "minimum": 0, "maximum": 1 }
      },
      "required": ["max_tokens", "temperature"]
    },
    "author": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "last_modified": { "type": "string", "format": "date-time" }
  }
}
```

This schema helps catch issues like missing placeholders, out-of-range parameters, or missing metadata during CI/CD before deploying prompts.

### Pydantic model

Pydantic is a popular data validation and settings management library in Python. It provides a way to define **models** that describe the expected structure of your data and automatically **validate** and **parse** input data against those models:
- Pydantic models let you **declare expected data structures with types in Python**.
- They **validate and parse input data automatically** to make sure it’s correct and consistent.
- Ideal for **schema validation of AI prompt files**, configs, or any structured input.

**What is a Pydantic model?**

- A **Pydantic model** is a Python class that inherits from `pydantic.BaseModel`.
- Inside the class, you declare **fields with types** which represent the expected shape and type of your data.
- When you create an instance of that model with input data (e.g., from JSON), Pydantic automatically:
  - Checks that the input adheres to declared types and constraints.
  - Converts input data types if possible (e.g., parsing strings to dates).
  - Raises clear errors if validation fails.
- This helps enforce **schema validation** programmatically in Python.

**Why use Pydantic models for prompt files?**

- You can **validate prompt definitions** (like your JSON/YAML prompt files) before using them in your pipeline.
- Ensures no missing fields, correct data types, and valid parameter ranges.
- Provides detailed error messages which can be caught during testing or CI.
- Makes your prompt-loading code more robust and maintainable.

**Simple example of a Pydantic model for a prompt file:**

```python
from pydantic import BaseModel, Field
from typing import Dict

class PromptModel(BaseModel):
    id: str
    description: str
    template: str
    parameters: Dict[str, float] = Field(default_factory=dict)
    author: str = None
    created_at: str = None
    last_modified: str = None

# Example usage
data = {
    "id": "summarizer_v1",
    "description": "Prompt for text summarization",
    "template": "<instruction>Summarize:</instruction>\n<content>{text}</content>",
    "parameters": {"max_tokens": 512, "temperature": 0.3},
    "author": "Jane Doe",
    "created_at": "2025-08-01T12:00:00Z"
}

prompt = PromptModel(**data)  # Validates input here

print(prompt.id)  # Access fields normally
```

If input data violates the schema (e.g., missing `id` or wrong type), Pydantic will raise an error immediately.

### Unit test prompts

Example test case in Python pseudocode:

```python
def test_summarizer_prompt_format():
    prompt = load_prompt("summarizer_v1.json")
    input_text = "OpenAI is an AI research lab."
    full_prompt = prompt["template"].format(text=input_text)
    
    # Assert placeholder substitution
    assert "{text}" not in full_prompt
    
    # Assert key elements present
    assert "Summarize the following text:" in full_prompt
    assert input_text in full_prompt

    # Optionally, call mock model and verify output format
    mock_output = mock_model_response(full_prompt)
    assert isinstance(mock_output, str) and len(mock_output) > 0
```

Having tests ensures prompt changes don't break formatting or expected behavior, preventing regressions in production.
