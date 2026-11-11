<script lang="ts">
  interface Props {
    kind: string;
    title: string;
    subtitle: string;
    caption: string;
    data: Record<string, unknown>;
  }
  let { kind, title, subtitle, caption, data }: Props = $props();

  const STIGMA_COLOR: Record<string, string> = {
    high: 'var(--stigma-high)',
    medium: 'var(--stigma-medium)',
    low: 'var(--stigma-low)',
  };
  const STIGMA_RANK: Record<string, number> = { low: 0, medium: 1, high: 2 };

  interface Point {
    id: string;
    title: string;
    year: number;
    analysis_unit: string;
    stigma: string | null;
  }
  const points = $derived((data.points as Point[]) ?? []);
  const counts = $derived((data.counts as { id: string; label: string; count: number }[]) ?? []);
  const matrix = $derived(data.matrix as {
    rows: { id: string; label: string }[];
    cols: { id: string; label: string }[];
    cells: { row: string; col: string; count: number }[];
  } | undefined);
  const tropes = $derived((data.tropes as { id: string; label: string; count: number }[]) ?? []);

  const W = 720;
  const H = 260;
  const PAD = { l: 56, r: 16, t: 20, b: 40 };

  const timeline = $derived.by(() => {
    if (!['corpus-timeline', 'stigma-timeline'].includes(kind) || points.length === 0) return null;
    const years = points.map((p) => p.year);
    const x0 = Math.min(...years) - 1;
    const x1 = Math.max(...years) + 1;
    const x = (year: number) => PAD.l + ((year - x0) / (x1 - x0)) * (W - PAD.l - PAD.r);
    const yLevels = ['low', 'medium', 'high'];
    const y = (stigma: string | null) => {
      const idx = stigma ? yLevels.indexOf(stigma) : -1;
      return PAD.t + (2 - Math.max(idx, 0)) * ((H - PAD.t - PAD.b) / 2) + (idx < 0 ? (H - PAD.t - PAD.b) / 4 : 0);
    };
    const ticks = Array.from({ length: x1 - x0 + 1 }, (_, i) => x0 + i).filter(
      (v, i, a) => i === 0 || v % 5 === 0 || i === a.length - 1,
    );
    return { x, y, ticks, x0, x1 };
  });

  const maxCount = $derived(Math.max(1, ...counts.map((c) => c.count)));
  const barW = $derived(kind === 'ethics-counts' ? 200 : 280);

  function wrapLabel(label: string, max = 30): string[] {
    if (label.length <= max) return [label];
    const words = label.split(' ');
    const lines: string[] = [];
    let cur = '';
    for (const w of words) {
      if ((cur + ' ' + w).trim().length > max) {
        lines.push(cur.trim());
        cur = w;
      } else {
        cur = (cur + ' ' + w).trim();
      }
    }
    if (cur) lines.push(cur);
    return lines.slice(0, 2);
  }

  function cellCount(row: string, col: string) {
    return matrix?.cells.find((c) => c.row === row && c.col === col)?.count ?? 0;
  }
</script>

