<script>
  import favicon from "$lib/assets/favicon.svg";
  import Spinner from "$components/Spinner.svelte";
  import { onMount } from "svelte";

  let spinner;

  onMount(() => {
    // spinner is already spinning on render
    spinner.stop();
  });

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Spinner bind:this={spinner} />

{@render children?.()}
