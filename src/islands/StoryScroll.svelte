<script lang="ts">
  import { onMount } from 'svelte';
  import CategoryExplorer from './CategoryExplorer.svelte';
  import EvidenceCard from '../components/EvidenceCard.svelte';
  import NarrativePicker from './NarrativePicker.svelte';
  import Viz from './Viz.svelte';
  import { LENSES, buildVerdicts } from '../lib/narrative';
  import { strings } from '../lib/i18n';
  import { vizSpec } from '../lib/vizspec';
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
  const sceneById = $derived(new Map(scenes.map((s) => [s.id, s])));

  const EXPLORER_CATS: Record<string, { keys: string[]; note?: string }> = {
    archetype: {
      keys: ['therapist_archetype'],
      note: 'Сестра Рэтчед в «Пролетая над гнездом кукушки» рассматривается как носитель профессиональной власти; интерфейс не приписывает ей профессию психолога или психиатра.',
    },
    space: {
      keys: ['space_type'],
      note: 'В кодировании «Опасного метода» сохранено значение ward, тогда как пример словаря scientific-clinic относится к тому же произведению — расхождение показано как есть и не исправляется.',
    },
    ethics: {
      keys: ['ethical_violation'],
      note: '«Частично» — спорная ситуация в конкретной единице анализа, а не приговор всей практике персонажа.',
    },
    stigma: {
      keys: ['stigma_level'],
      note: 'Уровень стигмы относится к репрезентации профессии на экране, а не к пациентам и не к психическим расстройствам.',
    },
    communication: { keys: ['utterance_type', 'visual_trope'] },
  };

  const CHAPTER_CAT: Record<string, string | undefined> = {
    archetype: 'therapist_archetype',
    space: 'space_type',
    ethics: 'ethical_violation',
    stigma: 'stigma_level',
  };

  const HASH_ALIAS: Record<string, string> = { language: 'communication' };

  function resolveAnchor(hash: string): { index: number; workId: string | null } {
    const h = HASH_ALIAS[hash] ?? hash;
    let i = sorted.findIndex((s) => s.anchor === h);
    if (i >= 0) return { index: i, workId: null };
    i = sorted.findIndex((s) => s.workIds.includes(h));
    if (i >= 0) return { index: i, workId: h };
    return { index: -1, workId: null };
  }

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
      const { index, workId } = resolveAnchor(hash);
      if (index >= 0) {
        active = index;
        requestAnimationFrame(() => {
          if (workId) {
            root
              ?.querySelector<HTMLElement>(`[data-work="${workId}"]`)
              ?.scrollIntoView({ block: 'start' });
          } else {
            go(index);
          }
        });
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

  function lensItems() {
    return LENSES.map((l) => ({
      id: l.id,
      label: l.label,
      text: l.text,
      href: `#${l.target}`,
      hrefLabel: sorted.find((s) => s.anchor === l.target)?.title ?? l.target,
    }));
  }

  function stepScenes(s: StoryStep): Scene[] {
    return s.sceneIds
      .map((id) => sceneById.get(id))
      .filter((sc): sc is Scene => Boolean(sc));
  }
</script>

<div class="story-layout">
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
          ><span class="story-toc__num">{s.num}</span>{s.title}</a>
        </li>
      {/each}
    </ol>
  </nav>

  <div class="scrolly" bind:this={root}>
    <div class="scrolly__steps">
      {#each sorted as s, i}
        <section class="step" id={s.anchor}>
          <p class="step__kicker">{s.kicker}</p>
          <h2 class="step__title">{s.title}</h2>
          {#if s.html}<div class="step__body">{@html s.html}</div>{/if}

          {#if s.tag === 'prologue'}
            <NarrativePicker items={lensItems()} groupLabel={strings.story.lensesTitle} />
          {:else if s.anchor === 'epilogue'}
            <NarrativePicker items={buildVerdicts(base)} groupLabel={strings.story.verdictsTitle} />
          {:else if EXPLORER_CATS[s.anchor]}
            {@const cfg = EXPLORER_CATS[s.anchor]}
            <CategoryExplorer
              catKeys={cfg.keys}
              scenes={scenes}
              {works}
              {entries}
              {base}
              note={cfg.note}
            />
          {/if}

          {#if s.viz}
            {@const spec = vizSpec(s.viz, works, scenes, entries)}
            {#if spec}
              <Viz
                kind={spec.kind}
                title={spec.title}
                subtitle={spec.subtitle}
                caption={spec.caption}
                data={spec.data}
              />
            {/if}
          {/if}

          {#if stepScenes(s).length}
            <h3 class="step__ev-title">{strings.story.evidence}</h3>
            <div class="step__evidence">
              {#each stepScenes(s) as sc}
                <EvidenceCard
                  scene={sc}
                  work={workById.get(sc.work_id)}
                  {entries}
                  {base}
                  catKey={CHAPTER_CAT[s.anchor]}
                />
              {/each}
            </div>
          {/if}

          {#if i < sorted.length - 1}
            <p class="step__next">
              <a href="#{sorted[i + 1].anchor}" onclick={(e) => { e.preventDefault(); go(i + 1); }}>
                {strings.story.nextChapter}: {sorted[i + 1].title} →
              </a>
            </p>
          {/if}
        </section>
      {/each}
    </div>
  </div>
</div>

<style>
  .story-layout {
    display: grid;
    gap: 1.5rem;
  }

  .scrolly { max-width: 56rem; min-width: 0; }

  .step {
    margin-bottom: 6rem;
    scroll-margin-top: 1rem;
  }
  .step__kicker {
    font-family: var(--mono);
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--orange);
    margin: 0 0 0.2rem;
  }
  .step__title {
    font-family: var(--serif);
    font-size: 1.9rem;
    font-weight: 400;
    letter-spacing: -0.01em;
    margin: 0 0 0.75rem;
  }
  .step__body :global(p) { margin: 0.75rem 0; }
  .step__body :global(strong) { color: var(--accent); }
  .step__body :global(a) { color: var(--accent); }
  .step__ev-title {
    font-size: 1.05rem;
    margin: 1.75rem 0 0.6rem;
    font-family: var(--font);
    font-weight: 600;
  }
  .step__evidence {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr));
    gap: 0.6rem;
  }
  .step__next { margin-top: 1.5rem; font-size: 0.92rem; }

  .story-toc {
    padding: 0.9rem 1.1rem;
    background: var(--bg-elev);
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
  .story-toc__num {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--orange);
    margin-right: 0.25rem;
  }

  @media (min-width: 60rem) {
    .story-layout {
      grid-template-columns: 13rem minmax(0, 1fr);
      gap: 2rem;
    }
    .story-toc {
      position: sticky;
      top: 1rem;
      align-self: start;
    }
    .story-toc__list {
      flex-direction: column;
      flex-wrap: nowrap;
      gap: 0.15rem;
    }
    .story-toc__list a { display: block; padding: 0.2rem 0; }
  }

  @media (max-width: 60rem) {
    .step { margin-bottom: 4rem; }
    .story-toc__list {
      flex-wrap: nowrap;
      overflow-x: auto;
      padding-bottom: 0.3rem;
    }
    .story-toc__list a { white-space: nowrap; }
  }
</style>
