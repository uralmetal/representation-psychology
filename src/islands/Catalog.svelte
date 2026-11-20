<script lang="ts">
  import { onMount } from 'svelte';
  import { strings } from '../lib/i18n';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  function param(name: string): string | null {
    if (typeof window === 'undefined') return null;
    return new URLSearchParams(window.location.search).get(name);
  }
  function numParam(name: string): number | null {
    const v = param(name);
    if (v == null || v === '') return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  interface Props {
    works: Work[];
    scenes: Scene[];
    entries: CodebookEntry[];
    base: string;
  }
  let { works, scenes, entries, base }: Props = $props();

  interface CatCfg {
    key: string;
    sceneField: 'space_type' | 'therapist_archetype' | 'ethical_violation' | 'stigma_level' | 'utterance_types' | 'visual_tropes';
    cat: string;
  }
  const CATS: CatCfg[] = [
    { key: 'space_type', sceneField: 'space_type', cat: 'space_type' },
    { key: 'therapist_archetype', sceneField: 'therapist_archetype', cat: 'therapist_archetype' },
    { key: 'ethical_violation', sceneField: 'ethical_violation', cat: 'ethical_violation' },
    { key: 'stigma_level', sceneField: 'stigma_level', cat: 'stigma_level' },
    { key: 'utterance_types', sceneField: 'utterance_types', cat: 'utterance_type' },
    { key: 'visual_tropes', sceneField: 'visual_tropes', cat: 'visual_trope' },
  ];

  const FIELD_LABELS: Record<string, string> = {
    scene_description: 'Описание сцены',
    space_type: 'Пространство',
    therapist_archetype: 'Архетип',
    ethical_violation: 'Этика',
    stigma_level: 'Стигма',
    utterance_type: 'Типы реплик',
    visual_trope: 'Визуальные тропы',
    scene_function: 'Функция сцены',
    general: 'Общее примечание',
  };

  const workById = $derived(new Map(works.map((w) => [w.id, w])));
  const entryByCatVal = $derived(new Map(entries.map((e) => [`${e.category}.${e.value}`, e])));
  const catLabel = $derived.by(() => {
    const m = new Map<string, string>();
    for (const e of entries) if (!m.has(e.category)) m.set(e.category, e.category_label);
    return m;
  });

  interface Row {
    scene: Scene;
    work: Work | undefined;
  }
  const rows: Row[] = $derived(scenes.map((scene) => ({ scene, work: workById.get(scene.work_id) })));

  function entryOf(cat: string, value: string): CodebookEntry | undefined {
    return entryByCatVal.get(`${cat}.${value}`);
  }
  function labelOf(cat: string, value: string): string {
    return entryOf(cat, value)?.label ?? value;
  }
  function valuesOf(row: Row, cfg: CatCfg): string[] {
    const v = row.scene[cfg.sceneField] as string | string[] | null;
    if (Array.isArray(v)) return v;
    return v ? [v] : [];
  }

  // Начальное состояние — дефолтное, чтобы SSR и гидратация совпадали;
  // параметры URL применяются в onMount.
  let q = $state('');
  let format = $state('all');
  let unit = $state('all');
  let sort = $state('year');
  let yearFrom = $state<number | null>(null);
  let yearTo = $state<number | null>(null);
  let filters = $state<Record<string, string>>(
    Object.fromEntries(CATS.map((c) => [c.key, ''])),
  );

  // paramsApplied защищает от гонки: эффект записи URL не должен сработать
  // (и стереть query) раньше, чем onMount прочитает параметры.
  let paramsApplied = $state(false);
  onMount(() => {
    const p = new URLSearchParams(window.location.search);
    q = p.get('q') ?? '';
    format = p.get('format') ?? 'all';
    unit = p.get('unit') ?? 'all';
    sort = p.get('sort') ?? 'year';
    yearFrom = numParam('year_from');
    yearTo = numParam('year_to');
    filters = {
      ...filters,
      ...Object.fromEntries(CATS.map((c) => [c.key, p.get(c.key) ?? ''])),
    };
    paramsApplied = true;
  });

  $effect(() => {
    if (typeof window === 'undefined' || !paramsApplied) return;
    const p = new URLSearchParams();
    if (q.trim()) p.set('q', q.trim());
    if (format !== 'all') p.set('format', format);
    if (unit !== 'all') p.set('unit', unit);
    if (sort !== 'year') p.set('sort', sort);
    if (Number.isFinite(yearFrom)) p.set('year_from', String(yearFrom));
    if (Number.isFinite(yearTo)) p.set('year_to', String(yearTo));
    for (const cfg of CATS) {
      if (filters[cfg.key]) p.set(cfg.key, filters[cfg.key]);
    }
    const qs = p.toString();
    history.replaceState(null, '', `${window.location.pathname}${qs ? `?${qs}` : ''}`);
  });

  const filtered = $derived(
    rows
      .filter((row) => {
        const w = row.work;
        if (format !== 'all' && w?.format !== format) return false;
        if (unit !== 'all' && row.scene.analysis_unit !== unit) return false;
        const from = Number.isFinite(yearFrom) ? (yearFrom as number) : null;
        const to = Number.isFinite(yearTo) ? (yearTo as number) : null;
        if (from != null && (w?.year_start ?? 0) < from) return false;
        if (to != null && (w?.year_end ?? 9999) > to) return false;
        const needle = q.trim().toLowerCase();
        if (needle) {
          const hay = [
            w?.title, w?.original_title, w?.country.join(' '), w?.genres.join(' '),
            row.scene.timecode, row.scene.description, row.scene.scene_function.join(' '),
          ].join(' ').toLowerCase();
          if (!hay.includes(needle)) return false;
        }
        for (const cfg of CATS) {
          const sel = filters[cfg.key];
          if (!sel) continue;
          const vals = valuesOf(row, cfg);
          if (sel === '__none__' ? vals.length > 0 : !vals.includes(sel)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sort === 'title') {
          return (a.work?.title ?? a.scene.work_id).localeCompare(
            b.work?.title ?? b.scene.work_id,
            'ru',
          );
        }
        return (a.work?.year_start ?? 0) - (b.work?.year_start ?? 0)
          || (a.work?.title ?? '').localeCompare(b.work?.title ?? '', 'ru');
      }),
  );

  let compareIds = $state<string[]>([]);
  function toggleCompare(id: string) {
    compareIds = compareIds.includes(id)
      ? compareIds.filter((x) => x !== id)
      : [...compareIds, id];
  }
  const compareRows = $derived(rows.filter((r) => compareIds.includes(r.scene.id)));
  const compareMixed = $derived(
    new Set(compareRows.map((r) => r.scene.analysis_unit)).size > 1,
  );

  function compareKey(row: Row, cat: string): string {
    const cfg = CATS.find((c) => c.cat === cat)!;
    return valuesOf(row, cfg).map((v) => labelOf(cfg.cat, v)).sort().join(' | ') || '—';
  }
  function compareSame(cat: string): boolean {
    if (compareRows.length < 2) return false;
    const first = compareKey(compareRows[0], cat);
    return compareRows.every((r) => compareKey(r, cat) === first);
  }

  function rememberReturn() {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem('rp:return-url', window.location.href);
    } catch {
      /* sessionStorage недоступен */
    }
  }

  function years(w: Work | undefined): string {
    if (!w) return '—';
    return w.year_start === w.year_end ? String(w.year_start) : `${w.year_start}–${w.year_end}`;
  }

  function trunc(text: string, n = 110): string {
    return text.length > n ? `${text.slice(0, n).trimEnd()}…` : text;
  }

  function csvEscape(v: string): string {
    return `"${v.replace(/"/g, '""')}"`;
  }

  function exportCsv() {
    const header = [
      'Произведение', 'Год', 'Страна', 'Формат', 'Единица анализа', 'Таймкод', 'scene_id',
      'Описание', 'Пространство', 'Архетип терапевта', 'Этическое нарушение', 'Уровень стигмы',
      'Типы реплик', 'Визуальные тропы', 'Функция сцены', 'Неизвестные токены', 'Пояснения кодирования',
    ];
    const lines = filtered.map((row) => {
      const s = row.scene;
      const w = row.work;
      const cell = (cfg: CatCfg) => valuesOf(row, cfg).map((v) => labelOf(cfg.cat, v)).join('; ');
      const notes = Object.entries(s.field_notes ?? {})
        .map(([f, t]) => `${FIELD_LABELS[f] ?? f}: ${t}`)
        .join(' | ');
      return [
        w?.title ?? s.work_id, years(w), w?.country.join(', ') ?? '',
        w?.format === 'tv_series' ? 'сериал' : 'фильм',
        s.analysis_unit === 'scene' ? 'сцена' : 'произведение целиком',
        s.timecode, s.id, s.description,
        cell(CATS[0]), cell(CATS[1]), cell(CATS[2]), cell(CATS[3]), cell(CATS[4]), cell(CATS[5]),
        s.scene_function.join('; '), s.note, notes,
      ].map(csvEscape).join(';');
    });
    const csv = '\uFEFF' + [header.map(csvEscape).join(';'), ...lines].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'catalog.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="catalog">
  <div class="catalog__filters">
    <input
      class="catalog__search"
      type="search"
      bind:value={q}
      placeholder={strings.catalog.search}
      aria-label={strings.catalog.search}
    />
    <label class="catalog__field">
      <span>Формат</span>
      <select bind:value={format}>
        <option value="all">{strings.catalog.formatAll}</option>
        <option value="movie">{strings.catalog.formatMovie}</option>
        <option value="tv_series">{strings.catalog.formatSeries}</option>
      </select>
    </label>
    <label class="catalog__field">
      <span>{strings.catalog.yearFrom}</span>
      <input type="number" min="1900" max="2100" bind:value={yearFrom} />
    </label>
    <label class="catalog__field">
      <span>{strings.catalog.yearTo}</span>
      <input type="number" min="1900" max="2100" bind:value={yearTo} />
    </label>
    <label class="catalog__field">
      <span>{strings.catalog.unit}</span>
      <select bind:value={unit}>
        <option value="all">{strings.catalog.unitAll}</option>
        <option value="scene">{strings.catalog.unitScene}</option>
        <option value="work_overall">{strings.catalog.unitOverall}</option>
      </select>
    </label>
    <label class="catalog__field">
      <span>Сортировка</span>
      <select bind:value={sort}>
        <option value="year">{strings.catalog.sortYear}</option>
        <option value="title">{strings.catalog.sortTitle}</option>
      </select>
    </label>
    {#each CATS as cfg}
      <label class="catalog__field">
        <span>{catLabel.get(cfg.cat) ?? cfg.cat}</span>
        <select bind:value={filters[cfg.key]}>
          <option value="">{strings.catalog.any}</option>
          <option value="__none__">{strings.catalog.noCode}</option>
          {#each entries.filter((e) => e.category === cfg.cat) as e}
            <option value={e.value}>{e.label}</option>
          {/each}
        </select>
      </label>
    {/each}
  </div>

  <p class="catalog__meta muted small">
    {strings.catalog.shown}: {filtered.length} {strings.catalog.of} {rows.length}
    {#if compareIds.length}
      · {strings.catalog.comparing}: {compareIds.length}
    {/if}
    <button type="button" class="btn btn--ghost btn--sm" onclick={exportCsv}>
      {strings.catalog.exportCsv}
    </button>
  </p>

  {#if compareIds.length >= 2}
    <div class="catalog__compare">
      <h3>{strings.catalog.compareTitle}</h3>
      {#if compareMixed}
        <p class="catalog__mixed" role="alert">{strings.catalog.compareMixed}</p>
        <p><button type="button" class="btn btn--ghost btn--sm" onclick={() => (compareIds = [])}>{strings.catalog.clearCompare}</button></p>
      {:else}
      <p class="muted small">{strings.catalog.compareHint}</p>
      <div class="catalog-table-wrap">
        <table class="catalog-table catalog-table--compare">
          <thead>
            <tr>
              <th scope="col"><span class="sr-only">{strings.catalog.compare}</span></th>
              {#each compareRows as row}
                <th>{row.work?.title ?? row.scene.work_id}</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each CATS as cfg}
              <tr class={compareSame(cfg.cat) ? 'is-same' : ''}>
                <th scope="row">{catLabel.get(cfg.cat) ?? cfg.cat}</th>
                {#each compareRows as row}
                  {@const vals = valuesOf(row, cfg)}
                  <td>
                    {#if vals.length}
                      {vals.map((v) => labelOf(cfg.cat, v)).join(' · ')}
                    {:else}
                      <span class="muted">—</span>
                    {/if}
                  </td>
                {/each}
              </tr>
            {/each}
            <tr>
              <th scope="row">Единица</th>
              {#each compareRows as row}
                <td>{row.scene.analysis_unit === 'scene' ? strings.catalog.unitScene : strings.catalog.unitOverall}</td>
              {/each}
            </tr>
            <tr>
              <th scope="row">{strings.catalog.timecode}</th>
              {#each compareRows as row}
                <td><a href="{base}scene/{row.scene.id}/" onclick={rememberReturn}>{row.scene.timecode}</a></td>
              {/each}
            </tr>
            <tr>
              <th scope="row">{strings.catalog.description}</th>
              {#each compareRows as row}
                <td class="small">{trunc(row.scene.description, 160)}</td>
              {/each}
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        <button type="button" class="btn btn--ghost btn--sm" onclick={() => (compareIds = [])}>
          {strings.catalog.clearCompare}
        </button>
      </p>
      {/if}
    </div>
  {/if}

  {#if filtered.length === 0}
    <p class="muted">{strings.catalog.empty}</p>
  {:else}
    <div class="catalog-table-wrap">
      <table class="catalog-table">
        <thead>
          <tr>
            <th scope="col"><span class="sr-only">{strings.catalog.compare}</span></th>
            <th scope="col">{strings.catalog.work}</th>
            <th scope="col">Формат</th>
            <th scope="col">{strings.catalog.unit}</th>
            <th scope="col">{strings.catalog.timecode}</th>
            <th scope="col">{strings.catalog.description}</th>
            {#each CATS as cfg}
              <th scope="col">{catLabel.get(cfg.cat) ?? cfg.cat}</th>
            {/each}
            <th scope="col">{strings.catalog.notes}</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as row (row.scene.id)}
            <tr class:is-selected={compareIds.includes(row.scene.id)}>
              <td>
                <input
                  type="checkbox"
                  checked={compareIds.includes(row.scene.id)}
                  onchange={() => toggleCompare(row.scene.id)}
                  aria-label="{strings.catalog.compare}: {row.work?.title ?? row.scene.id}"
                />
              </td>
              <td>
                <a href="{base}work/{row.scene.work_id}/" onclick={rememberReturn}>{row.work?.title ?? row.scene.work_id}</a>
                <div class="muted small">{years(row.work)} · {row.work?.country.join(', ')}</div>
              </td>
              <td class="small">{row.work?.format === 'tv_series' ? 'сериал' : 'фильм'}</td>
              <td class="small">
                {row.scene.analysis_unit === 'scene' ? strings.catalog.unitScene : strings.catalog.unitOverall}
              </td>
              <td class="small"><a href="{base}scene/{row.scene.id}/" onclick={rememberReturn}>{row.scene.timecode}</a></td>
              <td class="small catalog__desc" title={row.scene.description}>
                {trunc(row.scene.description)}
                {#if row.scene.scene_function.length}
                  <div class="muted catalog__fn">{trunc(row.scene.scene_function.join('; '), 80)}</div>
                {/if}
              </td>
              {#each CATS as cfg}
                {@const vals = valuesOf(row, cfg)}
                <td class="small">
                  {#if vals.length}
                    {#each vals as v, i}
                      {#if i > 0}, {/if}
                      {@const e = entryOf(cfg.cat, v)}
                      {#if e}
                        <a href="{base}codebook/#{e.id}">{e.label}</a>
                      {:else}
                        <span class="catalog__ood" title={strings.catalog.outOfDictionary}>{v}</span>
                      {/if}
                    {/each}
                  {:else}
                    <span class="muted">{strings.catalog.noCode}</span>
                  {/if}
                </td>
              {/each}
              <td class="small">
                {#if row.scene.note || Object.keys(row.scene.field_notes ?? {}).length}
                  <span title={Object.entries(row.scene.field_notes ?? {}).map(([f, t]) => `${FIELD_LABELS[f] ?? f}: ${t}`).join('\n') || row.scene.note}>✎</span>
                {:else}
                  <span class="muted">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="catalog-cards" aria-label="Результаты каталога">
      {#each filtered as row (row.scene.id)}
        <article class="catalog-card">
          <div class="catalog-card__top">
            <label class="catalog-card__compare">
              <input
                type="checkbox"
                checked={compareIds.includes(row.scene.id)}
                onchange={() => toggleCompare(row.scene.id)}
                aria-label="{strings.catalog.compare}: {row.work?.title ?? row.scene.id}"
              />
              <span>{strings.catalog.compare}</span>
            </label>
            <span class="catalog-card__unit">
              {row.scene.analysis_unit === 'scene' ? strings.catalog.unitScene : strings.catalog.unitOverall}
            </span>
          </div>
          <h3><a href="{base}work/{row.scene.work_id}/" onclick={rememberReturn}>{row.work?.title ?? row.scene.work_id}</a></h3>
          <p class="muted small">{years(row.work)} · {row.work?.country.join(', ')}</p>
          <p class="catalog-card__description">{row.scene.description}</p>
          <p class="small"><strong>{strings.catalog.timecode}:</strong> <a href="{base}scene/{row.scene.id}/" onclick={rememberReturn}>{row.scene.timecode || '—'}</a></p>
          <dl class="catalog-card__fields">
            {#each CATS as cfg}
              {@const vals = valuesOf(row, cfg)}
              <div>
                <dt>{catLabel.get(cfg.cat) ?? cfg.cat}</dt>
                <dd>
                  {#if vals.length}
                    {#each vals as v, i}
                      {#if i > 0}<span>, </span>{/if}
                      {@const e = entryOf(cfg.cat, v)}
                      {#if e}
                        <a href="{base}codebook/#{e.id}">{e.label}</a>
                      {:else}
                        <span class="catalog__ood" title={strings.catalog.outOfDictionary}>{v}</span>
                      {/if}
                    {/each}
                  {:else}
                    <span class="muted">{strings.catalog.noCode}</span>
                  {/if}
                </dd>
              </div>
            {/each}
          </dl>
          {#if row.scene.note || Object.keys(row.scene.field_notes ?? {}).length}
            <details class="catalog-card__notes">
              <summary>{strings.catalog.notes}</summary>
              {#if row.scene.note}<p>{row.scene.note}</p>{/if}
              {#each Object.entries(row.scene.field_notes ?? {}) as [field, note]}
                <p><strong>{FIELD_LABELS[field] ?? field}:</strong> {note}</p>
              {/each}
            </details>
          {/if}
        </article>
      {/each}
    </div>
  {/if}
</div>

<style>
  .catalog__filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 0.9rem;
    align-items: end;
    margin-bottom: 0.9rem;
  }
  .catalog__search {
    flex: 1 1 14rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 0.45rem 0.7rem;
    font: inherit;
  }
  .catalog__field { display: flex; flex-direction: column; gap: 0.2rem; }
  .catalog__field span {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .catalog__field select,
  .catalog__field input {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 0.4rem 0.55rem;
    font: inherit;
    max-width: 13rem;
  }
  .catalog__meta { display: flex; align-items: center; gap: 0.6rem; margin: 0 0 1rem; }
  .catalog__compare {
    margin: 0 0 1.5rem;
    padding: 1rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .catalog__compare h3 { margin-top: 0; }
  .catalog__mixed {
    padding: 0.6rem 0.8rem;
    border-left: 3px solid var(--orange);
    background: var(--orange-soft);
    border-radius: 4px;
    font-size: 0.9rem;
  }
  .catalog__ood {
    border-bottom: 1px dashed var(--orange);
    cursor: help;
  }
  .catalog-table-wrap { overflow-x: auto; }
  .catalog-cards { display: none; }
  .catalog-card {
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-card);
    min-width: 0;
  }
  .catalog-card h3 { margin: 0.45rem 0 0.15rem; font-size: 1.05rem; }
  .catalog-card p { margin: 0.35rem 0; }
  .catalog-card__top { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; }
  .catalog-card__compare { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; }
  .catalog-card__unit {
    display: inline-block;
    padding: 0.2rem 0.45rem;
    border-radius: 4px;
    background: var(--accent-soft);
    font-size: 0.75rem;
  }
  .catalog-card__description { line-height: 1.45; }
  .catalog-card__fields { margin: 0.75rem 0 0; display: grid; gap: 0.55rem; }
  .catalog-card__fields > div { display: grid; grid-template-columns: minmax(6.5rem, 0.8fr) minmax(0, 1.5fr); gap: 0.5rem; }
  .catalog-card__fields dt { color: var(--text-dim); font-size: 0.78rem; }
  .catalog-card__fields dd { margin: 0; overflow-wrap: anywhere; font-size: 0.85rem; }
  .catalog-card__notes { margin-top: 0.75rem; font-size: 0.82rem; }
  .catalog-card__notes summary { cursor: pointer; font-weight: 600; }
  .catalog-card__notes p { overflow-wrap: anywhere; }
  .catalog-table { min-width: 60rem; }
  .catalog-table--compare { min-width: 0; width: 100%; }
  .catalog-table--compare tr.is-same td,
  .catalog-table--compare tr.is-same th { background: var(--accent-soft); }
  tr.is-selected td { background: var(--accent-soft); }
  .catalog__desc { max-width: 16rem; }
  .catalog__fn { margin-top: 0.2rem; font-size: 0.78rem; }
  @media (max-width: 760px) {
    .catalog-table-wrap:not(.catalog-table--compare-wrap) { display: none; }
    .catalog-cards { display: grid; gap: 0.75rem; }
    .catalog__filters { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: end; }
    .catalog__search { grid-column: 1 / -1; width: 100%; min-width: 0; box-sizing: border-box; }
    .catalog__field { min-width: 0; }
    .catalog__field select, .catalog__field input { max-width: none; width: 100%; min-width: 0; box-sizing: border-box; }
    .catalog__meta { flex-wrap: wrap; }
    .catalog__compare { overflow-x: auto; }
  }
  .sr-only {
    position: absolute;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }
</style>
