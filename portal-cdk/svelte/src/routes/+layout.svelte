<script>
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import Header from "./components/header.svelte";
  import Footer from "./components/footer.svelte";
  import favicon from "$lib/assets/favicon.svg";
  import { userInfo } from "$lib/store.svelte.js";

  let { children } = $props();

  onMount(async () => {
    const getUserInfo = async () => {
      const userInfoUrl = page.url.origin + "/portal/users/whoami";
      //const userInfoUrl =
      //  "https://dq3yyi71b8t6w.cloudfront.net/portal/users/whoami";

      fetch(userInfoUrl, { method: "GET" })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error, status = ${response.status}`);
          }
          return response.json();
        })
        .then((jsonResponse) => {
          console.log("OnMount Get UsrInfo Json ", jsonResponse);
          return jsonResponse;
        })
        .catch((error) => {
          console.error(error);
          return { username: "unknown" };
        });
    };

    let updatedUserInfo = await getUserInfo();
    userInfo.username = updatedUserInfo.username;
  });
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

Hello, {userInfo.username}
<Header />

{@render children?.()}

<Footer />
