<script>
  import { onMount } from 'svelte';
  import UserInfo from './lib/UserInfo.svelte'

  let usernames = $state();
  let selectedUsername = $state();

  onMount(async () => {
      const url = '/portal/users/all/usernames'
      fetch(url, {
              method: 'GET',
          })
          .then( response => response.json() )
          .then( data => { usernames = data } )
          .catch( error => { console.log(error)} )
  });
</script>

<main>
  <div class="card">
    <h1>List of Usernames</h1>
    {#each usernames as username}
    <button onclick={() => selectedUsername = username}> { username } </button>
    {/each}

    <p> Selected username: { selectedUsername } </p>
  </div>

  <div class="card">
    {#if selectedUsername }
      {#key selectedUsername}
        <UserInfo username={ selectedUsername }/>
      {/key}
    {:else}
      <p>Please select username</p>
    {/if}
  </div>

</main>

<style>
</style>
