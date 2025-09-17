<script>
  import { onMount } from "svelte";
  import favicon from "$lib/assets/favicon.svg";
  import { UserClass } from "$lib/store.svelte.js";

  let user = new UserClass();

  onMount(async () => {
    user.pull();
  });

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

{@render children?.()}
