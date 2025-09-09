<script>
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import Header from "$components/layout/header.svelte";
  import Footer from "$components/layout/footer.svelte";
  import favicon from "$lib/assets/favicon.svg";
  import { userInfo } from "$lib/store.svelte.js";
  import { Spinner } from "@sveltestrap/sveltestrap";

  let { children } = $props();

  onMount(async () => {
    const getUserInfo = async () => {
      const userInfoUrl = page.url.origin + "/portal/users/whoami";

      fetch(userInfoUrl, { method: "GET" })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error, status = ${response.status}`);
          }
          return response.json();
        })
        .then((jsonResponse) => {
          console.log("OnMount Get UsrInfo Json ", jsonResponse);
          userInfo.username = jsonResponse.username;
        })
        .catch((error) => {
          console.error(error);
          userInfo.username = "unknown";
        });
    };

    await getUserInfo();
  });
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<Header />

{#if userInfo.username == "unknown"}
  <Spinner type="border" size="" color="primary" />
{:else}
  {@render children?.()}
{/if}

<Footer />
