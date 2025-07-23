<svelte:head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
</svelte:head>

<script>
  import { onMount } from 'svelte';
  import UserInfo from './lib/UserInfo.svelte'
  import { Button, Icon, Input, ListGroup, ListGroupItem, Spinner } from '@sveltestrap/sveltestrap';

  // sm}psmnpmnpsml{mms{ppmpnm{plmsmpps{pllp{p{npsmpp
  let usernames = $state();
  let searchTerm = $state("");
  let filteredUsernames = $derived(usernames.filter(username => username.indexOf(searchTerm) !== -1));
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
  <div class="container">
    <div id="add-users-buttons-div">
      <Button color="primary" disabled>+ Add Users</Button>
      <Button color="primary" disabled>+ Bulk Add Users</Button>
    </div>

    <div id="search-bar-div">
      <Input type="search" placeholder="search username"  bind:value={searchTerm}/>
    </div>

    <div id="scrollarea-div">
      <ListGroup>
        {#each filteredUsernames as username}
          <ListGroupItem onclick={() => selectedUsername = username}> 
            <p class="scrollarea-p" id="scrollarea-p-{ username }"> 
              <span> { username } </span>
            </p>
          </ListGroupItem>
        {/each}
      </ListGroup>
    </div>

    <div id="tabs-div">
      {#if selectedUsername }
        {#key selectedUsername}
          <UserInfo username={ selectedUsername } />
        {/key}
      {:else}
        <p>Please select username</p>
        <Spinner type="border" size="" color="primary"/>
      {/if}
    </div>
  </div>
</main>

<style>
  .container {
    /*border: 3px solid gray;*/
    display: grid;
    align-items: center;
    row-gap: 20px;
    column-gap: 50px;
    grid-template-columns: 300px 80% auto;
    grid-template-rows: 50px 50px minmax(50rem, 100%);
    grid-template-areas: 
      "btn . ."
      "search username ."
      "scrolls tabs tabs";
  }

  #add-users-buttons-div {
    grid-area: btn;
    text-align: left;
  }

  #search-bar-div {
    grid-area: search;
  }

  #username-div {
    grid-area: username;
  }

  #scrollarea-div {
    grid-area: scrolls;
    border: 1px solid gray;
    height: 100%;
  }

  .scrollarea-p {
    text-overflow: ellipsis;
    overflow: hidden;
    text-align: left;
  }

  #tabs-div {
    grid-area: tabs;
    height: 100%;
    width: 100%;
  }

</style>
