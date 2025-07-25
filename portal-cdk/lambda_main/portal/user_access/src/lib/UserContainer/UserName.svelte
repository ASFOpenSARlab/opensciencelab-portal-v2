<script>
    let { username, userData } = $props();

    import { Button, Icon } from '@sveltestrap/sveltestrap';
    import { showToast } from '../utils/toast/toast.js'
    import { clickToCopy } from "../utils/clickToCopy.js"

    let text = $state('Hello');
	
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

<main>
    <div id="div-id">
        <div id="username-id" class="ellipsis"> 
            { username }
        </div>
        <div class="icons no-wrap">
            <span use:clickToCopy={'#username-id'}>
                <Icon name="copy"/>
            </span>

            {#if userData.is_locked == true }
            <Icon name="lock" />
            {/if}

            {#if userData.roles.includes('admin') }
            <Icon name="person-rolodex" />
            {/if}
        </div>
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
