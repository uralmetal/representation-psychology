import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

export default defineConfig({
  site: 'https://uralmetal.github.io',
  base: '/representation-psychology',
  trailingSlash: 'always',
  output: 'static',
  integrations: [svelte()],
});
