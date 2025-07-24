<script>
    let { username, userData } = $props();

    import { Button, Icon, Toast, ToastHeader, ToastBody } from '@sveltestrap/sveltestrap';
    import { clickToCopy } from "../utils/clickToCopy.js"

    let text = '';
	
	function copySuccess(){
		text = "Success!"
	}
	
	function copyError(event){
		text = `Error! ${event.detail}`
	}

</script>

<svelte:window on:copysuccess={copySuccess} on:copyerror={copyError}/>

<main>
    <div id="div-id">
        <div class="ellipsis"> 
            { username }
        </div>

        <div class="icons no-wrap">
            <Icon name="copy" />

            {#if userData.is_locked == true }
            <Icon name="lock" />
            {/if}

            {#if userData.roles.includes('admin') }
            <Icon name="person-rolodex" />
            {/if}
        </div>

    </div>

    <div>
        <Toast isOpen=false>
            <ToastHeader>
                <Icon slot="icon" name="emoji-smile-fill" />
                Congrats!!
            </ToastHeader>
            <ToastBody>
                <p>
                    Username <i>{ username }</i> copied to clipboard.
                </p>
            </ToastBody>
        </Toast>
    </div>
</main>

<style>
    .ellipsis {
        font-size: 2rem;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
        max-width: 500px;
        display: inline-block;
    }

    .icons {
        font-size: 2rem;
        margin-left: 0rem;
    }

    .no-wrap {
        display: inline-block;
    }

</style>
