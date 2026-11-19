# Репрезентация психологии в кино

Статический сайт DH-прототипа: как кино и сериалы репрезентируют профессию психолога. Девять закодированных произведений, словарь категорий и seven-glavная история.

Сайт собирается как project site для GitHub Pages с базовым путём `/representation-psychology/`.

## Команды

```bash
npm install
npm run dev     # проверка медиареестра + ETL + astro dev
npm run data    # только ETL: xlsx → public/data/*.json + отчёт валидации
npm run validate:media # проверка медиареестра и запрета непроверенной публикации
npm run test:media # регрессионные тесты медиавалидатора
npm run build   # проверка медиареестра + ETL + astro build → dist/
npm run preview # предпросмотр dist/
```

Python-часть требует `.venv` с `requirements.txt` или системный Python с теми же пакетами (`pandas`, `openpyxl`, `pyyaml`, `jsonschema`). `scripts/etl.sh` использует `.venv/bin/python`, если он есть.

## Структура

- `materials/` — исходные документы и исходные медиаматериалы; в сборку не входят.
- `materials/media/` — правила учёта, проверка и очередь фотографий/кадров.
- `data/media-assets.yml` — реестр кандидатов и утверждённых изображений.
- `data/source/` — `coding.xlsx` (без имён кодеров), `codebook.yml`, `works.yml`.
- `data/etl/` — извлечение, нормализация, валидация, отчёт.
- `data/schemas/` — JSON Schema для публикуемых файлов.
- `data/out/` — непубликуемые артефакты (`withheld.json`), в git не входит.
- `public/data/` — сгенерированные `works.json`, `scenes.json`, `codebook.json`, `meta.json`, `validation-report.json`.
- `public/media/` — только индивидуально проверенные и утверждённые изображения; сборка отклоняет непроверенные/незарегистрированные файлы.
- `src/content/chapters/` — семь глав истории в markdown.
- `src/pages/`, `src/components/`, `src/islands/` — сайт на Astro + точечные Svelte-островки.

Обновление корпуса: заменить `data/source/coding.xlsx`, выполнить `npm run data`, проверить `validation-report.json`, затем `npm run build`.

Перед добавлением фотографий и кадров прочитать `materials/media/README.md` и `materials/design/03-final-design-handoff.md` §10.1. Статус `candidate` или `pending_review` никогда не означает разрешение на публикацию.

Подробности модели данных — в `DATA.md`. Лицензии — в `LICENSE`, `LICENSE-CONTENT.md`, `LICENSE-DATA.md`.
