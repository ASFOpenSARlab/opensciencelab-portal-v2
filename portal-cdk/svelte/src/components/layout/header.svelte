<script>
  import { base } from "$app/paths";
  import Spinner from "$components/Spinner.svelte";
  import { UserClass } from "$lib/store.svelte.js";
  import { onMount } from "svelte";

  let spinner;
  let user = new UserClass();

  onMount(async () => {
    user.pull();
    // spinner is already spinning on render
    spinner.stop();
  });
</script>

<Spinner bind:this={spinner} />

<div>
  <h1>
    This is a header: <i>{(user.data && user.data.username) || "username"}</i>
  </h1>
</div>

<style>
  div {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
