<script>
  import Header from "./components/header.svelte";
  import Footer from "./components/footer.svelte";

  import favicon from "$lib/assets/favicon.svg";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Header />

{@render children?.()}

<Footer />
