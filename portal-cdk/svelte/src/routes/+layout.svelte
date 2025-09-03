<script>
  import { page } from "$app/state";
  import { setContext } from "svelte";

  import Header from "./components/header.svelte";
  import Footer from "./components/footer.svelte";
  import favicon from "$lib/assets/favicon.svg";

  let { children } = $props();

  let getMyUsername = page.data.getMyUsername;
  let myUsername = getMyUsername();

  console.log(">>>>>*** ", myUsername);

  setContext("myUsername", myUsername);
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Header />

{@render children?.()}

<Footer />
