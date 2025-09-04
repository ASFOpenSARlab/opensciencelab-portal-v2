<script>
  import { userInfo } from "$lib/store.js";
</script>

<div>
  <h1>This is a header for <i>{$userInfo.username}</i></h1>
</div>

<style>
  div {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
