<script>
    let { username, userData } = $props();
    
    import { Button } from '@sveltestrap/sveltestrap';

    function doUnlockUser() {
        userData.is_locked = false;
        console.log("Unlocking user " + username)
    }

    function doLockUser() {
        userData.is_locked = true;
        console.log("Locking user " + username)
    }
</script>

<main>
    <div>
        {#if userData.is_locked == true }
            <Button color="warning" on:click={doUnlockUser}>Unlock User</Button>
        {:else}
            <Button color="warning" on:click={doLockUser}>Lock User</Button>
        {/if}

        <Button color="danger" disabled>Delete User</Button>
    </div>
</main>

<style>
</style>