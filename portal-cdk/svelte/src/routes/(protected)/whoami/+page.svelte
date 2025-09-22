<script>
  import { onMount } from "svelte";
  import { resolveRoute } from "$app/paths";
  import Spinner from "$components/Spinner.svelte";
  import { UserClass } from "$lib/store.svelte.js";
  import { error } from "@sveltejs/kit";

  let spinner;
  let errorMsg = $state(null);
  let user = new UserClass();

  onMount(async () => {
    spinner.start();
    user.pull();
    spinner.stop();
  });

  let onBtnClick = () => {
    user.data.username = new Date();
    console.log("Onclick", $state.snapshot(user.data));
  };

  let onLatest = async () => {
    spinner.start();
    try {
      const results = await user.pull();
    } catch (error) {
      errorMsg = error.stack;
    } finally {
      spinner.stop();
    }
  };

  let onSave = async () => {
    spinner.start();
    try {
      await user.push();
    } catch (error) {
      errorMsg = error.stack;
    } finally {
      spinner.stop();
    }
  };
</script>

<Spinner bind:this={spinner} />

<h1>Future Home Page</h1>

{#if errorMsg}
  <p style="color:red">{errorMsg}</p>
{/if}

<p>{(user.data && user.data.username) || "no username given"}</p>

<button onclick={onBtnClick}>New</button>
<button onclick={onLatest}>Get Latest</button>
<button onclick={onSave}>Save</button>
