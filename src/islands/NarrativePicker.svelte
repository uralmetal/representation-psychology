<script lang="ts">
  import { strings } from '../lib/i18n';

  export interface PickItem {
    id: string;
    label: string;
    text: string;
    /** одна ссылка-якорь (для линз — переход к главе) */
    href?: string;
    hrefLabel?: string;
    /** набор ссылок (для вердиктов эпилога) */
    links?: { label: string; href: string }[];
  }

  interface Props {
    items: PickItem[];
    groupLabel: string;
  }
  let { items, groupLabel }: Props = $props();

  let selectedId = $state<string | null>(null);
  const selected = $derived(items.find((i) => i.id === selectedId) ?? null);
</script>

<div class="picker" role="group" aria-label={groupLabel}>
  <div class="picker__options">
    {#each items as item}
      <button
        type="button"
        class="picker__option"
        class:is-selected={item.id === selectedId}
        aria-pressed={item.id === selectedId}
        onclick={() => (selectedId = item.id)}
      >{item.label}</button>
    {/each}
  </div>

  {#if selected}
    <p class="sr-only" role="status">Выбрано: {selected.label}.</p>
    <div class="picker__detail">
      <p class="picker__text">{selected.text}</p>
      {#if selected.href}
        <p class="picker__link"><a href={selected.href}>{selected.hrefLabel ?? strings.story.nextChapter} →</a></p>
      {/if}
      {#if selected.links?.length}
        <p class="picker__links">
          {#each selected.links as l, i}
            {#if i > 0} · {/if}<a href={l.href}>{l.label}</a>
          {/each}
        </p>
      {/if}
    </div>
  {:else}
    <p class="picker__prompt muted small">{strings.story.pickPrompt}</p>
  {/if}
</div>

<style>
  .picker {
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 1.25rem 0;
  }
  .picker__options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }
  .picker__option {
    border: 1px solid var(--border);
    background: var(--bg-soft);
    color: var(--text);
    border-radius: 8px;
    padding: 0.5rem 0.85rem;
    font-size: 0.88rem;
    cursor: pointer;
    text-align: left;
  }
  .picker__option:hover { border-color: var(--accent); }
  .picker__option.is-selected {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--accent-ink);
  }
  .picker__prompt { margin: 0.8rem 0 0; }
  .picker__detail {
    margin-top: 1rem;
    border-left: 3px solid var(--orange);
    padding-left: 0.9rem;
  }
  .picker__text { margin: 0 0 0.5rem; font-size: 0.92rem; }
  .picker__link, .picker__links { margin: 0.3rem 0 0; font-size: 0.88rem; }
</style>
