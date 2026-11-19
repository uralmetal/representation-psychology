<script lang="ts">
  import EvidenceCard from '../components/EvidenceCard.svelte';
  import { strings } from '../lib/i18n';
  import {
    CAT_DEFS,
    entriesOfCategory,
    entryOf,
    sceneValues,
  } from '../lib/codeview';
  import type { CatDef } from '../lib/codeview';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  interface Props {
    /** ключи CAT_DEFS: один — обычный выбор, два — переключаемые слои */
    catKeys: string[];
    scenes: Scene[];
    works: Work[];
    entries: CodebookEntry[];
    base: string;
    /** постоянная методологическая оговорка под интерактивом */
    note?: string;
  }
  let { catKeys, scenes, works, entries, base, note }: Props = $props();

  const pairs = $derived(
    catKeys
      .map((k) => ({ key: k, def: CAT_DEFS[k] }))
      .filter((p): p is { key: string; def: NonNullable<(typeof CAT_DEFS)[string]> } => Boolean(p.def)),
  );
  const workById = $derived(new Map(works.map((w) => [w.id, w])));

  // catKeys уникальны для каждого экземпляра на странице — детерминированный
  // id, совпадающий между SSR и гидратацией.
  const uid = catKeys.join('-');
  let activeTab = $state(0);
  let selected = $state<Record<string, string>>({});

  function evidenceFor(catKey: string, value: string): Scene[] {
    const def = CAT_DEFS[catKey];
    return scenes.filter((s) => sceneValues(s, def).includes(value));
  }

  function isSelected(catKey: string, value: string): boolean {
    return selected[catKey] === value;
  }

  function pick(catKey: string, value: string) {
    selected = { ...selected, [catKey]: value };
  }

  const multi = $derived(pairs.length > 1);

  function selectTab(i: number) {
    activeTab = i;
    document.getElementById(`${uid}-tab-${i}`)?.focus();
  }

  function onTabKey(e: KeyboardEvent, i: number) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const n = pairs.length;
    const next =
      e.key === 'ArrowRight' ? (i + 1) % n
      : e.key === 'ArrowLeft' ? (i - 1 + n) % n
      : e.key === 'Home' ? 0
      : n - 1;
    selectTab(next);
  }

  function statusText(catKey: string, def: CatDef): string {
    const v = selected[catKey];
    if (!v) return '';
    const e = entryOf(entries, def.cat, v);
    const ev = evidenceFor(catKey, v);
    const nScene = ev.filter((s) => s.analysis_unit === 'scene').length;
    const nOverall = ev.filter((s) => s.analysis_unit === 'work_overall').length;
    return `${e?.label ?? v}. Сцены: ${nScene}, произведения целиком: ${nOverall}.`;
  }

  function detailEntry(catKey: string): CodebookEntry | undefined {
    const v = selected[catKey];
    return v ? entryOf(entries, CAT_DEFS[catKey].cat, v) : undefined;
  }
</script>

