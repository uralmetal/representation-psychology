<script lang="ts">
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

  const ethicsLabel: Record<string, string> = { yes: 'Да', partial: 'Частично', no: 'Нет' };
  const stigmaLabel: Record<string, string> = { high: 'Высокий', medium: 'Средний', low: 'Низкий' };
  const stigmaClass: Record<string, string> = { high: 'stigma-high', medium: 'stigma-medium', low: 'stigma-low' };

  const unitLabel = $derived(scene.analysis_unit === 'scene' ? 'сцена' : 'произведение целиком');
  const formatLabel = $derived(work?.format === 'tv_series' ? 'сериал' : 'фильм');
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
          <a href={codeHref(e)}>{e?.label ?? scene.space_type}</a>
        {:else}
          <span class="muted">в словаре нет</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Архетип</dt>
      <dd>
        {#each scene.therapist_archetype as a}
          {@const e = entry('therapist_archetype', a)}
          <a href={codeHref(e)}>{e?.label ?? a}</a>{' '}
        {/each}
      </dd>
    </div>
    <div>
      <dt>Этическое нарушение</dt>
      <dd>
        {#if scene.ethical_violation}
          {@const e = entry('ethical_violation', scene.ethical_violation)}
          <a href={codeHref(e)}>{e?.label ?? ethicsLabel[scene.ethical_violation]}</a>
        {:else}
          <span class="muted">—</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Стигма</dt>
      <dd class={scene.stigma_level ? stigmaClass[scene.stigma_level] : ''}>
        {#if scene.stigma_level}
          {@const e = entry('stigma_level', scene.stigma_level)}
          <span aria-hidden="true">●</span>{' '}
          <a href={codeHref(e)}>{e?.label ?? stigmaLabel[scene.stigma_level]}</a>
        {:else}
          <span class="muted">—</span>
        {/if}
      </dd>
    </div>
    <div>
      <dt>Типы реплик</dt>
      <dd>
        {#each scene.utterance_types as u}
          {@const e = entry('utterance_type', u)}
          <a href={codeHref(e)}>{e?.label ?? u}</a>{' '}
        {/each}
      </dd>
    </div>
    <div>
      <dt>Визуальные тропы</dt>
      <dd>
        {#each scene.visual_tropes as t}
          {@const e = entry('visual_trope', t)}
          <a href={codeHref(e)}>{e?.label ?? t}</a>{' '}
        {/each}
      </dd>
    </div>
    <div class="scene-fields__wide">
      <dt>Функция сцены</dt>
      <dd>{scene.scene_function.join('; ') || '—'}</dd>
    </div>
    {#if scene.note}
      <div class="scene-fields__wide"><dt>Примечание</dt><dd class="note">{scene.note}</dd></div>
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
</style>
