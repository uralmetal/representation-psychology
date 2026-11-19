<script lang="ts">
  import { strings } from '../lib/i18n';
  import { CAT_DEFS, entryOf, labelOf, sceneValues } from '../lib/codeview';
  import type { CatDef } from '../lib/codeview';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  interface Props {
    scene: Scene;
    work: Work | undefined;
    entries: CodebookEntry[];
    base: string;
    /** ключ CAT_DEFS — показывать только эту категорию; без неё — все */
    catKey?: string;
    /** значение, которое нужно выделить внутри категории */
    highlight?: string;
    /** id якоря для прямых ссылок */
    anchorId?: string;
  }
  let { scene, work, entries, base, catKey, highlight, anchorId }: Props = $props();

  const defs: CatDef[] = $derived(
    catKey ? [CAT_DEFS[catKey]] : Object.values(CAT_DEFS),
  );
  const isOverall = $derived(scene.analysis_unit === 'work_overall');
  const unitLabel = $derived(isOverall ? strings.story.unitOverall : strings.story.unitScene);
  const years = $derived(
    work ? (work.year_start === work.year_end ? String(work.year_start) : `${work.year_start}–${work.year_end}`) : '',
  );
  const fieldNotes = $derived(Object.entries(scene.field_notes ?? {}));
  const FIELD_LABELS: Record<string, string> = {
    scene_description: 'Описание',
    space_type: 'Пространство',
    therapist_archetype: 'Архетип',
    ethical_violation: 'Этика',
    stigma_level: 'Стигма',
    utterance_type: 'Типы реплик',
    visual_trope: 'Визуальные тропы',
    scene_function: 'Функция сцены',
    general: 'Общее примечание',
  };
</script>

<article class="evidence" id={anchorId} data-work={scene.work_id}>
  <header class="evidence__head">
    <a class="evidence__title" href="{base}work/{scene.work_id}/">{work?.title ?? scene.work_id}</a>
    <span class="evidence__meta muted small">
      {years}{years ? ' · ' : ''}{unitLabel} · <code>{scene.id}</code>
    </span>
  </header>
  {#if scene.timecode}
    <p class="evidence__time small muted">{scene.timecode}</p>
  {/if}
  <p class="evidence__desc small">{scene.description}</p>

  <dl class="evidence__codes">
    {#each defs as def}
      {@const vals = sceneValues(scene, def)}
      <div class="evidence__code">
        <dt>{def.tab}</dt>
        <dd>
          {#if vals.length}
            {#each vals as v}
              {@const e = entryOf(entries, def.cat, v)}
              {#if e}
                <a class:is-highlight={v === highlight} href={`${base}codebook/#${e.id}`}>{labelOf(entries, def.cat, v)}</a>{' '}
              {:else}
                <span class="evidence__ood" title={strings.catalog.outOfDictionary}>{labelOf(entries, def.cat, v)}</span>{' '}
              {/if}
            {/each}
          {:else}
            <span class="muted">—</span>
          {/if}
        </dd>
      </div>
    {/each}
  </dl>

  {#if scene.note || fieldNotes.length}
    <details class="evidence__notes">
      <summary>{strings.story.fieldNotes}</summary>
      <dl>
        {#if scene.note}<div><dt>Примечание</dt><dd>{scene.note}</dd></div>{/if}
        {#each fieldNotes as [field, text]}
          <div><dt>{FIELD_LABELS[field] ?? field}</dt><dd>{text}</dd></div>
        {/each}
      </dl>
    </details>
  {/if}

  <p class="evidence__links small">
    <a href="{base}scene/{scene.id}/">{strings.story.openRecord} →</a>
  </p>
</article>

<style>
  .evidence {
    background: var(--bg-soft);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    min-width: 0;
  }
  .evidence__head {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem 0.6rem;
    align-items: baseline;
  }
  .evidence__title {
    font-family: var(--serif);
    font-size: 1.05rem;
    color: var(--text);
    text-decoration: none;
  }
  .evidence__title:hover { color: var(--accent); }
  .evidence__time { margin: 0.15rem 0 0; }
  .evidence__desc { margin: 0.4rem 0 0.6rem; color: var(--text); }
  .evidence__codes {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
    gap: 0.3rem 0.8rem;
    margin: 0 0 0.5rem;
    font-size: 0.82rem;
  }
  .evidence__code dt {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
  }
  .evidence__code dd { margin: 0.1rem 0 0; }
  .evidence__codes a.is-highlight {
    font-weight: 700;
    text-decoration: underline;
    text-decoration-thickness: 2px;
    text-underline-offset: 3px;
  }
  .evidence__notes { font-size: 0.82rem; margin-bottom: 0.4rem; }
  .evidence__notes summary { cursor: pointer; color: var(--accent); font-weight: 600; }
  .evidence__notes dl { margin: 0.4rem 0 0; display: grid; gap: 0.35rem; }
  .evidence__notes dt { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-dim); }
  .evidence__notes dd { margin: 0.1rem 0 0; color: var(--text-dim); }
  .evidence__links { margin: 0; }
  .evidence__ood {
    border-bottom: 1px dashed var(--orange);
    cursor: help;
  }
</style>
