# Справочник: Локальный рендеринг Markdown-файлов

> Владелец: Вадим Рудаков, lefthand67@gmail.com

Файлы Markdown (`.md`) широко используются для документации, рабочих инструкций (runbooks) и README файлов проектов. Хотя их можно читать как обычный текст, гораздо удобнее просматривать их в отформатированном виде. Это руководство шаг за шагом показывает, как разработчики и инженеры эксплуатации могут локально визуализировать Markdown с помощью разных инструментов.

## MystMD

[MystMD](https://mystmd.org/) позволяет отображать Markdown-файлы в виде сайта с поддержкой научного контента, формул и расширенных макетов.

### Установка и запуск
1. Создать виртуальное окружение Python:
   ```bash
   python3 -m venv ~/.venv/mystmd
   source ~/.venv/mystmd/bin/activate
   ```
2. Перейти в рабочую директорию или репозиторий:
   ```bash
   cd <repo>
   ```
3. Запустить сервер Myst:
   ```bash
   myst start
   ```

### Использование
- После запуска `myst start` открыть в браузере:
  ```
  http://localhost:3000
  ```
- Markdown-файлы будут отображаться как удобный и навигационный сайт.

## Vim

Пользователи Vim могут просматривать Markdown прямо в редакторе с функцией обновления в реальном времени, используя сервер **instant-markdown-d** и плагин **vim-instant-markdown**.

### Установка
1. Установите глобальный сервер instant-markdown:
   ```bash
   npm install -g instant-markdown-d
   ```
2. Настройте плагины Vim (через vim-plug):
   ```vim
   call plug#begin('~/.vim/plugged')
   Plug 'instant-markdown/vim-instant-markdown', { 'do': 'yarn install' }
   call plug#end()
   ```

### Дополнительные настройки
Добавьте в `~/.vimrc`, при необходимости (раскомментируйте нужное):
```vim
let g:instant_markdown_slow = 1
let g:instant_markdown_autostart = 0
let g:instant_markdown_open_to_the_world = 1
let g:instant_markdown_allow_unsafe_content = 1
let g:instant_markdown_allow_external_content = 0
let g:instant_markdown_mathjax = 1
let g:instant_markdown_mermaid = 1
let g:instant_markdown_logfile = '/tmp/instant_markdown.log'
let g:instant_markdown_autoscroll = 0
let g:instant_markdown_port = 8888
let g:instant_markdown_python = 1
let g:instant_markdown_theme = 'dark'
```

### Использование
- Откройте `.md` файл в Vim.  
- Браузер автоматически откроется с рендером Markdown по адресу:
  ```
  http://localhost:8090/
  ```
- Все изменения в Vim будут моментально отображаться в браузере.

### Источники
1. [Репозиторий vim-instant-markdown на GitHub](https://github.com/instant-markdown/vim-instant-markdown)  
2. [Как просматривать Markdown в Vim](https://blog.markdowntools.com/posts/how-to-preview-rendered-markdown-in-vim)  

## Редактор Kate

[Kate](https://kate-editor.org/) — это мощный текстовый редактор с встроенной функцией просмотра Markdown.

### Использование
1. Откройте файл Markdown (`.md`) в Kate.  
2. Включите предпросмотр Markdown:
   - Меню **Инструменты** → **Markdown Preview**.  
   - Откроется разделённое окно с исходным текстом и отрендеренной версией.  
3. Просмотр можно включать и отключать в процессе редактирования.

## Заключение

- **MystMD** подходит для работы с документацией, которую удобно представлять в виде сайта, особенно для научных и технических текстов.  
- **Vim с instant-markdown** — лучший вариант для разработчиков, предпочитающих консольные инструменты и работу в реальном времени.  
- **Kate** удобен тем, кто использует графический редактор с уже встроенным предпросмотром.  

Каждый из методов позволяет быстро и удобно проверять форматирование, ссылки и визуальное оформление Markdown-файлов.
