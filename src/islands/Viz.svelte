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
  interface NamedCount {
    id: string;
    label: string;
    count: number;
  }
  interface MatrixData {
    rows: { id: string; label: string }[];
    cols: { id: string; label: string }[];
    cells: { row: string; col: string; count: number }[];
  }
  interface VizGroup {
    label: string;
    units: number;
    counts?: NamedCount[];
    tropes?: NamedCount[];
    matrix?: MatrixData;
  }
  const points = $derived((data.points as Point[]) ?? []);
  const groups = $derived((data.groups as VizGroup[]) ?? []);

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

  function unitWord(n: number): string {
    const mod10 = n % 10;
    const mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return 'единица';
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'единицы';
    return 'единиц';
  }

  const barW = 280;

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

  function cellCount(matrix: MatrixData | undefined, row: string, col: string) {
    return matrix?.cells.find((c) => c.row === row && c.col === col)?.count ?? 0;
  }
</script>

<div class="viz-block">
  <h3 class="viz-title">{title}</h3>
  {#if subtitle}<p class="muted small">{subtitle}</p>{/if}

  {#if timeline}
    {@const tl = timeline!}
    {@const scenePts = points.filter((p) => p.analysis_unit === 'scene')}
    {@const overallPts = points.filter((p) => p.analysis_unit !== 'scene')}
    {#each [
      { label: 'Сцены', pts: scenePts, kind: 'circle' },
      { label: 'Произведения целиком', pts: overallPts, kind: 'rect' },
    ] as grp}
      {#if grp.pts.length}
        <h4 class="viz-sub">{grp.label} · {grp.pts.length} {unitWord(grp.pts.length)}</h4>
        <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title} — {grp.label}">
          <title>{title} — {grp.label}</title>
          {#each tl.ticks as t}
            <line x1={tl.x(t)} y1={PAD.t} x2={tl.x(t)} y2={H - PAD.b} stroke="var(--border)" stroke-width="1" />
            <text x={tl.x(t)} y={H - PAD.b + 16} fill="var(--text-dim)" font-size="11" text-anchor="middle">{t}</text>
          {/each}
          {#each ['low', 'medium', 'high'] as level}
            <text x={PAD.l - 8} y={tl.y(level) + 4} fill="var(--text-dim)" font-size="11" text-anchor="end">
              {{ low: 'Низкий', medium: 'Средний', high: 'Высокий' }[level]}
            </text>
            <line x1={PAD.l} y1={tl.y(level)} x2={W - PAD.r} y2={tl.y(level)} stroke="var(--border)" stroke-width="1" stroke-dasharray="3 4" />
          {/each}
          {#each grp.pts as p}
            {@const cx = tl.x(p.year)}
            {@const cy = tl.y(p.stigma)}
            {#if grp.kind === 'circle'}
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
      {/if}
    {/each}
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
  {:else if groups.length}
    {#each groups as g}
      <h4 class="viz-sub">{g.label} · {g.units} {unitWord(g.units)}</h4>

      {#if g.counts?.length}
        {#if kind === 'ethics-counts'}
          <p class="viz-ethics-counts">
            {#each g.counts as c}{c.label}: <strong>{c.count}</strong>{c.id !== g.counts[g.counts.length - 1].id ? ' · ' : ''}{/each}
          </p>
        {/if}
        {@const gMax = Math.max(1, ...g.counts.map((c) => c.count))}
        <svg viewBox="0 0 720 {Math.max(120, g.counts.length * 44 + 30)}" role="img" aria-label="{title} — {g.label}">
          <title>{title} — {g.label}</title>
          {#each g.counts as c, i}
            {@const y = 20 + i * 44}
            {#each wrapLabel(c.label) as line, li}
              <text x="0" y={y + 10 + li * 13} fill="var(--text)" font-size="11.5">{line}</text>
            {/each}
            <rect x={barW} y={y} width={(c.count / gMax) * (W - barW - 50)} height="18" fill="var(--accent)">
              <title>{c.label}: {c.count}</title>
            </rect>
            <text x={barW + (c.count / gMax) * (W - barW - 50) + 6} y={y + 14} fill="var(--text-dim)" font-size="12">{c.count}</text>
          {/each}
        </svg>
        <table>
          <caption>{g.label}</caption>
          <thead><tr><th>Значение</th><th>Число единиц</th></tr></thead>
          <tbody>
            {#each g.counts as c}<tr><td>{c.label}</td><td>{c.count}</td></tr>{/each}
          </tbody>
        </table>
      {/if}

      {#if g.tropes?.length}
        <h4 class="viz-sub">Визуальные тропы · {g.label}</h4>
        <table>
          <caption>Визуальные тропы — {g.label}</caption>
          <thead><tr><th>Троп</th><th>Число единиц</th></tr></thead>
          <tbody>
            {#each g.tropes as t}<tr><td>{t.label}</td><td>{t.count}</td></tr>{/each}
          </tbody>
        </table>
      {/if}

      {#if g.matrix}
        <table class="matrix">
          <caption>{g.label}</caption>
          <thead>
            <tr><th>Архетип \ Пространство</th>{#each g.matrix.cols as c}<th>{c.label}</th>{/each}</tr>
          </thead>
          <tbody>
            {#each g.matrix.rows as r}
              <tr>
                <th>{r.label}</th>
                {#each g.matrix.cols as c}
                  {@const n = cellCount(g.matrix, r.id, c.id)}
                  <td class="matrix__cell" style:background-color={n ? `color-mix(in srgb, var(--accent) ${Math.min(80, n * 25)}%, transparent)` : 'transparent'}>
                    {n || ''}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    {/each}
    <p class="viz-note muted small">{caption}</p>
  {/if}
</div>

<style>
  .viz-title { margin-top: 0; }
  .viz-ethics-counts { margin: 0.25rem 0 0.75rem; font-size: 0.95rem; }
  .viz-legend text { font-family: var(--font); }
  .viz-sub { margin: 1rem 0 0.25rem; font-size: 0.95rem; }
  .viz-note { margin-top: 0.75rem; }
  .matrix td, .matrix th { text-align: center; }
  .matrix__cell { min-width: 3.5rem; }
</style>
