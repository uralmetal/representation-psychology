import { getChapters } from './chapters';
import { codebookFile, scenesFile, worksFile } from './data';
import { strings } from './i18n';
import type { CodebookEntry, Scene, StoryStep, Work } from './types';

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

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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

export function filmChapterHtml(
  work: Work,
  scenes: Scene[],
  entries: CodebookEntry[],
  base: string,
): string {
  const m = mergeWorkScenes(scenes);
  const code = (cat: string, val: string | null | undefined): string => {
    if (!val) return '<span class="muted">нет кода</span>';
    const { label, id } = codeLabel(entries, cat, val);
    return id ? `<a href="${base}codebook/#${id}">${esc(label)}</a>` : esc(label);
  };
  const codeList = (cat: string, vals: string[]): string => {
    if (!vals.length) return '<span class="muted">—</span>';
    return vals.map((v) => code(cat, v)).join(', ');
  };

  const fmt = work.format === 'tv_series' ? 'сериал' : 'фильм';
  const yrs = work.year_start === work.year_end ? String(work.year_start) : `${work.year_start}–${work.year_end}`;
  const sceneLink = scenes[0]
    ? ` · <a href="${base}scene/${scenes[0].id}/">Единица анализа →</a>`
    : '';

  return [
    `<p class="film-meta"><strong>Формат:</strong> ${fmt} · <strong>Годы:</strong> ${yrs} · <strong>Страны:</strong> ${esc(work.country.join(', '))} · <strong>Жанры:</strong> ${esc(work.genres.join(', '))}</p>`,
    `<p>${esc(work.description)}</p>`,
    '<ul class="film-codes">',
    `<li><strong>Пространство сессии:</strong> ${code('space_type', m.space)}</li>`,
    `<li><strong>Архетип терапевта:</strong> ${codeList('therapist_archetype', m.archetypes)}</li>`,
    `<li><strong>Этическое нарушение:</strong> ${code('ethical_violation', m.ethics)}</li>`,
    `<li><strong>Уровень стигмы:</strong> ${code('stigma_level', m.stigma)}</li>`,
    `<li><strong>Типы реплик:</strong> ${codeList('utterance_type', m.utterances)}</li>`,
    `<li><strong>Визуальные тропы:</strong> ${codeList('visual_trope', m.tropes)}</li>`,
    '</ul>',
    m.notes.length ? `<p class="film-note muted small">Примечание: ${esc(m.notes.join(' '))}</p>` : '',
    `<p class="film-link"><a href="${base}work/${work.id}/">Страница произведения →</a>${sceneLink}</p>`,
  ].join('\n');
}

export function buildSteps(): StoryStep[] {
  const base = import.meta.env.BASE_URL;
  const chapters = getChapters().sort((a, b) => a.order - b.order);
  const works = worksFile().works;
  const scenes = scenesFile().scenes;
  const entries = codebookFile().entries;
  const sceneById = new Map(scenes.map((s) => [s.id, s]));
  const scenesByWork = new Map<string, Scene[]>();
  for (const s of scenes) {
    const list = scenesByWork.get(s.work_id) ?? [];
    list.push(s);
    scenesByWork.set(s.work_id, list);
  }

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
    html: filmChapterHtml(w, scenesByWork.get(w.id) ?? [], entries, base),
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
