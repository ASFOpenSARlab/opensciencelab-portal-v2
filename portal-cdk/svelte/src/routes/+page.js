export const load = async ({ fetch, url }) => {
  async function getMyUsername() {
    //const whoamiUrl = url.origin + "/portal/users/whoami";
    const whoamiUrl =
      "https://dq3yyi71b8t6w.cloudfront.net" + "/portal/users/whoami";
    console.log("****** ", whoamiUrl);

    const res = await fetch(whoamiUrl, {
      method: "GET",
    });
    console.log("****** ", res);

    username = await res.json();
    console.log("******", username);

    return "emlundell";
  }

  return {
    getMyUsername: await getMyUsername,
  };
};
