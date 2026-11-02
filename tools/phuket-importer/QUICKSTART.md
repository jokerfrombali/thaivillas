# Быстрый запуск Phuket Importer

1. Открой Docker Desktop и дождись статуса «Docker is running».
2. В PowerShell:

```powershell
cd <папка репозитория thaivillas>\tools\phuket-importer
.\run.ps1
```

3. Открой http://localhost:8093
4. Выбери сайт `getyourphuket.com`, нажми **«Скачать весь сайт»** и дождись надписи «готово».
5. Повтори для `indreamsphuket.ru`.

Результат появится в `imports\getyourphuket-all-<дата>\` и `imports\indreams-all-<дата>\`.
Открой там `index.html`, чтобы посмотреть, что скачалось.

## Как отдать результат, чтобы он появился на сайте

Папка `imports/` не попадает в git автоматически (в ней много фото). Залей её в отдельную ветку:

```powershell
git checkout -b imports
git add -f imports
git commit -m "Imported listings"
git push -u origin imports
```

Потом напиши Claude «залил импорт в ветку imports» — объекты, тексты и фото будут перенесены на сайт.
