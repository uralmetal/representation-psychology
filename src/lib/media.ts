import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';

export interface MediaAssetRecord {
  id: string;
  kind: 'film_still' | 'photograph';
  status: 'candidate' | 'pending_review' | 'approved' | 'published_by_request' | 'rejected';
  work_id?: string | null;
  scene_id?: string | null;
  source_file?: string | null;
  public_path?: string | null;
  image_url?: string | null;
  source_url?: string | null;
  source_date?: string | null;
  source_notes?: string | null;
  creator_or_rightsholder?: string | null;
  license?: string | null;
  license_url?: string | null;
  rights_notes?: string | null;
  analysis_unit?: 'scene' | 'work_overall' | null;
  screen_time_verified?: boolean;
  proposed_scene_id?: string | null;
  analysis_purpose?: string | null;
  /** Narrative chapter where this approved asset supports a specific analytical thesis. */
  chapter_anchor?: string | null;
  alt?: string | null;
  caption?: string | null;
  attribution?: string | null;
  legal_basis?: string | null;
  legal_review?: {
    status: 'not_reviewed' | 'approved' | 'rejected';
    reference?: string | null;
    reviewer?: string | null;
    reviewed_at?: string | null;
  } | null;
}

export type PublicMediaAsset = MediaAssetRecord & {
  status: 'approved' | 'published_by_request';
  work_id: string;
  image_url: string;
  alt: string;
  caption: string;
  analysis_purpose: string;
};

interface MediaManifest {
  assets: MediaAssetRecord[];
}

function manifest(): MediaManifest {
  const raw = readFileSync(join(process.cwd(), 'data/media-assets.yml'), 'utf8');
  const parsed = parse(raw) as MediaManifest | null;
  return parsed ?? { assets: [] };
}

/** Owner-requested publication is distinct from independent rights approval. */
function isPublicReady(asset: MediaAssetRecord): asset is PublicMediaAsset {
  const hasPublicImage = typeof asset.image_url === 'string'
    && asset.image_url.startsWith('https://');
  const hasEditorialText = typeof asset.alt === 'string' && asset.alt.trim().length > 0
    && typeof asset.caption === 'string' && asset.caption.trim().length > 0
    && typeof asset.analysis_purpose === 'string' && asset.analysis_purpose.trim().length > 0;
  const hasWork = typeof asset.work_id === 'string' && asset.work_id.length > 0;

  if (asset.status === 'published_by_request') {
    return hasPublicImage && hasEditorialText && hasWork;
  }

  return asset.status === 'approved'
    && hasPublicImage && hasEditorialText && hasWork
    && typeof asset.attribution === 'string' && asset.attribution.trim().length > 0
    && typeof asset.legal_basis === 'string' && asset.legal_basis.trim().length > 0
    && asset.legal_review?.status === 'approved'
    && typeof asset.legal_review.reference === 'string' && asset.legal_review.reference.trim().length > 0
    && typeof asset.legal_review.reviewer === 'string' && asset.legal_review.reviewer.trim().length > 0
    && typeof asset.legal_review.reviewed_at === 'string' && asset.legal_review.reviewed_at.trim().length > 0;
}

/** Publicly rendered assets are either independently approved or explicitly published at the owner's request. */
function publicAssets(): PublicMediaAsset[] {
  return manifest().assets.filter(isPublicReady);
}

/** Work-level photos/stills belong on the work detail page, not duplicated on every scene. */
export function mediaForWork(workId: string): PublicMediaAsset[] {
  return publicAssets().filter((asset) => asset.work_id === workId && !asset.scene_id && !asset.chapter_anchor);
}

/** Scene-specific frames are shown only on the matching analysis-unit page. */
export function mediaForScene(sceneId: string): PublicMediaAsset[] {
  return publicAssets().filter((asset) => asset.scene_id === sceneId && !asset.chapter_anchor);
}

/** Only assets explicitly attached to a chapter appear in the narrative; never infer placements. */
export function mediaForChapter(chapterAnchor: string): PublicMediaAsset[] {
  return publicAssets().filter((asset) => asset.chapter_anchor === chapterAnchor && !asset.scene_id);
}
