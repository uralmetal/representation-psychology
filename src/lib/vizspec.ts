import { archetypeCounts, ethicsCounts, spaceMatrix, stigmaCounts, tropeCounts, utteranceCounts, vizPoints } from './viz';
import type { CodebookEntry, Scene, Work } from './types';

export interface VizSpec {
  kind: string;
  title: string;
  subtitle: string;
  caption: string;
  data: Record<string, unknown>;
}

const BASE_NOTE = 'Полный учтённый набор прототипа (9 единиц анализа), а не выборка кинематографа.';

interface UnitGroup {
  label: string;
  scenes: Scene[];
}

// Агрегированные диаграммы никогда не смешивают scene и work_overall:
// каждая панель считается по своему типу единицы анализа со своим знаменателем.
function unitGroups(scenes: Scene[]): { label: string; units: number; scenes: Scene[] }[] {
  return [
    { label: 'Сцены', scenes: scenes.filter((s) => s.analysis_unit === 'scene') },
    { label: 'Произведения целиком', scenes: scenes.filter((s) => s.analysis_unit === 'work_overall') },
  ]
    .filter((g) => g.scenes.length > 0)
    .map((g) => ({ label: g.label, units: g.scenes.length, scenes: g.scenes }));
}

function matrixData(scenes: Scene[], entries: CodebookEntry[]) {
  const m = spaceMatrix(scenes, entries);
  return {
    rows: m.archetypes.map((a) => ({ id: a.id, label: a.label })),
    cols: m.spaces.map((s) => ({ id: s.id, label: s.label })),
    cells: m.cells.map((c) => ({ row: c.archetype, col: c.space, count: c.count })),
  };
}

export function vizSpec(id: string, works: Work[], scenes: Scene[], entries: CodebookEntry[]): VizSpec | null {
  const points = vizPoints(works, scenes, entries);
  const groups = unitGroups(scenes);
  switch (id) {
    case 'corpus-timeline':
      return {
        kind: 'corpus-timeline',
        title: 'Корпус прототипа по годам',
        subtitle: 'Сцены и произведения, закодированные целиком, показаны раздельными панелями. Ось Y — уровень стигмы.',
        caption: `${BASE_NOTE} Ось — годы выхода произведений, не линия тренда.`,
        data: { points },
      };
    case 'stigma-timeline':
      return {
        kind: 'stigma-timeline',
        title: 'Стигма по годам',
        subtitle: 'Сцены и произведения, закодированные целиком, показаны раздельными панелями.',
        caption: `${BASE_NOTE} Ось — годы выхода произведений, не линия тренда.`,
        data: { points },
      };
    case 'archetype-counts':
      return {
        kind: 'archetype-counts',
        title: 'Архетипы профессиональных персонажей',
        subtitle: 'Число единиц анализа на каждый архетип — функцию персонажа в сюжете.',
        caption: `${BASE_NOTE} «Опасный метод» посчитан один раз — как «Романтизированный учёный».`,
        data: {
          groups: groups.map((g) => ({
            label: g.label,
            units: g.units,
            counts: archetypeCounts(g.scenes, entries),
          })),
        },
      };
    case 'space-matrix':
      return {
        kind: 'space-matrix',
        title: 'Архетип × пространство',
        subtitle: 'Число единиц анализа в каждой ячейке матрицы, отдельно для каждого типа единицы.',
        caption: `${BASE_NOTE} «Веб-терапия» без кода пространства отражена в столбце «Нет кода».`,
        data: {
          groups: groups.map((g) => ({
            label: g.label,
            units: g.units,
            matrix: matrixData(g.scenes, entries),
          })),
        },
      };
    case 'ethics-counts':
      return {
        kind: 'ethics-counts',
        title: 'Этическое нарушение',
        subtitle: 'Распределение единиц по кодам «Да / Частично / Нет», отдельно для каждого типа единицы.',
        caption: BASE_NOTE,
        data: {
          groups: groups.map((g) => ({
            label: g.label,
            units: g.units,
            counts: ethicsCounts(g.scenes, entries),
          })),
        },
      };
    case 'stigma-counts':
      return {
        kind: 'stigma-counts',
        title: 'Уровень стигмы',
        subtitle: 'Распределение единиц анализа по уровням стигмы репрезентации профессии, отдельно для каждого типа единицы.',
        caption: `${BASE_NOTE} Стигма относится к изображению профессии на экране, а не к пациентам.`,
        data: {
          groups: groups.map((g) => ({
            label: g.label,
            units: g.units,
            counts: stigmaCounts(g.scenes, entries),
          })),
        },
      };
    case 'utterance-counts':
      return {
        kind: 'utterance-counts',
        title: 'Типы реплик и визуальные тропы',
        subtitle: 'Частоты кодов в таблице кодирования, отдельно для каждого типа единицы.',
        caption: `${BASE_NOTE} Токены вне словаря в подсчёт не входят — они остаются в примечаниях карточек.`,
        data: {
          groups: groups.map((g) => ({
            label: g.label,
            units: g.units,
            counts: utteranceCounts(g.scenes, entries),
            tropes: tropeCounts(g.scenes, entries),
          })),
        },
      };
    default:
      return null;
  }
}
