<script>
  import { onMount } from 'svelte';
  import UserInfo from './lib/UserInfo.svelte'
  import { ScrollArea } from "bits-ui";
  import { Tabs } from "bits-ui";

  let usernames = $state();
  let selectedUsername = $state("emlundell");

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
      <div>
        <button>+ Add Users</button>
        <button>+ Bulk Add Users</button>
      </div>
    </div>

    <div id="search-bar-div">
      <input type="search" id="site-search" name="q" />
      <button>Search Users</button>
    </div>

    <div id="scrollarea-div">
      <ScrollArea.Root>
        <ScrollArea.Viewport>
          {#each usernames as username}
          <button onclick={() => selectedUsername = username}> { username } </button>
          {/each}
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar orientation="vertical">
          <ScrollArea.Thumb/>
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </div>

    <div id="username-div">
      <h1>{selectedUsername}</h1>
    </div>

    <div id="tabs-div">
      {#if selectedUsername }
        <Tabs.Root value="userinfo">
          <Tabs.List>
            <Tabs.Trigger value="userinfo">
              User Info
            </Tabs.Trigger>
            <Tabs.Trigger value="labinfo">
              Assigned Labs
            </Tabs.Trigger>
          </Tabs.List>
          <Tabs.Content value="userinfo">
            {#key selectedUsername}
              <UserInfo username={ selectedUsername }/>
            {/key}
          </Tabs.Content>
          <Tabs.Content value="labinfo">
            <p>Under construction</p>
          </Tabs.Content>
        </Tabs.Root>
      {:else}
        <p>Please select username</p>
      {/if}
    </div>
  </div>
</main>

<style>
  .container {
    display: grid;
    grid-template-columns: 400px 400px 1000px;
    grid-template-rows: 50px 50px 1000px;
    grid-template-areas: 
      "btn . ."
      "search username ."
      "scrolls tabs tabs";
  }

  #add-users-buttons-div {
    grid-area: btn;
    justify-items: left;
  }

  #search-bar-div {
    grid-area: search;
    justify-items: left;
  }

  #username-div {
    grid-area: username;
  }

  #scrollarea-div {
    grid-area: scrolls;
    border: 3px solid brown;
  }

  #tabs-div {
    grid-area: tabs;
    border: 3px solid brown;
  }

</style>
