# Kolos Desktop Updater

Запуск:

```bat
run_updater.bat
```

Або напряму:

```bat
venv\Scripts\python.exe -m updater.main
```

Updater працює напряму через Git:

- перевіряє `origin/main`;
- показує локальний і віддалений commit;
- показує changelog нових комітів;
- перед оновленням створює backup `db.sqlite3` у `backups/YYYY-MM-DD/`;
- виконує `git fetch origin`, `git reset --hard origin/main`;
- запускає `python manage.py migrate`;
- якщо існує `requirements.txt`, запускає `python -m pip install -r requirements.txt`.

Опційний файл налаштувань `updater_config.json` створюється при зміні папки backup. Команду перезапуску можна задати через змінну середовища `KOLOS_RESTART_COMMAND`.

