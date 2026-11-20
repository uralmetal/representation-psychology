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
  const frames = $derived(work.frames ?? []);
  const fieldNotes = $derived.by(() => {
    const out: Record<string, string> = {};
    for (const s of scenes) {
      for (const [k, v] of Object.entries(s.field_notes ?? {})) {
        out[k] = out[k] ? `${out[k]} ${v}` : v;
      }
    }
    return Object.entries(out);
  });
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

<article class="work-feature">
  {#if work.original_title}<p class="muted small wf-original">{work.original_title}</p>{/if}
  <dl class="wf-meta">
    <div><dt>Формат</dt><dd>{formatLabel}</dd></div>
    <div><dt>Годы</dt><dd>{years}</dd></div>
    <div class="wf-wide"><dt>Страны</dt><dd>{work.country.join(', ')}</dd></div>
    <div class="wf-wide"><dt>Жанры</dt><dd>{work.genres.join(', ')}</dd></div>
  </dl>
  <p class="wf-desc">{work.description}</p>

  {#if frames.length}
    <div class="wf-frames">
      {#each frames.slice(0, 3) as f}
        <a class="img-zoom" href="{base}{f}" data-lightbox aria-label="Открыть кадр на весь экран">
          <img src="{base}{f}" alt="Кадр из «{work.title}»" loading="lazy" />
        </a>
      {/each}
    </div>
  {/if}

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

  {#if fieldNotes.length}
    <div class="wf-fieldnotes">
      <h4 class="wf-fieldnotes__title">Пояснения кодирования</h4>
      <dl>
        {#each fieldNotes as [field, text]}
          <div>
            <dt>{FIELD_LABELS[field] ?? field}</dt>
            <dd>{text}</dd>
          </div>
        {/each}
      </dl>
    </div>
  {/if}

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
  .wf-frames {
    display: flex;
    gap: 0.4rem;
    margin: 0 0 0.9rem;
    overflow-x: auto;
  }
  .wf-frames .img-zoom { flex: 0 0 auto; display: block; }
  .wf-frames img {
    height: 84px;
    width: auto;
    border-radius: 6px;
    border: 1px solid var(--border);
    object-fit: cover;
    flex: 0 0 auto;
  }
  .wf-fieldnotes { margin: 0 0 0.8rem; font-size: 0.82rem; }
  .wf-fieldnotes__title {
    margin: 0 0 0.35rem;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
  }
  .wf-fieldnotes dl { margin: 0; display: grid; gap: 0.4rem; }
  .wf-fieldnotes dt { color: var(--accent); font-size: 0.75rem; }
  .wf-fieldnotes dd { margin: 0.1rem 0 0; color: var(--text-dim); }
</style>
