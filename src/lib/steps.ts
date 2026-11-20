import { getChapters } from './chapters';
import { scenesFile, worksFile } from './data';
import { strings } from './i18n';
import type { CodebookEntry, Scene, StoryStep } from './types';

export interface MergedScene {
  space: string | null;
  archetypes: string[];
  ethics: 'yes' | 'partial' | 'no' | null;
  stigma: 'high' | 'medium' | 'low' | null;
  utterances: string[];
  tropes: string[];
  notes: string[];
}

export function mergeWorkScenes(scenes: Scene[]): MergedScene {
  const uniq = (vals: string[]) => [...new Set(vals)];
  const first = <T>(vals: (T | null)[]): T | null => vals.find((v) => v != null) ?? null;
  return {
    space: first(scenes.map((s) => s.space_type)),
    archetypes: uniq(scenes.flatMap((s) => s.therapist_archetype)),
    ethics: first(scenes.map((s) => s.ethical_violation)),
    stigma: first(scenes.map((s) => s.stigma_level)),
    utterances: uniq(scenes.flatMap((s) => s.utterance_types)),
    tropes: uniq(scenes.flatMap((s) => s.visual_tropes)),
    notes: scenes.map((s) => s.note).filter((n): n is string => Boolean(n)),
  };
}

export function codeLabel(
  entries: CodebookEntry[],
  category: string,
  value: string | null | undefined,
): { label: string; id: string | null } {
  if (!value) return { label: '', id: null };
  const e = entries.find((x) => x.category === category && x.value === value);
  return e ? { label: e.label, id: e.id } : { label: value, id: null };
}

export function buildSteps(): StoryStep[] {
  const chapters = getChapters().sort((a, b) => a.order - b.order);
  const works = worksFile().works;
  const scenes = scenesFile().scenes;
  const sceneById = new Map(scenes.map((s) => [s.id, s]));

  const chapterSteps: StoryStep[] = chapters.map((c, i) => ({
    anchor: c.anchor,
    title: c.title,
    order: i,
    html: c.html,
    kind: 'chapter',
    tag: c.kind,
    kicker: `${strings.story.chapterKicker} ${i + 1} ${strings.story.of} ${chapters.length}`,
    workIds: [
      ...new Set(
        c.scene_ids
          .map((id) => sceneById.get(id)?.work_id)
          .filter((id): id is string => Boolean(id)),
      ),
    ],
    workId: null,
  }));

  const filmSteps: StoryStep[] = works.map((w, j) => ({
    anchor: w.id,
    title: w.title,
    order: 0,
    html: '',
    kind: 'film',
    tag: 'film',
    kicker: `${strings.story.filmKicker} ${j + 1} ${strings.story.of} ${works.length}`,
    workIds: [w.id],
    workId: w.id,
  }));

  const epiIndex = chapterSteps.findIndex((s) => s.tag === 'epilogue');
  const out = [...chapterSteps];
  out.splice(epiIndex === -1 ? out.length : epiIndex, 0, ...filmSteps);
  return out.map((s, i) => ({ ...s, order: i }));
}
