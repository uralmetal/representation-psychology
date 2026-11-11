<script lang="ts">
  import { onMount } from 'svelte';
  import WorkFeature from '../components/WorkFeature.svelte';
  import { strings } from '../lib/i18n';
  import type { CodebookEntry, Scene, StoryStep, Work } from '../lib/types';

  interface Props {
    steps: StoryStep[];
    works: Work[];
    scenes: Scene[];
    entries: CodebookEntry[];
    base: string;
  }
  let { steps, works, scenes, entries, base }: Props = $props();

  const sorted = $derived([...steps].sort((a, b) => a.order - b.order));
  const activeStep = $derived(sorted[active]);

  const workById = $derived(new Map(works.map((w) => [w.id, w])));
  const activeWork = $derived(
    activeStep?.workId ? workById.get(activeStep.workId) : undefined,
  );
  const activeScenes = $derived(
    activeStep?.workId ? scenes.filter((s) => s.work_id === activeStep.workId) : [],
  );

  const yearMin = $derived(Math.min(...works.map((w) => w.year_start)));
  const yearMax = $derived(Math.max(...works.map((w) => w.year_end)));
  const catTotal = $derived(new Set(entries.map((e) => e.category)).size);

  let active = $state(0);
  let root: HTMLElement | undefined = $state();

  onMount(() => {
    const els = Array.from(root!.querySelectorAll<HTMLElement>('.step'));
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          const i = els.indexOf(e.target as HTMLElement);
          if (i >= 0) active = i;
        }
      },
      { rootMargin: '-30% 0px -60% 0px' },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  });

  $effect(() => {
    const anchor = activeStep?.anchor;
    if (anchor && typeof history !== 'undefined') {
      history.replaceState(null, '', `#${anchor}`);
    }
  });

  function go(i: number) {
    const el = root?.querySelectorAll<HTMLElement>('.step')[i];
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }

  function years(w: Work): string {
    return w.year_start === w.year_end ? String(w.year_start) : `${w.year_start}–${w.year_end}`;
  }

  function showFilms(s: StoryStep): boolean {
    return s.kind === 'chapter' && s.tag === 'content' && s.workIds.length > 0;
  }
</script>

