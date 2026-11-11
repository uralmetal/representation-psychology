import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import MarkdownIt from 'markdown-it';
import { parse } from 'yaml';
import type { Chapter } from './types';

const CHAPTERS_DIR = join(process.cwd(), 'src/content/chapters');
const base = import.meta.env.BASE_URL;

const md = new MarkdownIt({ html: false, linkify: false });

function sceneHref(id: string): string {
  return `${base}scene/${id}/`;
}

export function getChapters(): Chapter[] {
  const files = readdirSync(CHAPTERS_DIR)
    .filter((name) => name.endsWith('.md'))
    .sort();

  return files.map((name) => {
    const raw = readFileSync(join(CHAPTERS_DIR, name), 'utf8');
    const match = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!match) throw new Error(`${name}: нет frontmatter`);
    const meta = parse(match[1]) as Record<string, unknown>;
    let body = match[2];

    body = body.replace(/\]\(scene:([a-z0-9-]+)\)/g, (_, id) => `](${sceneHref(id)})`);
    body = body.replace(/\]\(page:([a-z0-9/-]+)\)/g, (_, p) => `](${base}${p}/)`);
    let html = md.render(body);
    html = html.replace(
      /href="([^"]*\/scene\/([a-z0-9-]+)\/)"/g,
      'href="$1" data-scene="$2"',
    );

    return {
      slug: name.replace(/\.md$/, ''),
      id: String(meta.anchor ?? meta.id ?? ''),
      title: String(meta.title ?? ''),
      order: Number(meta.order ?? 0),
      kind: (meta.kind as Chapter['kind']) ?? 'content',
      anchor: String(meta.anchor ?? meta.id ?? ''),
      viz: meta.viz ? String(meta.viz) : null,
      scene_ids: Array.isArray(meta.scene_ids) ? meta.scene_ids.map(String) : [],
      html,
    };
  });
}
