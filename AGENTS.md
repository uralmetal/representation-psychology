# AGENTS.md

Статический сайт «Репрезентация психологии в кино» (Astro 5 + Svelte 5 островки, GitHub Pages project site).

## Команды

- `npm run data` — ETL: `data/source/coding.xlsx` → `public/data/*.json` + `validation-report.json` (Python через `.venv/bin/python`, пакеты из `requirements.txt`).
- `npm run validate:media` — проверяет реестр фотографий/кадров и не допускает публикацию неподтверждённых или незарегистрированных файлов.
- `npm run test:media` — проверяет медиавалидатор регрессионными тестами.
- `npm run build` — проверка медиареестра + ETL + `astro build` → `dist/`. Падает при ошибках валидаторов.
- `npm run dev` — dev-сервер на `http://localhost:4321/representation-psychology/`.

## Важно

- В `.astro`-файлах **нельзя использовать синтаксис блоков** `{#if}`/`{:else}`/`{/if}`/`{#each}`/`{/each}` — компилятор Astro генерирует невалидный JS (`${#if ...}` внутри template literal; известный баг withastro/astro#16502), и esbuild падает с `Expected "in" but found ...`. Использовать JS-выражения: `{cond && (...)}`, `{items.map(...)}`.
- Node в WSL — v26; astro 7.4.10 + @astrojs/svelte 9.1.4 + svelte 5.57.
- `base` в `astro.config.mjs` = `/representation-psychology`, `site` = `https://uralmetal.github.io` — поменять, если владелец репозитория другой.
- Имена кодеров не должны попадать в публичные файлы: столбец «Категория анализа» удалён из `data/source/coding.xlsx` и из таблиц в `materials/`; валидатор проверяет это автоматически.
- Токены кодирования вне `codebook.yml` не становятся кодами — уходят в `note` (см. `materials/Plan.md`).
- Исходная история проекта — `materials/Репрезентация психологии в кино.md`; главы в `src/content/chapters/` — её адаптация (карточки произведений живут в `data/source/works.yml` и на страницах `/work/`).
- **Изображения:** единственный реестр — `data/media-assets.yml`; инструкции и очередь — `materials/media/`. Кандидаты хранятся в `materials/` и не публикуются. Только записи со статусом `approved`, полной атрибуцией и индивидуальной фиксацией правовой проверки могут иметь файл в `public/media/`. Не обходить `scripts/validate_media.py` и не переносить кадры из материалов в `public/` автоматически. См. handoff §10.1.
