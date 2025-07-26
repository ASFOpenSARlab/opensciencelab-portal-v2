<script>
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

<main>
    <div id="userinfoContainer">
        <div id="userinfo-id">
            <p>User Info</p>
        </div>

        <div id="email-id">
            <p>Email:</p>
            <p>{ userData.email }</p>
        </div>
        
        <div id="createdTime-id">
            <p>Created:</p>
            <p>{ userData.created_at }</p>
        </div>

        <div id="updatedTime-id">
            <p>Last Update:</p>
            <p>{ userData.last_update }</p>
        </div>

        <div id="access-id">
            <p>Access:</p>
            <p>{ userData.access }</p>
        </div>

        <div id="roles-id">
            <p>Roles:</p>
            <p>{ userData.roles }</p>
        </div>
    </div>
</main>

<style>
    #userinfoContainer {
        border: 1px solid grey;
        border-radius: 1rem;
        display: grid;
        row-gap: 10px;
        column-gap: 10px;
        grid-template-rows: auto auto auto auto auto auto;
        grid-template-columns: auto auto auto;
        grid-template-areas:
            "userinfo . ."
            "email . ."
            "createdTime updatedTime ."
            "ipAddr ipCountry ."
            "access roles"
            "comments comments .";
    }

    #createdTime-id {
        grid-area: createdTime;
        justify-self: left;
    }

    #updatedTime-id {
        grid-area: updatedTime;
        justify-self: left;
    }

    #email-id {
        grid-area: email;
        justify-self: left;
    }

    #access-id {
        grid-area: access;
        justify-self: left;
    }

    #roles-id {
        grid-area: roles;
        justify-self: left;
    }
</style>