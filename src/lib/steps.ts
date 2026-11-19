import { getChapters } from './chapters';
import { scenesFile } from './data';
import { strings } from './i18n';
import type { StoryStep } from './types';

export function buildSteps(): StoryStep[] {
  const chapters = getChapters().sort((a, b) => a.order - b.order);
  const scenes = scenesFile().scenes;
  const sceneById = new Map(scenes.map((s) => [s.id, s]));

  return chapters.map((c, i) => ({
    anchor: c.anchor,
    title: c.title,
    order: i,
    num: i + 1,
    html: c.html,
    kind: 'chapter',
    tag: c.kind,
    kicker: `${strings.story.chapterKicker} ${i + 1} ${strings.story.of} ${chapters.length}`,
    viz: c.viz,
    sceneIds: c.scene_ids,
    workIds: [
      ...new Set(
        c.scene_ids
          .map((id) => sceneById.get(id)?.work_id)
          .filter((id): id is string => Boolean(id)),
      ),
    ],
  }));
}
