export interface Work {
  id: string;
  title: string;
  original_title: string;
  format: 'movie' | 'tv_series';
  year_start: number;
  year_end: number;
  country: string[];
  genres: string[];
  description: string;
}

export interface Scene {
  id: string;
  work_id: string;
  analysis_unit: 'scene' | 'work_overall';
  timecode: string;
  description: string;
  space_type: string | null;
  therapist_archetype: string[];
  ethical_violation: 'yes' | 'partial' | 'no' | null;
  stigma_level: 'high' | 'medium' | 'low' | null;
  utterance_types: string[];
  visual_tropes: string[];
  scene_function: string[];
  note: string;
}

export interface CodebookEntry {
  id: string;
  category: string;
  category_label: string;
  category_definition: string;
  value: string;
  label: string;
  definition: string;
  example: string;
}

export interface Envelope<T> {
  version: string;
  generated_at: string;
}

export interface WorksFile extends Envelope<never> {
  works: Work[];
}

export interface ScenesFile extends Envelope<never> {
  scenes: Scene[];
}

export interface CodebookFile extends Envelope<never> {
  entries: CodebookEntry[];
}

export interface MetaFile extends Envelope<never> {
  title: string;
  license: string;
}

export interface Chapter {
  slug: string;
  id: string;
  title: string;
  order: number;
  kind: 'prologue' | 'content' | 'epilogue';
  anchor: string;
  viz: string | null;
  scene_ids: string[];
  html: string;
}

export interface StoryStep {
  anchor: string;
  title: string;
  order: number;
  html: string;
  kind: 'chapter' | 'film';
  tag: 'prologue' | 'content' | 'epilogue' | 'film';
  kicker: string;
  workIds: string[];
  workId: string | null;
}
