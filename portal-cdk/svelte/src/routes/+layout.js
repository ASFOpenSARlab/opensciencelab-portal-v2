export const prerender = false;

export const load = async ({ fetch, url }) => {
  const getUserInfo = async () => {
    const userInfoUrl = url.origin + "/portal/users/whoami";
    const res = await fetch(userInfoUrl, {
      method: "GET",
    });
    console.log(res);
    if (res.ok === "ok") {
      return await res.json();
    } else {
      return { username: "unknown" };
    }
  };

  return {
    userInfo: await getUserInfo(),
  };
};
