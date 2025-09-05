// userInfo statefully holds the info like username of the user
// The actual values of userInfo are determined within layout.svelte on page mount
// Being reactive, any changes in one place will be reflective where ever userInfo is imported and used
const userInfoDefault = {
  username: "friend",
};

export let userInfo = $state(userInfoDefault);
