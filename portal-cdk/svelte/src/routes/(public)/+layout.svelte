<script>
  import Footer from "$components/layout/Footer.svelte";

  /** @type {import('./$types').LayoutProps} */
  let { data, children } = $props();
</script>

<div class="container">
  <lside></lside>

  <main>
    {@render children?.()}
  </main>

  <rside></rside>

  <footer>
    <Footer />
  </footer>
</div>

<style>
  .container {
    display: grid;

    grid-template-areas:
      "lside content rside"
      "footer footer footer";

    grid-template-columns: 10px 1fr 10px;
    grid-template-rows: 1fr 4rem;
    grid-gap: 10px;

    height: 100vh;
  }

  lside {
    grid-area: lside;
    margin-left: 0.5rem;
  }

  main {
    grid-area: content;
  }

  rside {
    grid-area: rside;
    margin-right: 0.5rem;
  }

  footer {
    grid-area: footer;
  }
</style>
