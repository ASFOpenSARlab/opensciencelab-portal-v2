<script>
  import Header from "$components/layout/Header.svelte";
  import Footer from "$components/layout/Footer.svelte";

  let { children } = $props();
</script>

<div class="app-container">
  <Header />

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
