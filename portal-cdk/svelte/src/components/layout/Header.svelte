<script>
  import { base } from "$app/paths";
  import Spinner from "$components/utils/Spinner.svelte";
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
  <div class="this-is-a">
    This is a header: <i>{(user.data && user.data.username) || "username"}</i>
  </div>
</div>

<style>
  .this-is-a {
    font-size: 2rem;
    font-style: oblique;
  }

  .header {
    text-align: center;
    width: 100%;
    height: 100%;
    background-color: orange;
  }
</style>
