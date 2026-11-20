import type { CodebookEntry, Scene, Work } from './types';

export interface VizPoint {
  id: string;
  work_id: string;
  title: string;
  year: number;
  analysis_unit: string;
  stigma: string | null;
  archetypes: string[];
  space: string | null;
  ethics: string | null;
}

export interface NamedCount {
  id: string;
  label: string;
  count: number;
}

export interface MatrixCell {
  archetype: string;
  space: string;
  count: number;
}

function labelOf(entries: CodebookEntry[], category: string, value: string | null): string {
  if (!value) return '';
  return entries.find((e) => e.category === category && e.value === value)?.label ?? value;
}

export function vizPoints(works: Work[], scenes: Scene[], entries: CodebookEntry[]): VizPoint[] {
  const byId = new Map(works.map((w) => [w.id, w]));
  return scenes.map((s) => {
    const work = byId.get(s.work_id);
    return {
      id: s.id,
      work_id: s.work_id,
      title: work?.title ?? s.work_id,
      year: work?.year_start ?? 0,
      analysis_unit: s.analysis_unit,
      stigma: s.stigma_level,
      archetypes: s.therapist_archetype,
      space: s.space_type,
      ethics: s.ethical_violation,
    };
  });
}

export function archetypeCounts(scenes: Scene[], entries: CodebookEntry[]): NamedCount[] {
  const counts = new Map<string, number>();
  for (const s of scenes) {
    for (const a of s.therapist_archetype) counts.set(a, (counts.get(a) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([id, count]) => ({ id, label: labelOf(entries, 'therapist_archetype', id) || id, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ru'));
}

export function spaceMatrix(scenes: Scene[], entries: CodebookEntry[]): {
  archetypes: NamedCount[];
  spaces: NamedCount[];
  cells: MatrixCell[];
} {
  const archOrder = new Map<string, number>();
  const spaceOrder = new Map<string, number>();
  const cells = new Map<string, number>();
  for (const s of scenes) {
    for (const a of s.therapist_archetype) {
      if (!archOrder.has(a)) archOrder.set(a, archOrder.size);
      const space = s.space_type ?? 'none';
      if (!spaceOrder.has(space)) spaceOrder.set(space, spaceOrder.size);
      const key = `${a}|${space}`;
      cells.set(key, (cells.get(key) ?? 0) + 1);
    }
  }
  const mk = (order: Map<string, number>, cat: string) =>
    [...order.keys()]
      .sort((x, y) => order.get(x)! - order.get(y)!)
      .map((id) => ({
        id,
        label: id === 'none' ? 'Нет кода' : labelOf(entries, cat, id) || id,
        count: 0,
      }));
  const archetypes = mk(archOrder, 'therapist_archetype');
  const spaces = mk(spaceOrder, 'space_type');
  const cellList: MatrixCell[] = [];
  for (const [key, count] of cells) {
    const [archetype, space] = key.split('|');
    cellList.push({ archetype, space, count });
  }
  return { archetypes, spaces, cells: cellList };
}

export function ethicsCounts(scenes: Scene[], entries: CodebookEntry[]): NamedCount[] {
  const order = ['yes', 'partial', 'no'];
  const counts = new Map<string, number>();
  for (const s of scenes) if (s.ethical_violation) counts.set(s.ethical_violation, (counts.get(s.ethical_violation) ?? 0) + 1);
  return order
    .filter((id) => counts.has(id))
    .map((id) => ({ id, label: labelOf(entries, 'ethical_violation', id) || id, count: counts.get(id)! }));
}

export function utteranceCounts(scenes: Scene[], entries: CodebookEntry[]): NamedCount[] {
  const counts = new Map<string, number>();
  for (const s of scenes) for (const u of s.utterance_types) counts.set(u, (counts.get(u) ?? 0) + 1);
  return [...counts.entries()]
    .map(([id, count]) => ({ id, label: labelOf(entries, 'utterance_type', id) || id, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ru'));
}

export function tropeCounts(scenes: Scene[], entries: CodebookEntry[]): NamedCount[] {
  const counts = new Map<string, number>();
  for (const s of scenes) for (const t of s.visual_tropes) counts.set(t, (counts.get(t) ?? 0) + 1);
  return [...counts.entries()]
    .map(([id, count]) => ({ id, label: labelOf(entries, 'visual_trope', id) || id, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ru'));
}
