import { archetypeCounts, ethicsCounts, spaceMatrix, tropeCounts, utteranceCounts, vizPoints } from './viz';
import type { CodebookEntry, Scene, Work } from './types';

export interface VizSpec {
  kind: string;
  title: string;
  subtitle: string;
  caption: string;
  data: Record<string, unknown>;
}

const BASE_NOTE = 'Полный учтённый набор прототипа (9 единиц анализа), а не выборка кинематографа.';

export function vizSpec(id: string, works: Work[], scenes: Scene[], entries: CodebookEntry[]): VizSpec | null {
  const points = vizPoints(works, scenes, entries);
  switch (id) {
    case 'corpus-timeline':
      return {
        kind: 'corpus-timeline',
        title: 'Корпус прототипа по годам',
        subtitle: 'Круг — сцена, квадрат — произведение целиком. Цвет — уровень стигмы.',
        caption: `${BASE_NOTE} Ось — годы выхода произведений, не линия тренда.`,
        data: { points },
      };
    case 'stigma-timeline':
      return {
        kind: 'stigma-timeline',
        title: 'Стигма по годам',
        subtitle: 'Круг — сцена, квадрат — произведение целиком.',
        caption: `${BASE_NOTE} Ось — годы выхода произведений, не линия тренда.`,
        data: { points },
      };
    case 'archetype-counts':
      return {
        kind: 'archetype-counts',
        title: 'Архетипы терапевта',
        subtitle: 'Число единиц анализа на каждый архетип из словаря.',
        caption: `${BASE_NOTE} «Опасный метод» посчитан один раз — как «Романтизированный учёный».`,
        data: { counts: archetypeCounts(scenes, entries) },
      };
    case 'space-matrix':
      return {
        kind: 'space-matrix',
        title: 'Архетип × пространство',
        subtitle: 'Число единиц анализа в каждой ячейке матрицы.',
        caption: `${BASE_NOTE} «Веб-терапия» без кода пространства отражена в столбце «Нет кода».`,
        data: {
          matrix: (() => {
            const m = spaceMatrix(scenes, entries);
            return {
              rows: m.archetypes.map((a) => ({ id: a.id, label: a.label })),
              cols: m.spaces.map((s) => ({ id: s.id, label: s.label })),
              cells: m.cells.map((c) => ({ row: c.archetype, col: c.space, count: c.count })),
            };
          })(),
        },
      };
    case 'ethics-counts':
      return {
        kind: 'ethics-counts',
        title: 'Этическое нарушение',
        subtitle: 'Распределение единиц по кодам «Да / Частично / Нет».',
        caption: BASE_NOTE,
        data: { counts: ethicsCounts(scenes, entries) },
      };
    case 'utterance-counts':
      return {
        kind: 'utterance-counts',
        title: 'Типы реплик и визуальные тропы',
        subtitle: 'Частоты кодов в таблице кодирования.',
        caption: `${BASE_NOTE} Токены вне словаря в подсчёт не входят — они остаются в примечаниях карточек.`,
        data: { counts: utteranceCounts(scenes, entries), tropes: tropeCounts(scenes, entries) },
      };
    default:
      return null;
  }
}
