import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { CodebookFile, MetaFile, ScenesFile, WorksFile } from './types';

const DATA_DIR = join(process.cwd(), 'public/data');

function load<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, name), 'utf8')) as T;
}

export const worksFile = () => load<WorksFile>('works.json');
export const scenesFile = () => load<ScenesFile>('scenes.json');
export const codebookFile = () => load<CodebookFile>('codebook.json');
export const metaFile = () => load<MetaFile>('meta.json');
