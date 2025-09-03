<script>
  import { page } from "$app/state";
  import { getContext } from "svelte";

  const myUsername = getContext("myUsername");

  console.log("page.svelete/myUsename ", myUsername);

  //let origin = page.url.origin;
  let origin = "https://dq3yyi71b8t6w.cloudfront.net";
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
  <h1>Welcome {myUsername}</h1>

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
