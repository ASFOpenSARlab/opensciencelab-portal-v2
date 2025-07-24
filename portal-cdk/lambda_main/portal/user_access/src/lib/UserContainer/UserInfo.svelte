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
            <span>Email:</span>
            <span>{ userData.email }</span>
        </div>
        
        <div id="created-id">
            <span>Created:</span>
            <span>{ userData.created_at }</span>
        </div>

        <div id="created-id">
            <span>Last Update:</span>
            <span>{ userData.last_update }</span>
        </div>

        <div id="created-id">
            <span>Access:</span>
            <span>{ userData.access }</span>
        </div>

        <div id="created-id">
            <span>Roles:</span>
            <span>{ userData.roles }</span>
        </div>
    </div>
</main>

<style>
    #userinfoContainer {
        border: 1px solid grey;
        border-radius: 1rem;
        display: grid;
        text-align: left;
        row-gap: 10px;
        column-gap: 10px;
        grid-template-rows: auto auto auto auto auto auto minmax(10rem, 100%);
        grid-template-columns: auto auto auto;
        grid-template-areas:
            "userinfo"
            "email . ."
            "createdTime updatedTime ."
            "ipAddr ipCountry ."
            "access roles"
            "comments comments .";
    }



    #createdTime-div {
        grid-area: createdTime;
    }

    #updatedTime-div {
        grid-area: updatedTime;
    }

    #email-div {
        grid-area: email;
    }

    #access-div {
        grid-area: access;
    }

    #labs-div {
        grid-area: labs;
    }
</style>