<script lang="ts">
  import { strings } from '../lib/i18n';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  interface Props {
    scene: Scene;
    work: Work | undefined;
    entries: CodebookEntry[];
    base: string;
  }

  let { scene, work, entries, base }: Props = $props();

  const byCatVal = $derived(
    new Map(entries.map((e) => [`${e.category}.${e.value}`, e])),
  );

  function entry(category: string, value: string | null | undefined) {
    if (!value) return undefined;
    return byCatVal.get(`${category}.${value}`);
  }

  function codeHref(e: CodebookEntry | undefined) {
    return e ? `${base}codebook/#${e.id}` : '#';
  }

  const stigmaClass: Record<string, string> = { high: 'stigma-high', medium: 'stigma-medium', low: 'stigma-low' };

  const unitLabel = $derived(scene.analysis_unit === 'scene' ? 'сцена' : 'произведение целиком');
  const formatLabel = $derived(work?.format === 'tv_series' ? 'сериал' : 'фильм');

  const FIELD_LABELS: Record<string, string> = {
    scene_description: 'Описание сцены',
    space_type: 'Пространство',
    therapist_archetype: 'Архетип',
    ethical_violation: 'Этическое нарушение',
    stigma_level: 'Стигма',
    utterance_type: 'Типы реплик',
    visual_trope: 'Визуальные тропы',
    scene_function: 'Функция сцены',
    general: 'Общее примечание',
  };
  const fieldNotes = $derived(Object.entries(scene.field_notes ?? {}));
</script>

<article class="scene-card">
  <h3>{work?.title ?? scene.work_id}</h3>
  <dl class="scene-fields">
    <div><dt>Произведение</dt><dd>{work?.title ?? scene.work_id}</dd></div>
    <div><dt>Формат</dt><dd>{formatLabel}, {unitLabel}</dd></div>
    <div><dt>Таймкод</dt><dd>{scene.timecode}</dd></div>
    <div class="scene-fields__wide"><dt>Описание</dt><dd>{scene.description}</dd></div>
    <div>
      <dt>Пространство</dt>
      <dd>
        {#if scene.space_type}
          {@const e = entry('space_type', scene.space_type)}
          {#if e}
            <a href={codeHref(e)}>{e.label}</a>
          {:else}
            <span class="ood" title="значение вне словаря">{scene.space_type}</span>
          {/if}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Архетип</dt>
      <dd>
        {#if scene.therapist_archetype.length}
          {#each scene.therapist_archetype as a}
            {@const e = entry('therapist_archetype', a)}
            {#if e}<a href={codeHref(e)}>{e.label}</a>{:else}<span class="ood" title="значение вне словаря">{a}</span>{/if}{' '}
          {/each}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Этическое нарушение</dt>
      <dd>
        {#if scene.ethical_violation}
          {@const e = entry('ethical_violation', scene.ethical_violation)}
          {#if e}<a href={codeHref(e)}>{e.label}</a>{:else}<span class="ood" title="значение вне словаря">{scene.ethical_violation}</span>{/if}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Стигма</dt>
      <dd class={scene.stigma_level ? stigmaClass[scene.stigma_level] : ''}>
        {#if scene.stigma_level}
          {@const e = entry('stigma_level', scene.stigma_level)}
          <span aria-hidden="true">●</span>{' '}
          {#if e}<a href={codeHref(e)}>{e.label}</a>{:else}<span class="ood" title="значение вне словаря">{scene.stigma_level}</span>{/if}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Типы реплик</dt>
      <dd>
        {#if scene.utterance_types.length}
          {#each scene.utterance_types as u}
            {@const e = entry('utterance_type', u)}
            {#if e}<a href={codeHref(e)}>{e.label}</a>{:else}<span class="ood" title="значение вне словаря">{u}</span>{/if}{' '}
          {/each}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Визуальные тропы</dt>
      <dd>
        {#if scene.visual_tropes.length}
          {#each scene.visual_tropes as t}
            {@const e = entry('visual_trope', t)}
            {#if e}<a href={codeHref(e)}>{e.label}</a>{:else}<span class="ood" title="значение вне словаря">{t}</span>{/if}{' '}
          {/each}
        {:else}
          <span class="muted">Нет кода</span>
        {/if}
      </dd>
    </div>
    <div class="scene-fields__wide">
      <dt>Функция сцены</dt>
      <dd>{scene.scene_function.join('; ') || '—'}</dd>
    </div>
    {#if scene.note}
      <div class="scene-fields__wide"><dt>Примечание</dt><dd class="note">{scene.note}</dd></div>
    {/if}
    {#if fieldNotes.length}
      <div class="scene-fields__wide">
        <dt>{strings.scene.fieldNotes}</dt>
        <dd>
          <dl class="field-notes">
            {#each fieldNotes as [field, text]}
              <div class="field-notes__item">
                <dt>{FIELD_LABELS[field] ?? field}</dt>
                <dd>{text}</dd>
              </div>
            {/each}
          </dl>
        </dd>
      </div>
    {/if}
  </dl>
</article>

<style>
  .scene-card h3 { margin-top: 0; }
  .scene-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 0.75rem 1.5rem; margin: 0; }
  .scene-fields__wide { grid-column: 1 / -1; }
  .scene-fields dt { font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.04em; }
  .scene-fields dd { margin: 0.15rem 0 0; }
  .note { white-space: pre-line; font-size: 0.9rem; color: var(--text-dim); }
  .stigma-high { color: var(--stigma-high); }
  .stigma-medium { color: var(--stigma-medium); }
  .stigma-low { color: var(--stigma-low); }
  .stigma-high a, .stigma-medium a, .stigma-low a { color: inherit; }
  .field-notes { margin: 0.25rem 0 0; display: grid; gap: 0.5rem; }
  .field-notes__item dt {
    font-size: 0.75rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .field-notes__item dd { margin: 0.1rem 0 0; font-size: 0.9rem; color: var(--text-dim); }
</style>
