<script lang="ts">
  import type { ApprovedMediaAsset } from '../lib/media';

  interface Props {
    asset: ApprovedMediaAsset;
    base: string;
    workTitle: string;
    workHref?: string;
    analysisUnitLabel?: string | null;
    chapterLabel?: string | null;
  }

  let {
    asset,
    base,
    workTitle,
    workHref,
    analysisUnitLabel = null,
    chapterLabel = null,
  }: Props = $props();
  const imageSrc = `${base.replace(/\/$/, '')}${asset.public_path}`;
  const kindLabel = asset.kind === 'film_still' ? 'Кадр из произведения' : 'Фотография';
</script>

<figure class="media-figure">
  <img src={imageSrc} alt={asset.alt} loading="lazy" decoding="async" />
  <figcaption>
    <p class="media-figure__caption">
      <span class="media-figure__kind">{kindLabel}</span>
      {asset.caption}
    </p>
    <p class="media-figure__context">
      <strong>Произведение:</strong>
      {#if workHref}
        <a href={workHref}>{workTitle}</a>
      {:else}
        {workTitle}
      {/if}
      {#if asset.scene_id && analysisUnitLabel}
        · <strong>Единица анализа:</strong>
        <a href={`${base}scene/${asset.scene_id}/`}>{analysisUnitLabel}</a>
      {:else if asset.analysis_unit === 'work_overall'}
        · <strong>Уровень анализа:</strong> произведение целиком
      {/if}
      {#if chapterLabel}
        · <strong>Глава:</strong> {chapterLabel}
      {/if}
    </p>
    {#if asset.analysis_purpose}
      <p class="media-figure__purpose">
        <strong>Аналитическая связь:</strong> {asset.analysis_purpose}
      </p>
    {/if}
    <p class="media-figure__attribution">
      {asset.attribution}
      · <a href={asset.source_url} target="_blank" rel="noopener noreferrer">Источник</a>
      {#if asset.license && asset.license_url}
        · <a href={asset.license_url} target="_blank" rel="noopener noreferrer">{asset.license}</a>
      {/if}
    </p>
  </figcaption>
</figure>

<style>
  .media-figure {
    margin: 1.25rem 0;
    min-width: 0;
  }
  .media-figure img {
    display: block;
    width: 100%;
    max-height: 38rem;
    object-fit: contain;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .media-figure figcaption {
    max-width: 48rem;
    margin-top: 0.5rem;
  }
  .media-figure__caption {
    margin: 0;
    font-size: 0.9rem;
  }
  .media-figure__kind {
    display: inline-block;
    margin-right: 0.4rem;
    color: var(--text-dim);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .media-figure__context {
    margin: 0.35rem 0 0;
    font-size: 0.82rem;
  }
  .media-figure__context strong {
    color: var(--text-dim);
    font-weight: 600;
  }
  .media-figure__purpose {
    margin: 0.35rem 0 0;
    font-size: 0.85rem;
  }
  .media-figure a:focus-visible {
    outline: 2px solid var(--orange);
    outline-offset: 2px;
    border-radius: 2px;
  }
  .media-figure__purpose strong {
    color: var(--text-dim);
    font-weight: 600;
  }
  .media-figure__attribution {
    margin: 0.2rem 0 0;
    color: var(--text-dim);
    font-size: 0.78rem;
  }
</style>
