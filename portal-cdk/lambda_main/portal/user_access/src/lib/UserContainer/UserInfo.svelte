<script>
    import { Icon } from '@sveltestrap/sveltestrap';
    import { clickToCopy } from "../utils/clickToCopy.js"

    let { username, userData } = $props();

    import {
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardSubtitle,
        CardText,
        CardTitle
    } from '@sveltestrap/sveltestrap';
</script>



<div>
    <fieldset>
        <legend>User Info</legend>
        <div id="container">

            {#snippet item(name, label, value, htmlType)}
                <div id="{name}-id" class="container-cell">
                    <div class="userdata-label">
                        {label}
                    <!--    <span use:clickToCopy={name}-userdata-value" id="copy-span">
                            <Icon name="copy"/>
                        </span> -->
                    </div>
                    <div id="{name}-userdata-value" class="userdata-value">
                        {#if htmlType == "textarea"}
                            <textarea>{ value }</textarea>
                        {:else}
                            <span>{ value }</span>
                        {/if}
                    </div>
                </div>
            {/snippet}

            {@render item("email", "Email", userData.email)}
            {@render item("createdTime", "Created", userData.created_at)}
            {@render item("updatedTime", "Last Updated", userData.last_update)}
            {@render item("ipAddress", "IP Address", userData.ip_address)}
            {@render item("ipCountry", "IP Country", userData.ip_country)}
            {@render item("roles", "Roles", userData.roles)}
            {@render item("access", "Access", userData.access)}
            {@render item("comments", "Comments", userData.comments, "textarea")}

        </div>
    </fieldset>
</div>

<style>

    #copy-span {
        display: table-cell;
        padding-left: 1rem;
    }

    fieldset {
        padding: 2rem;
        border: 1px solid grey;
        border-radius: 1rem;
    }

    fieldset legend {
        border-bottom: 1px solid black;
        text-align: left;
    }

    #container {
        margin: 1rem;
        padding-top: 1rem;
        display: grid;
        row-gap: 2rem;
        column-gap: 10px;
        grid-template-rows: repeat(5, minmax(4rem, auto));
        grid-template-columns: auto auto;
        grid-template-areas:
            "email ."
            "createdTime updatedTime"
            "ipAddr ipCountry"
            "access roles"
            "comments comments";
    }

    .container-cell {
        text-align: start;
        width: 100%;
        height: 100%;

    }

    .container-cell > div {
        padding: 0.2rem;
    }

    .userdata-label {
        color: grey;
    }

    .userdata-value {
        color: inherit;
    }

    #createdTime-id {
        grid-area: createdTime;
    }

    #updatedTime-id {
        grid-area: updatedTime;
    }

    #ipAddress-id {
        grid-area: ipAddr;
    }

    #ipCountry-id {
        grid-area: ipCountry;
    }

    #email-id {
        grid-area: email;
    }

    #access-id {
        grid-area: access;
    }

    #roles-id {
        grid-area: roles;
    }

    #comments-id {
        grid-area: comments;
    }

    #comments-id textarea {
        width: 100%;
        height: 10rem;
        border-radius: 0.5rem;
        background-color: #f8f8f8;
    }
</style>