<div class="viz-block">
  <h3 class="viz-title">{title}</h3>
  {#if subtitle}<p class="muted small">{subtitle}</p>{/if}

  {#if timeline}
    {@const tl = timeline!}
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title}>
      <title>{title}</title>
      {#each tl.ticks as t}
        <line x1={tl.x(t)} y1={PAD.t} x2={tl.x(t)} y2={H - PAD.b} stroke="var(--border)" stroke-width="1" />
        <text x={tl.x(t)} y={H - PAD.b + 18} fill="var(--text-dim)" font-size="11" text-anchor="middle">{t}</text>
      {/each}
      {#each ['low', 'medium', 'high'] as level, i}
        <text x={PAD.l - 8} y={tl.y(level) + 4} fill="var(--text-dim)" font-size="11" text-anchor="end">
          {{ low: 'Низкий', medium: 'Средний', high: 'Высокий' }[level]}
        </text>
        <line x1={PAD.l} y1={tl.y(level)} x2={W - PAD.r} y2={tl.y(level)} stroke="var(--border)" stroke-width="1" stroke-dasharray="3 4" />
      {/each}
      {#each points as p}
        {@const cx = tl.x(p.year)}
        {@const cy = tl.y(p.stigma)}
        {#if p.analysis_unit === 'scene'}
          <circle cx={cx} cy={cy} r="6" fill={STIGMA_COLOR[p.stigma ?? 'medium'] ?? 'var(--scene)'} stroke="var(--bg)" stroke-width="1.5">
            <title>{p.title} ({p.year})</title>
          </circle>
        {:else}
          <rect x={cx - 5} y={cy - 5} width="10" height="10" fill={STIGMA_COLOR[p.stigma ?? 'medium'] ?? 'var(--overall)'} stroke="var(--bg)" stroke-width="1.5">
            <title>{p.title} ({p.year})</title>
          </rect>
        {/if}
      {/each}
    </svg>
    <table>
      <caption>{caption}</caption>
      <thead><tr><th>Произведение</th><th>Год</th><th>Единица</th><th>Стигма</th></tr></thead>
      <tbody>
        {#each points as p}
          <tr>
            <td>{p.title}</td><td>{p.year}</td>
            <td>{p.analysis_unit === 'scene' ? 'сцена' : 'целиком'}</td>
            <td>{p.stigma ?? '—'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else if matrix}
    <table class="matrix">
      <caption>{caption}</caption>
      <thead>
        <tr><th>Архетип \ Пространство</th>{#each matrix.cols as c}<th>{c.label}</th>{/each}</tr>
      </thead>
      <tbody>
        {#each matrix.rows as r}
          <tr>
            <th>{r.label}</th>
            {#each matrix.cols as c}
              {@const n = cellCount(r.id, c.id)}
              <td class="matrix__cell" style:background-color={n ? `color-mix(in srgb, var(--accent) ${Math.min(80, n * 25)}%, transparent)` : 'transparent'}>
                {n || ''}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <svg viewBox="0 0 720 {Math.max(120, counts.length * 44 + 30)}" role="img" aria-label={title}>
      <title>{title}</title>
      {#each counts as c, i}
        {@const y = 20 + i * 44}
        {#each wrapLabel(c.label) as line, li}
          <text x="0" y={y + 10 + li * 13} fill="var(--text)" font-size="11.5">{line}</text>
        {/each}
        <rect x={barW} y={y} width={(c.count / maxCount) * (W - barW - 50)} height="18" fill="var(--accent)">
          <title>{c.label}: {c.count}</title>
        </rect>
        <text x={barW + (c.count / maxCount) * (W - barW - 50) + 6} y={y + 14} fill="var(--text-dim)" font-size="12">{c.count}</text>
      {/each}
    </svg>
    <table>
      <caption>{caption}</caption>
      <thead><tr><th>Значение</th><th>Число единиц</th></tr></thead>
      <tbody>
        {#each counts as c}<tr><td>{c.label}</td><td>{c.count}</td></tr>{/each}
      </tbody>
    </table>
    {#if tropes.length}
      <h4 class="viz-sub">Визуальные тропы</h4>
      <table>
        <thead><tr><th>Троп</th><th>Число единиц</th></tr></thead>
        <tbody>
          {#each tropes as t}<tr><td>{t.label}</td><td>{t.count}</td></tr>{/each}
        </tbody>
      </table>
    {/if}
  {/if}

  <p class="viz-caption">{caption}</p>
</div>

<style>
  .viz-title { margin-top: 0; }
  .viz-sub { margin: 1rem 0 0.25rem; font-size: 0.95rem; }
  .matrix td, .matrix th { text-align: center; }
  .matrix__cell { min-width: 3.5rem; }
</style>
