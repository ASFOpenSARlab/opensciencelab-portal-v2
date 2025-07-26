<script>
    let { username, userData } = $props();
    
    import { Button } from '@sveltestrap/sveltestrap';

    function doUnlockUser() {
        userData.is_locked = false;
        console.log("TODO: Update DB here. Unlocking user " + username)
    }

    function doLockUser() {
        userData.is_locked = true;
        console.log("TODO: Update DB here. Locking user " + username)
    }
</script>

<div>
    <div>
        {#if userData.is_locked == true }
            <Button color="warning" onclick={doUnlockUser}>Unlock User</Button>
        {:else}
            <Button color="warning" onclick={doLockUser}>Lock User</Button>
        {/if}

        <Button color="danger" disabled>Delete User</Button>
    </div>
</div>

<style>
</style>