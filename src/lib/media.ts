import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';

export interface MediaAssetRecord {
  id: string;
  kind: 'film_still' | 'photograph';
  status: 'candidate' | 'pending_review' | 'approved' | 'rejected';
  work_id?: string | null;
  scene_id?: string | null;
  source_file?: string | null;
  public_path?: string | null;
  source_url?: string | null;
  creator_or_rightsholder?: string | null;
  analysis_purpose?: string | null;
  alt?: string | null;
  caption?: string | null;
  attribution?: string | null;
  legal_basis?: string | null;
}

export type ApprovedMediaAsset = MediaAssetRecord & {
  status: 'approved';
  work_id: string;
  public_path: string;
  source_url: string;
  alt: string;
  caption: string;
  attribution: string;
};

interface MediaManifest {
  assets: MediaAssetRecord[];
}

function manifest(): MediaManifest {
  const raw = readFileSync(join(process.cwd(), 'data/media-assets.yml'), 'utf8');
  const parsed = parse(raw) as MediaManifest | null;
  return parsed ?? { assets: [] };
}

/** Keep a runtime guard in addition to the build-time validation gate. */
function isPublicReady(asset: MediaAssetRecord): asset is ApprovedMediaAsset {
  return asset.status === 'approved'
    && typeof asset.work_id === 'string' && asset.work_id.length > 0
    && typeof asset.public_path === 'string' && asset.public_path.startsWith('/media/')
    && typeof asset.source_url === 'string' && asset.source_url.startsWith('https://')
    && typeof asset.alt === 'string' && asset.alt.trim().length > 0
    && typeof asset.caption === 'string' && asset.caption.trim().length > 0
    && typeof asset.attribution === 'string' && asset.attribution.trim().length > 0;
}

/** Only individually reviewed, fully described assets can reach a public page. */
function approvedAssets(): ApprovedMediaAsset[] {
  return manifest().assets.filter(isPublicReady);
}

/** Work-level photos/stills belong on the work detail page, not duplicated on every scene. */
export function mediaForWork(workId: string): ApprovedMediaAsset[] {
  return approvedAssets().filter((asset) => asset.work_id === workId && !asset.scene_id);
}

/** Scene-specific frames are shown only on the matching analysis-unit page. */
export function mediaForScene(sceneId: string): ApprovedMediaAsset[] {
  return approvedAssets().filter((asset) => asset.scene_id === sceneId);
}
