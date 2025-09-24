<script>
  let isToastOpen = $state(false);
  let toastText = $state("Message here");
  let toastType = $state("Message Type");
  let toastDelay = $state(3000); //ms

  const giveAToast = (event) => {
    toastText = event.detail.text;
    toastType = event.detail.type;
    isToastOpen = true;

    const timeoutId = setTimeout(() => {
      isToastOpen = false;
    }, toastDelay);
  };
</script>

<svelte:window on:giveAToast={giveAToast} />

{#if isToastOpen}
  <div class="centered-div styled">
    <p><b>Type</b>: {toastType}</p>
    <p><b>Text</b>: {toastText}</p>
  </div>
{/if}

<style>
  .centered-div {
    width: 500px; /* Or any desired width */
    margin: 0 auto; /* Centers horizontally */
    position: absolute; /* Positions relative to the nearest positioned ancestor */
    top: 5%; /* Aligns to the top */
    left: 50%; /* Starts at the horizontal center */
    transform: translateX(-50%); /* Adjusts for the div's own width */
  }

  .styled {
    background-color: aliceblue;
    border: 2px solid black;
    padding: 1rem;
  }
</style>
