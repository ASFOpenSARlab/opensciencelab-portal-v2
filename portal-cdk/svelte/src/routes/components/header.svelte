<script>
  import { userInfo } from "$lib/store.svelte.js";
</script>

<div>
  <a href="/">Go to Portal Home</a>
  &emsp;&emsp;
  <h1>This is a header for <i>{userInfo.username}</i></h1>
</div>

<style>
  div {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
