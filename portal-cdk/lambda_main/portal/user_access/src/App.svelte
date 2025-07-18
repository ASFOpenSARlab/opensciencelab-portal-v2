<script>
  import { onMount } from 'svelte';
  import UserInfo from './lib/UserInfo.svelte'
  import { ScrollArea } from "bits-ui";
  import { Tabs } from "bits-ui";

  let usernames = $state();
  let selectedUsername = $state("username");

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
      <p>{selectedUsername}</p>
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
    border: 3px solid gray;
    display: grid;
    align-items: center;
    row-gap: 20px;
    column-gap: 50px;
    grid-template-columns: 400px 200px auto;
    grid-template-rows: 50px 50px minmax(10px, 100%);
    grid-template-areas: 
      "btn . ."
      "search username ."
      "scrolls tabs tabs";
  }

  #add-users-buttons-div {
    grid-area: btn;
  }

  #search-bar-div {
    grid-area: search;
  }

  #username-div {
    grid-area: username;
  }

  #username-div > p {
    margin: 0;
    text-align: left;
    font-size: 3rem;
  }

  #scrollarea-div {
    grid-area: scrolls;
    border: 3px solid gray;
    height: 100%;
  }

  #tabs-div {
    grid-area: tabs;
    border: 3px solid gray;
    height: 100%;
    width: 100%;
  }

</style>