<div class="explorer" role="group" aria-label={strings.story.interactiveLabel}>
  {#if multi}
    <div class="explorer__tabs" role="tablist" aria-label={strings.story.interactiveLabel}>
      {#each pairs as p, i}
        <button
          type="button"
          role="tab"
          id={`${uid}-tab-${i}`}
          aria-selected={i === activeTab}
          aria-controls={`${uid}-panel-${i}`}
          tabindex={i === activeTab ? 0 : -1}
          class:is-active={i === activeTab}
          onclick={() => selectTab(i)}
          onkeydown={(e) => onTabKey(e, i)}
        >{p.def.tab}</button>
      {/each}
    </div>
  {/if}

  {#each pairs as p, di}
    {@const catKey = p.key}
    {@const def = p.def}
    {@const visible = di === activeTab}
    <div
      class="explorer__pane"
      class:hidden={!visible}
      role={multi ? 'tabpanel' : 'group'}
      aria-label={multi ? undefined : def.tab}
      id={multi ? `${uid}-panel-${di}` : undefined}
      aria-labelledby={multi ? `${uid}-tab-${di}` : undefined}
    >
      <div class="explorer__options" role="group" aria-label={def.tab}>
        {#each entriesOfCategory(entries, def.cat) as e}
          <button
            type="button"
            class="explorer__option"
            class:is-selected={isSelected(catKey, e.value)}
            aria-pressed={isSelected(catKey, e.value)}
            onclick={() => pick(catKey, e.value)}
          >{e.label}</button>
        {/each}
      </div>

      {#if selected[catKey]}
        {@const e = detailEntry(catKey)}
        {@const evScenes = evidenceFor(catKey, selected[catKey])}
        {@const evSceneUnits = evScenes.filter((s) => s.analysis_unit === 'scene')}
        {@const evOverallUnits = evScenes.filter((s) => s.analysis_unit === 'work_overall')}
        <p class="sr-only" role="status">{statusText(catKey, def)}</p>
        <div class="explorer__detail">
          {#if e}
            <p class="explorer__def"><strong>{e.label}.</strong> {e.definition}</p>
            {#if e.example}<p class="explorer__example muted small">Пример из словаря: {e.example}</p>{/if}
          {/if}
          {#if evScenes.length}
            {#each [
              { label: 'Сцены', list: evSceneUnits },
              { label: 'Произведения целиком', list: evOverallUnits },
            ] as grp}
              <p class="explorer__ev-label">{grp.label} · {grp.list.length}</p>
              {#if grp.list.length}
                <div class="explorer__evidence">
                  {#each grp.list as s}
                    <EvidenceCard
                      scene={s}
                      work={workById.get(s.work_id)}
                      {entries}
                      {base}
                      catKey={catKey}
                      highlight={selected[catKey]}
                    />
                  {/each}
                </div>
              {:else}
                <p class="explorer__empty muted small">Нет записей этого типа единиц.</p>
              {/if}
            {/each}
          {:else}
            <p class="explorer__empty muted small">{strings.story.noExamples}</p>
          {/if}
        </div>
      {:else}
        <p class="explorer__prompt muted small">{strings.story.pickPrompt}</p>
      {/if}
    </div>
  {/each}

  {#if note}<p class="explorer__note muted small">{note}</p>{/if}
</div>

<style>
  .explorer {
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 1.25rem 0;
  }
  .explorer__tabs {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.9rem;
    flex-wrap: wrap;
  }
  .explorer__tabs button {
    border: 1px solid var(--border);
    background: var(--bg-soft);
    color: var(--text-dim);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .explorer__tabs button.is-active,
  .explorer__tabs button[aria-selected='true'] {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--accent-ink);
  }
  .explorer__options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }
  .explorer__option {
    border: 1px solid var(--border);
    background: var(--bg-soft);
    color: var(--text);
    border-radius: 8px;
    padding: 0.5rem 0.85rem;
    font-size: 0.88rem;
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s ease, background 0.15s ease;
  }
  .explorer__option:hover { border-color: var(--accent); }
  .explorer__option.is-selected {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--accent-ink);
  }
  .explorer__prompt { margin: 0.8rem 0 0; }
  .explorer__detail {
    margin-top: 1rem;
    border-left: 3px solid var(--orange);
    padding: 0.2rem 0 0.2rem 0.9rem;
  }
  .explorer__def { margin: 0 0 0.4rem; font-size: 0.92rem; }
  .explorer__example { margin: 0 0 0.8rem; }
  .explorer__ev-label { margin: 0.7rem 0 0.4rem; font-size: 0.85rem; font-weight: 600; color: var(--text-dim); }
  .explorer__evidence {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr));
    gap: 0.6rem;
  }
  .explorer__empty { margin: 0.6rem 0 0; }
  .explorer__note {
    margin: 0.9rem 0 0;
    padding-top: 0.6rem;
    border-top: 1px dashed var(--border);
  }
  .hidden { display: none; }
</style>
