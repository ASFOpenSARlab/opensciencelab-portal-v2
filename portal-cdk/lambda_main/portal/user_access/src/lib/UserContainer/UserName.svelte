<script>
    let { username, userData } = $props();

    import { Button, Icon } from '@sveltestrap/sveltestrap';
    import { clickToCopy } from "../utils/clickToCopy.js"

    let text = $state('Hello');

</script>

<div>
    <div id="div-id">
        <div id="username-id" class="ellipsis"> 
            { username }
        </div>
        <div class="icons no-wrap">
            <span use:clickToCopy={'#username-id'} id="copy-span">
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
</div>

<style>
    #username-id {
        font-weight: bold;
        padding-left: 1rem;
        font-size: 2rem;
    }

    #copy-span {
        display: table-cell;
        padding-left: 1rem;
    }

    .ellipsis {
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
