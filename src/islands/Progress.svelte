<script lang="ts">
  import { onMount } from 'svelte';

  let width = $state(0);

  function update() {
    const doc = document.documentElement;
    const total = doc.scrollHeight - doc.clientHeight;
    width = total > 0 ? Math.min(100, (window.scrollY / total) * 100) : 0;
  }

  onMount(() => {
    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
    };
  });
</script>

<div class="progress" style:width="{width}%" aria-hidden="true"></div>
