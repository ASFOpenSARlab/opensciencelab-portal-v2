<script>
  import { username } from "$lib/utils";
  import { page } from "$app/state";

  let domain = page.url.host;
  let usernames = $state([]);

  async function getUsernames() {
    const url = domain + "/portal/users/all/usernames";

    await fetch(url, {
      method: "GET",
    })
      .then((response) => {
        console.log("Response: ", response);
        return response.json();
      })
      .then((data) => {
        console.log("Data: ", data);
        if (Object.keys(data).length === 0) {
          throw "No data";
        }
        usernames = data;
      })
      .catch((error) => {
        throw error;
      });
  }
</script>

<div>
  <h1>Welcome {username}</h1>

  <p>Here's a list of all usernames:</p>

  <div class="container">
    {#await getUsernames()}
      <!--Spinner type="border" size="" color="primary" /-->
      Loading...
    {:then data}
      {#each Object.entries(usernames) as [key, username]}
        <p>{username}</p>
      {/each}
    {:catch error}
      <h3 class="color-error">{error}</h3>
    {/await}
  </div>
</div>
