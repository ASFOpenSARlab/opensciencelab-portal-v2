<script>
  import Toast from "$components/utils/Toast.svelte";
  import favicon from "$lib/assets/favicon.svg";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Toast />

{@render children?.()}
