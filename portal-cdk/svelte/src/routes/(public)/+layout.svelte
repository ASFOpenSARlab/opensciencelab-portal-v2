<script>
  import Footer from "$components/layout/footer.svelte";

  /** @type {import('./$types').LayoutProps} */
  let { data, children } = $props();
</script>

{@render children()}

<Footer />
