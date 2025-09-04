<script>
  import Header from "./components/header.svelte";
  import Footer from "./components/footer.svelte";
  import favicon from "$lib/assets/favicon.svg";

  import { userInfo } from "$lib/store.js";

  //let { children } = $props();
  let { children, data } = $props();
  userInfo.set(data.userInfo);
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Header />

{@render children?.()}

<Footer />
