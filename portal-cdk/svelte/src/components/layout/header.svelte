<script>
  import { base } from "$app/paths";
  import { UserClass } from "$lib/store.svelte.js";
  import { onMount } from "svelte";

  let user = new UserClass();

  onMount(async () => {
    user.pull();
  });
</script>

<div>
  <h1>This is a header for <i>{user.data}</i></h1>
</div>

<style>
  div {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
