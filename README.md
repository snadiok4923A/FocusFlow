# FocusFlow — Personal Productivity Manager

A more substantial Python portfolio project for task management, habit tracking, productivity statistics, and CSV export. Built with Python's standard library and SQLite; no pip installs required.

## Features
- Create tasks with descriptions, priority, and optional due dates
- Filter tasks by open/completed status
- Complete and delete tasks
- Create habits and log each habit once per day
- Track current streak, monthly activity, and total habit logs
- Dashboard with open/completed/overdue task counts
- Export task data to CSV
- Persistent SQLite database
- Automated unit tests

## Requirements
Python 3.9+; no third-party packages.

## Run
```bash
python focusflow.py
```
On some systems, use `python3 focusflow.py`. A local `focusflow.db` database is created automatically.

To choose another database:
```bash
python focusflow.py --db ./data/focusflow.db
```

## Test
```bash
python -m unittest discover -s tests -v
```

## Files
```text
FocusFlow-Productivity-Manager/
├── focusflow.py
├── tests/
│   └── test_focusflow.py
├── README.md
├── LICENSE
└── .gitignore
```

## Suggested future upgrades
- Streamlit dashboard with charts
- Search and advanced filters
- Weekly/monthly reports
- Reminders
- Cloud sync or a REST API

## Privacy
Your tasks and habits are stored locally in `focusflow.db`. Do not commit your personal database to a public repository.

## License
MIT License. See `LICENSE`.
