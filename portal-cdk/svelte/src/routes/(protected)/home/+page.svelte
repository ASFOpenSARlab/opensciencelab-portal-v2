<script>
  import { onMount } from "svelte";
  import { resolveRoute } from "$app/paths";
  import Loading from "$components/Loading.svelte";
  import { UserClass } from "$lib/store.svelte.js";
  import { error } from "@sveltejs/kit";

  let spinner;
  let errorMsg = $state(null);
  let user = new UserClass();

  onMount(async () => {
    user.pull();
  });

  let onBtnClick = () => {
    user.data.username = new Date();
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

<h1>Future Home Page</h1>

{#if errorMsg}
  <p style="color:red">{errorMsg}</p>
{/if}

<Loading bind:this={spinner} />

<p>{user.data}</p>

<button onclick={onBtnClick}>New</button>
<button onclick={onLatest}>Get Latest</button>
<button onclick={onSave}>Save</button>
