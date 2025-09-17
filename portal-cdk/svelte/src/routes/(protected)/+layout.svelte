<script>
  //import { onMount } from "svelte";
  import Header from "$components/layout/header.svelte";
  import Footer from "$components/layout/footer.svelte";
  import favicon from "$lib/assets/favicon.svg";
  //import { UserClass } from "$lib/store.svelte.js";

  //onMount(async () => {
  //  let user = new UserClass();
  //
  //  await user.latest();
  //});

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Header />

{@render children?.()}

<Footer />
