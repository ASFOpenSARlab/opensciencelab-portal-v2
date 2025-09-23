<script>
  import Header from "$components/layout/Header.svelte";
  import Footer from "$components/layout/Footer.svelte";

  let { children } = $props();
</script>

<div class="container">
  <header>
    <Header />
  </header>

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
      "header header header"
      "lside content rside"
      "footer footer footer";

    grid-template-columns: 10px 1fr 10px;
    grid-template-rows: 4rem 1fr 4rem;
    grid-gap: 10px;

    height: 100vh;
  }

  header {
    grid-area: header;
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
