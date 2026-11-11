<script lang="ts">
  import { codeLabel, mergeWorkScenes } from '../lib/steps';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  interface Props {
    work: Work;
    scenes: Scene[];
    entries: CodebookEntry[];
    base: string;
  }
  let { work, scenes, entries, base }: Props = $props();

  const m = $derived(mergeWorkScenes(scenes));
  const sceneId = $derived(scenes[0]?.id ?? null);

  function codeHref(category: string, value: string | null | undefined): string {
    if (!value) return '#';
    const { id } = codeLabel(entries, category, value);
    return id ? `${base}codebook/#${id}` : '#';
  }

  function codeText(category: string, value: string | null | undefined): string {
    if (!value) return '';
    return codeLabel(entries, category, value).label;
  }

  function listText(category: string, vals: string[]): string {
    return vals.map((v) => codeLabel(entries, category, v).label).join(', ');
  }

  const years = $derived(
    work.year_start === work.year_end ? String(work.year_start) : `${work.year_start}–${work.year_end}`,
  );
  const formatLabel = $derived(work.format === 'tv_series' ? 'сериал' : 'фильм');
</script>

<article class="work-feature">
  <h3 class="wf-title">{work.title}</h3>
  {#if work.original_title}<p class="muted small wf-original">{work.original_title}</p>{/if}
  <dl class="wf-meta">
    <div><dt>Формат</dt><dd>{formatLabel}</dd></div>
    <div><dt>Годы</dt><dd>{years}</dd></div>
    <div class="wf-wide"><dt>Страны</dt><dd>{work.country.join(', ')}</dd></div>
    <div class="wf-wide"><dt>Жанры</dt><dd>{work.genres.join(', ')}</dd></div>
  </dl>
  <p class="wf-desc">{work.description}</p>

  <dl class="wf-codes">
    <div>
      <dt>Пространство</dt>
      <dd>
        {#if m.space}
          <a href={codeHref('space_type', m.space)}>{codeText('space_type', m.space)}</a>
        {:else}
          <span class="muted">нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Архетип</dt>
      <dd>
        {#each m.archetypes as a}
          <a href={codeHref('therapist_archetype', a)}>{codeText('therapist_archetype', a)}</a>{' '}
        {/each}
      </dd>
    </div>
    <div>
      <dt>Этика</dt>
      <dd>
        {#if m.ethics}
          <a href={codeHref('ethical_violation', m.ethics)}>{codeText('ethical_violation', m.ethics)}</a>
        {:else}
          <span class="muted">—</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Стигма</dt>
      <dd>
        {#if m.stigma}
          <a href={codeHref('stigma_level', m.stigma)}>{codeText('stigma_level', m.stigma)}</a>
        {:else}
          <span class="muted">—</span>
        {/if}
      </dd>
    </div>
    <div class="wf-wide">
      <dt>Типы реплик</dt>
      <dd>{listText('utterance_type', m.utterances) || '—'}</dd>
    </div>
    <div class="wf-wide">
      <dt>Визуальные тропы</dt>
      <dd>{listText('visual_trope', m.tropes) || '—'}</dd>
    </div>
  </dl>

  {#if m.notes.length}
    <p class="wf-note muted small">Примечание: {m.notes.join(' ')}</p>
  {/if}

  <p class="wf-links small">
    <a href="{base}work/{work.id}/">Страница произведения →</a>
    {#if sceneId} · <a href="{base}scene/{sceneId}/">Единица анализа →</a>{/if}
  </p>
</article>

<style>
  .work-feature { padding: 0.25rem 0.25rem 0.5rem; }
  .wf-title { margin: 0 0 0.15rem; font-size: 1.25rem; }
  .wf-original { margin: 0 0 0.6rem; }
  .wf-meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.4rem 1rem;
    margin: 0 0 0.8rem;
    font-size: 0.85rem;
  }
  .wf-meta dt {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .wf-meta dd { margin: 0.1rem 0 0; }
  .wf-wide { grid-column: 1 / -1; }
  .wf-desc { font-size: 0.92rem; color: var(--text-dim); margin: 0 0 0.9rem; }
  .wf-codes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem 1rem;
    margin: 0 0 0.8rem;
    font-size: 0.85rem;
  }
  .wf-codes dt {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .wf-codes dd { margin: 0.15rem 0 0; }
  .wf-note { margin: 0 0 0.6rem; }
  .wf-links { margin: 0; }
</style>
