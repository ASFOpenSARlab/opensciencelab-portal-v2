<script>
  import Footer from "$components/layout/Footer.svelte";

  /** @type {import('./$types').LayoutProps} */
  let { data, children } = $props();
</script>

<div class="app-container">
  <main>
    {@render children?.()}
  </main>

  <Footer />
</div>

<style>
  .app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh; /* Ensures the container always takes at least the full viewport height. 100vh adds scrollbars for some reason. */
    margin: 0;
  }

  main {
    flex-grow: 1;
  }
</style>
