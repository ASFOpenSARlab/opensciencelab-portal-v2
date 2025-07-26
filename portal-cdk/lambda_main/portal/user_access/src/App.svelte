<svelte:head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
</svelte:head>

<script>
  import { onMount } from 'svelte';
  import UserContainer from './lib/UserContainer.svelte'
  import ToastContainer from './lib/utils/toast/Toast.svelte'
  import { showToast } from './lib/utils/toast/toast.js'
  import { Button, Icon, Input, ListGroup, ListGroupItem, Spinner } from '@sveltestrap/sveltestrap';

  let usernames = $state([]);
  let searchTerm = $state("");
  let filteredUsernames = $derived(usernames.filter(username => username.indexOf(searchTerm) !== -1));
  let selectedUsername = $state("");

  function getUsernames() {
    //const url = '/portal/users/all/usernames'
    const url = 'https://dq3yyi71b8t6w.cloudfront.net/portal/users/all/usernames'

    fetch(url, {
          method: 'GET',
      })
      .then( response => response.json() )
      .then( data => { 
        usernames = data;
        usernames.push("sm}psmnpmnpsml{mms{ppmpnm{plmsmpps{pllp{p{npsmpp"); 
        console.log("Fetch response and usernames: ", data, $state.snapshot(usernames)); 
      } )
      .catch( error => { console.log(error)} )
  }

  onMount(async () => {
      getUsernames();
  });

  // Copy handlers
  function copySuccess(event){
        showToast({
            "type": "success",
            "text": "Copied text: " + event.detail
        })
	}
	
	function copyError(event){
        showToast({
            "type": "success",
            "text": "Error! " + event.detail
        })
	}
</script>

<svelte:window on:copysuccess={copySuccess} on:copyerror={copyError}/>

<div>
  <ToastContainer/>
</div>

<div class="container">
  <div id="add-users-buttons-div">
    <Button color="primary" disabled>+ Add Users</Button>
    <Button color="primary" disabled>+ Bulk Add Users</Button>
  </div>

  <div id="search-bar-div">
    <Input type="search" placeholder="search usernames" bind:value={searchTerm}/>
  </div>

  <div id="scrollarea-div">
    <!--{#key filteredUsernames}-->
      {#if filteredUsernames == [] || filteredUsernames == '' }
        <div id="filtered-username-id">
          <Spinner type="border" size="" color="primary"/>
        </div>
      {:else}
        <ListGroup>
          {#each filteredUsernames as username (username)}
            <ListGroupItem onclick={() => selectedUsername = username}> 
              <p class="scrollarea-p" id="scrollarea-p-{ username }"> 
                <span> { username } </span>
              </p>
            </ListGroupItem>
          {/each}
        </ListGroup>
      {/if}
    <!--{/key}-->
  </div>

  <div id="usercontainer-div">
    <!--{#key selectedUsername}-->
      {#if selectedUsername }
        <UserContainer username={ selectedUsername } />
      {:else}
        <h3>Please select username</h3>
      {/if}
    <!--{/key}-->
  </div>

</div>


<style>
  .container {
    display: grid;
    align-items: center;
    row-gap: 1rem;
    column-gap: 1rem;
    grid-template-columns: 300px auto;
    grid-template-rows: 2rem 2rem minmax(20rem, 100%) auto;
    grid-template-areas: 
      "btns toastcontainer"
      "search usercontainer"
      "scrolls usercontainer"
      ". usercontainer";
  }

  #add-users-buttons-div {
    grid-area: btns;
    text-align: left;
    margin-top: 0rem;
  }

  #search-bar-div {
    grid-area: search;
    margin-top: 1rem;
  }

  #scrollarea-div {
    grid-area: scrolls;
    border: 1px solid gray;
    height: 100%;
    border-radius: 1rem;
    margin-top: 1rem;
  }

  #scrollarea-div .scrollarea-p {
    text-overflow: ellipsis;
    overflow: hidden;
    text-align: left;
  }

  #scrollarea-div #filtered-username-id {
    padding-top: 2rem;
  }

  #usercontainer-div {
    grid-area: usercontainer;
    height: 100%;
    width: 100%;
  }

</style>