{#snippet miniCard(w: Work)}
  <a class="card mini-card" href="{base}work/{w.id}/">
    <span class="mini-card__year">{years(w)}</span>
    <span class="mini-card__body">
      <span class="mini-card__title">{w.title}</span>
      <span class="muted small">{w.format === 'tv_series' ? 'сериал' : 'фильм'}</span>
    </span>
  </a>
{/snippet}

<div class="scrolly" bind:this={root}>
  <div class="scrolly__steps">
    {#each sorted as s}
      <section class="step" id={s.anchor}>
        <p class="step__kicker">{s.kicker}</p>
        <h2>{s.title}</h2>
        <div class="step__body">{@html s.html}</div>
        {#if showFilms(s)}
          <div class="step__works">
            <p class="step__works-label">{strings.story.stepWorks}</p>
            <div class="step__works-list">
              {#each s.workIds as wid}
                {@const w = workById.get(wid)}
                {#if w}{@render miniCard(w)}{/if}
              {/each}
            </div>
          </div>
        {/if}
      </section>
    {/each}
  </div>

  <div class="scrolly__stage-wrap">
    <aside class="scrolly__stage" aria-label={strings.story.title}>
      <ol class="stage__rail">
        {#each sorted as s, i}
          <li>
            <button
              type="button"
              class:is-active={i === active}
              aria-current={i === active ? 'true' : undefined}
              onclick={() => go(i)}
            >
              <span class="stage__num">{i + 1}</span>
              <span class="stage__label">{s.title}</span>
            </button>
          </li>
        {/each}
      </ol>

      <div class="stage__panel">
        {#if activeStep?.kind === 'film' && activeWork}
          {#key activeStep.anchor}
            <WorkFeature work={activeWork} scenes={activeScenes} {entries} {base} />
          {/key}
        {:else if activeStep && showFilms(activeStep)}
          <div class="stage-films">
            <p class="stage-works__label">{strings.story.stepWorks}</p>
            {#each activeStep.workIds as wid}
              {@const w = workById.get(wid)}
              {#if w}{@render miniCard(w)}{/if}
            {/each}
          </div>
        {:else if activeStep?.tag === 'prologue'}
          <div class="card stage__info">
            <h3>{strings.siteTitle}</h3>
            <p class="muted small">{strings.home.thesis}</p>
            <p class="muted small">
              {works.length} произведений · {catTotal} категорий словаря · {yearMin}–{yearMax}
            </p>
          </div>
        {:else if activeStep?.tag === 'epilogue'}
          <div class="card stage__info">
            <h3>{strings.story.endTitle}</h3>
            <p class="muted small">{strings.footer.disclaimer}</p>
            <p class="small"><a href="{base}method/">{strings.nav.method} →</a></p>
          </div>
        {/if}
      </div>
    </aside>
  </div>
</div>

<style>
  .scrolly {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(19rem, 26rem);
    gap: 3rem;
    align-items: start;
  }

  .step {
    margin-bottom: 7rem;
    scroll-margin-top: 1rem;
  }
  .step__kicker {
    font-family: var(--mono);
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 0 0 0.2rem;
  }
  .step__body :global(p) { margin: 0.75rem 0; }
  .step__body :global(strong) { color: var(--accent); }
  .step__body :global(.film-meta) { color: var(--text-dim); font-size: 0.9rem; }
  .step__body :global(.film-codes) {
    list-style: none;
    padding: 0;
    margin: 0.75rem 0;
    display: grid;
    gap: 0.35rem;
    font-size: 0.92rem;
  }
  .step__body :global(.film-codes strong) { color: var(--accent); }
  .step__body :global(.film-note) { margin: 0.5rem 0; }
  .step__body :global(.film-link) { margin: 0.75rem 0 0; }
  .step__works { display: none; }

  .scrolly__stage-wrap {
    position: sticky;
    top: 0;
    height: 100vh;
  }
  .scrolly__stage {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.5rem 0.25rem 1rem 0;
  }

  .stage__rail {
    list-style: none;
    margin: 0;
    padding: 0.25rem 0 0.5rem;
    overflow-y: auto;
    flex: 0 1 auto;
    max-height: 11rem;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }
  .stage__rail button {
    display: flex;
    gap: 0.55rem;
    align-items: baseline;
    width: 100%;
    background: none;
    border: none;
    border-left: 2px solid var(--border);
    padding: 0.22rem 0.55rem;
    color: var(--text-dim);
    cursor: pointer;
    text-align: left;
    font: inherit;
    font-size: 0.8rem;
  }
  .stage__rail button:hover { color: var(--text); }
  .stage__rail button.is-active {
    border-left-color: var(--accent);
    color: var(--text);
  }
  .stage__num {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--accent);
    min-width: 1.1rem;
  }
  .stage__label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .stage__panel {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding-right: 0.35rem;
  }

  .stage-works__label,
  .step__works-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
    margin: 0 0 0.45rem;
  }

  .mini-card {
    display: flex;
    gap: 0.8rem;
    align-items: baseline;
    color: var(--text);
    text-decoration: none;
    margin-bottom: 0.5rem;
    padding: 0.55rem 0.8rem;
    transition:
      border-color 0.2s ease,
      transform 0.2s ease;
  }
  .mini-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
  }
  .mini-card__year {
    font-family: var(--mono);
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--accent);
    min-width: 2.6rem;
  }
  .mini-card__body {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
  }
  .mini-card__title { font-size: 0.92rem; }

  .stage__info h3 { margin-top: 0; }
  .stage__info p { margin: 0.4rem 0; }

  @media (max-width: 60rem) {
    .scrolly { grid-template-columns: 1fr; }
    .scrolly__stage-wrap { display: none; }
    .step { margin-bottom: 4rem; }
    .step__works { display: block; margin-top: 1.25rem; }
    .step__works-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
      gap: 0.5rem;
    }
  }
</style>
