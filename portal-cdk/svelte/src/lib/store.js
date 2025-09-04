import { writable } from "svelte/store";

const userInfoDefault = {
  username: "friend",
};

export let userInfo = writable(userInfoDefault);
