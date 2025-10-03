<script>
  import { Toasts } from "svoast";
  import favicon from "$lib/assets/favicon.svg";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Toasts position="top-right" />

{@render children?.()}
