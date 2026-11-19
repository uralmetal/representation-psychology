import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';

export interface MediaAsset {
  id: string;
  kind: 'film_still' | 'photograph';
  status: 'candidate' | 'pending_review' | 'approved' | 'rejected';
  work_id?: string | null;
  scene_id?: string | null;
  public_path: string;
  source_url: string;
  alt: string;
  caption: string;
  attribution: string;
}

interface MediaManifest {
  assets: MediaAsset[];
}

function manifest(): MediaManifest {
  const raw = readFileSync(join(process.cwd(), 'data/media-assets.yml'), 'utf8');
  const parsed = parse(raw) as MediaManifest | null;
  return parsed ?? { assets: [] };
}

/** Only individually reviewed assets can reach a public page. */
function approvedAssets(): MediaAsset[] {
  return manifest().assets.filter((asset) => asset.status === 'approved');
}

/** Work-level photos/stills belong on the work detail page, not duplicated on every scene. */
export function mediaForWork(workId: string): MediaAsset[] {
  return approvedAssets().filter((asset) => asset.work_id === workId && !asset.scene_id);
}

/** Scene-specific frames are shown only on the matching analysis-unit page. */
export function mediaForScene(sceneId: string): MediaAsset[] {
  return approvedAssets().filter((asset) => asset.scene_id === sceneId);
}
