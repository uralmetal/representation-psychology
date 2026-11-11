<script lang="ts">
  import { onMount } from 'svelte';
  import SceneCard from '../components/SceneCard.svelte';
  import type { CodebookEntry, Scene, Work } from '../lib/types';

  interface Props {
    base: string;
  }
  let { base }: Props = $props();

  let dialog: HTMLDialogElement;
  let currentId = $state<string | null>(null);
  let works = $state<Work[]>([]);
  let scenes = $state<Scene[]>([]);
  let entries = $state<CodebookEntry[]>([]);
  let loaded = $state(false);
  let returnFocus: HTMLElement | null = null;

  const scene = $derived(scenes.find((s) => s.id === currentId));
  const work = $derived(works.find((w) => w.id === scene?.work_id));

  async function ensureData() {
    if (loaded) return;
    const [w, s, c] = await Promise.all([
      fetch(`${base}data/works.json`).then((r) => r.json()),
      fetch(`${base}data/scenes.json`).then((r) => r.json()),
      fetch(`${base}data/codebook.json`).then((r) => r.json()),
    ]);
    works = w.works;
    scenes = s.scenes;
    entries = c.entries;
    loaded = true;
  }

  function onClick(event: MouseEvent) {
    const link = (event.target as HTMLElement).closest?.('a[data-scene]');
    if (!(link instanceof HTMLAnchorElement)) return;
    event.preventDefault();
    const id = link.dataset.scene;
    if (!id) return;
    returnFocus = link;
    currentId = id;
    void ensureData().then(() => dialog?.showModal());
  }

  function onClose() {
    dialog?.close();
    returnFocus?.focus();
    currentId = null;
  }

  onMount(() => {
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  });
</script>

<dialog
  bind:this={dialog}
  aria-labelledby="scene-dialog-title"
  onclose={onClose}
  class="scene-dialog"
>
  <div class="scene-dialog__inner">
    <button type="button" class="scene-dialog__close" onclick={() => dialog?.close()} aria-label="Закрыть">
      ×
    </button>
    <h2 id="scene-dialog-title">{work?.title ?? 'Карточка единицы'}</h2>
    {#if scene}
      <SceneCard {scene} {work} {entries} {base} />
    {:else if loaded}
      <p class="muted">Единица не найдена.</p>
    {:else}
      <p class="muted">Загрузка…</p>
    {/if}
  </div>
</dialog>

<style>
  .scene-dialog {
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-elev);
    color: var(--text);
    max-width: min(46rem, 92vw);
    width: 100%;
    padding: 0;
  }
  .scene-dialog::backdrop { background: rgba(0, 0, 0, 0.55); }
  .scene-dialog__inner { padding: 1.25rem 1.5rem 1.5rem; position: relative; }
  .scene-dialog__close {
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    background: none;
    border: none;
    color: var(--text-dim);
    font-size: 1.6rem;
    cursor: pointer;
    line-height: 1;
  }
  .scene-dialog__close:hover { color: var(--text); }
  .scene-dialog h2 { margin-top: 0; }
</style>
