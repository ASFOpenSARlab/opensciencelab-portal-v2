<script>
  import { page } from "$app/state";
  import { Spinner } from "@sveltestrap/sveltestrap";
  import { userInfo } from "$lib/store.svelte.js";

  let origin = page.url.origin;
  let usernames = $state([]);

  async function getUsernames() {
    const url = origin + "/portal/users/all/usernames";

    await fetch(url, {
      method: "GET",
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        if (Object.keys(data).length === 0) {
          throw "No data";
        }
        usernames = data;
      })
      .catch((error) => {
        throw error;
      });
  }

  let myUsername = userInfo.username;
</script>

<div>
  {#if !userInfo.username}
    <h1>Welcome, Friend</h1>
  {:else}
    <h1>Welcome, {userInfo.username}</h1>
  {/if}

  <p>Here's a list of all usernames:</p>

  <div class="container">
    {#await getUsernames()}
      <Spinner type="border" size="" color="primary" />
    {:then data}
      {#each Object.entries(usernames) as [key, username]}
        <p>{username}</p>
      {/each}
    {:catch error}
      <h3 class="color-error">{error}</h3>
    {/await}
  </div>
</div>
