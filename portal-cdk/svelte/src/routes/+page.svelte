<script>
  import { page } from "$app/state";

  import { userInfo } from "$lib/store.js";
  const username = $userInfo.username;
  console.log("page.svelete/userInfo ", username);

  let origin = page.url.origin;
  let usernames = $state([]);

  async function getUsernames() {
    const url = origin + "/portal/users/all/usernames";

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
