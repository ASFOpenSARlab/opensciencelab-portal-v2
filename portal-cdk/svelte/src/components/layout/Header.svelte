<script>
  import { base } from "$app/paths";
  import Spinner from "$components/Spinner.svelte";
  import { UserClass } from "$lib/store.svelte.js";
  import { onMount } from "svelte";

  let spinner;
  let user = new UserClass();

  onMount(async () => {
    spinner.start();
    user.pull();
    spinner.stop();
  });
</script>

<Spinner bind:this={spinner} />

<div class="header">
  <h2>
    This is a header: <i>{(user.data && user.data.username) || "username"}</i>
  </h2>
</div>

<style>
  .header {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
