<script>
  import { getContext } from "svelte";

  let myUsername = getContext("myUsername");
</script>

<div>
  <h1>This is a header for <i>{myUsername}</i></h1>
</div>

<style>
  div {
    text-align: center;
    width: 100%;
    height: 3rem;
    background-color: orange;
  }
</style>
