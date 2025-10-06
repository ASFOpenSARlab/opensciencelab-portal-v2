<script>
  const id = $props.id();
  let spinning = $state(true);

  export const start = () => {
    spinning = true;
  };

  export const stop = () => {
    spinning = false;
  };
</script>

{#if spinning}
  <div class="loading">
    <div class="spinner"></div>
  </div>
{/if}

<style>
  .loading {
    position: absolute;
    left: 50%;
    top: 50%;
  }

  .spinner {
    border: 4px solid #f3f3f3; /* Light grey */
    border-top: 4px solid #3498db; /* Blue */
    border-radius: 50%;
    width: 100px;
    height: 100px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
</style>
