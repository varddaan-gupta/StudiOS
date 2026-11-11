# StudiOS

A local-first study desktop app: courses, notes, planner, tasks, revision quizzes and a context-aware AI
assistant. The AI runs on your own computer through Ollama. Built with Python and PySide6 (Qt).

## Run it

1. Install Python 3.10+ (tick "Add python.exe to PATH" on Windows) and Ollama (https://ollama.com/download).
2. In this folder:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Mac/Linux: source .venv/bin/activate)
   pip install -r requirements.txt
   python scripts/setup_ollama.py   (downloads llama3.2:3b, about 2 GB; add a name for another model)
   python main.py
   ```
3. `python scripts/selftest.py` checks everything without Ollama.

## Structure

```
main.py                     entry point
StudiOS/
  config.py                 defaults: model, modules, exams, data folder (edit here first)
  runtime.py                AppContext (shared state), background Worker, study timer
  app.py                    splash, first-run wizard, window
  core/                     no UI code
    db.py                   SQLite document store + backup/restore
    ollama.py               Ollama client: status, pull, chat stream, JSON mode
    context.py              builds the AI system prompt from course + subject + notes
    quiz.py                 quiz prompts and validation
    stats.py                progress numbers
    favicons.py             course logos (cached)
  ui/
    theme.py                colours + stylesheet
    widgets.py              Panel, BarChart, icons, helpers
    main_window.py          dock, top bar, page switching
    pages/                  one file per module (dashboard, courses, notes, assistant,
                            planner, revision, tasks, progress, settings, wizard)
scripts/                    setup_ollama.py, selftest.py
assets/                     logos
```

Data lives in `~/.studios/studios.db` (override with the `STUDIOS_HOME` environment variable).

## Add a module

1. Create `StudiOS/ui/pages/mypage.py` with a class extending `Page` or `DynamicPage` (see `tasks.py`).
2. Add one line to `PAGES` in `StudiOS/ui/pages/__init__.py` and to `MODULES` in `config.py`.
3. Add its icon path to `ICON_PATHS` in `ui/widgets.py`.

Pages read and write data with `self.db` (`add`, `list`, `update`, `remove`), call the AI with
`self.ctx.run(...)` so the window never freezes, and switch pages with `self.ctx.go("notes", note_id=...)`.
To add a new kind of record, just use a new name in `COLLECTIONS` in `core/db.py`.
to install requirements : pip install -r requirements.txt