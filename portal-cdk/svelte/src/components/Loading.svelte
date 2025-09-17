<script>
  let showSpinner = $state(false);

  export const start = () => {
    showSpinner = true;
  };

  export const stop = () => {
    showSpinner = false;
  };

  const wait = (elapse) => {
    setTimeout(() => {
      return true;
    }, elapse);
  };
</script>

{#if showSpinner && wait(10)}
  <div class="loading">Loading....</div>
{/if}

<style>
  .loading {
    position: absolute;
    left: 50%;
    top: 50%;
  }
</style>
