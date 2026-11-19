import type { CodebookEntry, Scene } from './types';

export interface CatDef {
  /** ключ кодбука: space_type, therapist_archetype, ... */
  cat: string;
  /** поле сцены: space_type, therapist_archetype, ethical_violation, stigma_level, utterance_types, visual_tropes */
  field: 'space_type' | 'therapist_archetype' | 'ethical_violation' | 'stigma_level' | 'utterance_types' | 'visual_tropes';
  /** короткая подпись слоя (для вкладок) */
  tab: string;
}

export const CAT_DEFS: Record<string, CatDef> = {
  space_type: { cat: 'space_type', field: 'space_type', tab: 'Пространство' },
  therapist_archetype: { cat: 'therapist_archetype', field: 'therapist_archetype', tab: 'Архетип' },
  ethical_violation: { cat: 'ethical_violation', field: 'ethical_violation', tab: 'Этика' },
  stigma_level: { cat: 'stigma_level', field: 'stigma_level', tab: 'Стигма' },
  utterance_type: { cat: 'utterance_type', field: 'utterance_types', tab: 'Типы реплик' },
  visual_trope: { cat: 'visual_trope', field: 'visual_tropes', tab: 'Визуальные тропы' },
};

export function sceneValues(scene: Scene, def: CatDef): string[] {
  const v = scene[def.field] as string | string[] | null;
  if (Array.isArray(v)) return v;
  return v ? [v] : [];
}

export function entryOf(entries: CodebookEntry[], cat: string, value: string): CodebookEntry | undefined {
  return entries.find((e) => e.category === cat && e.value === value);
}

export function labelOf(entries: CodebookEntry[], cat: string, value: string): string {
  return entryOf(entries, cat, value)?.label ?? value;
}

export function entriesOfCategory(entries: CodebookEntry[], cat: string): CodebookEntry[] {
  return entries.filter((e) => e.category === cat);
}
