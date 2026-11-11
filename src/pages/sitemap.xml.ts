import type { APIRoute } from 'astro';
import { scenesFile, worksFile } from '../lib/data';

export const GET: APIRoute = ({ site }) => {
  const base = import.meta.env.BASE_URL;
  const origin = (site?.origin ?? 'https://uralmetal.github.io').replace(/\/$/, '');
  const paths = [
    '',
    'infographics/',
    'codebook/',
    'method/',
    ...worksFile().works.map((w) => `work/${w.id}/`),
    ...scenesFile().scenes.map((s) => `scene/${s.id}/`),
  ];
  const urls = paths
    .map((p) => `  <url><loc>${origin}${base}${p}</loc></url>`)
    .join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
