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
  const scenesByWorkId = $derived.by(() => {
    const map = new Map<string, Scene[]>();
    for (const s of scenes) {
      const list = map.get(s.work_id) ?? [];
      list.push(s);
      map.set(s.work_id, list);
    }
    return map;
  });

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

    const hash = decodeURIComponent(window.location.hash.replace('#', ''));
    if (hash) {
      const i = sorted.findIndex((s) => s.anchor === hash);
      if (i >= 0) {
        active = i;
        requestAnimationFrame(() => go(i));
      }
    }
    return () => io.disconnect();
  });

  $effect(() => {
    const anchor = activeStep?.anchor;
    if (anchor && typeof history !== 'undefined') {
      history.replaceState(null, '', `#${anchor}`);
      try {
        sessionStorage.setItem('rp:last-anchor', anchor);
      } catch {
        /* sessionStorage недоступен */
      }
    }
  });

  function go(i: number) {
    const el = root?.querySelectorAll<HTMLElement>('.step')[i];
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    const anchor = sorted[i]?.anchor;
    if (anchor && typeof history !== 'undefined') {
      history.pushState(null, '', `#${anchor}`);
    }
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

<nav class="story-toc" aria-label={strings.story.contents}>
  <p class="story-toc__title">{strings.story.contents}</p>
  <ol class="story-toc__list">
    {#each sorted as s, i}
      <li>
        <a
          href="#{s.anchor}"
          class:is-active={i === active}
          aria-current={i === active ? 'true' : undefined}
          onclick={(e) => { e.preventDefault(); go(i); }}
        >{s.title}</a>
      </li>
    {/each}
  </ol>
</nav>

<div class="scrolly" bind:this={root}>
  <div class="scrolly__steps">
    {#each sorted as s}
      <section class="step" id={s.anchor}>
        <p class="step__kicker">{s.kicker}</p>
        <h2>{s.title}</h2>
        {#if s.html}<div class="step__body">{@html s.html}</div>{/if}
        {#if s.kind === 'film'}
          {@const w = s.workId ? workById.get(s.workId) : undefined}
          {#if w}
            <WorkFeature work={w} scenes={scenesByWorkId.get(w.id) ?? []} {entries} {base} />
          {/if}
        {/if}
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
</div>

<style>
  .scrolly { max-width: 56rem; }

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
  .step__works { margin-top: 1.25rem; }
  .step__works-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
    gap: 0.5rem;
  }

  .story-toc {
    margin: 0 0 2rem;
    padding: 0.9rem 1.1rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .story-toc__title {
    margin: 0 0 0.5rem;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
  }
  .story-toc__list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem 0.9rem;
  }
  .story-toc__list a {
    color: var(--text-dim);
    text-decoration: none;
    font-size: 0.9rem;
    border-bottom: 1px dotted transparent;
  }
  .story-toc__list a:hover { color: var(--accent); border-bottom-color: var(--accent); }
  .story-toc__list a.is-active { color: var(--accent); }

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

  @media (max-width: 60rem) {
    .step { margin-bottom: 4rem; }
  }
</style>
