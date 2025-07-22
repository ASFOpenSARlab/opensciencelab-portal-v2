<script>
    import { Button } from '@sveltestrap/sveltestrap';

    let { username } = $props()
    let userData = $state()

    console.log("prop 'username' selected: " + username)

    if (username) {
        const url = '/portal/users/get/'+username;

        fetch(url, {
            method: 'GET',
        })
        .then( response => response.json() )
        .then( data => { userData = data } )
        .catch( error => { console.log(error)} )
    }

    
    userData = {
        "last_cookie_assignment": "2025-07-14 23:11:13",
        "created_at": "2025-06-03 07:12:32",
        "last_update": "2025-07-14 23:11:13",
        "labs": [], 
        "profile": {
            "user_affliated_with_nasa_research_email": "", 
            "pi_affliated_with_nasa_research_email": "", 
            "research_member_affliated_with_university": false, 
            "country_of_residence": "US", 
            "user_affliated_with_isro_research_email": "", 
            "faculty_member_affliated_with_university": false, 
            "is_affliated_with_isro_research": "no", 
            "is_affiliated_with_us_gov_research": "no", 
            "user_affliated_with_gov_research_email": "", 
            "graduate_student_affliated_with_university": false, 
            "is_affiliated_with_nasa": "no", 
            "is_affliated_with_university": "no", 
            "user_or_pi_nasa_email": "default"
        }, 
        "access": ["user"], 
        "random_dict": null, 
        "email": "emlundell@alaska.edu", 
        "roles": ["user"], 
        "is_locked": false, 
        "some_int_without_default": null, 
        "username": "emlundell", 
        "some_int_with_default": "42", 
        "require_profile_update": false
    };
      
</script>

<main>
    <!--p style="border: 2px solid red;">=== User info: { JSON.stringify(userData, null, 2) }</p-->
    <div class="container">
        {#if userData }
            <div id="username-div">
                <p>Username: { username }</p>
            </div>
            <div id="createdTime-div">
                <p>Created: { userData.created_at }</p>
            </div>
            <div id="updatedTime-div">
                <p>Updated: { userData.last_update }</p>
            </div>
            <div id="email-div">
                <p>Email: { userData.email }</p>
            </div>
            <div id="access-div">
                <p>access: { userData.access }</p>
            </div>
            <div id="labs-div">
                <p>Labs: { userData.labs }</p>
            </div>
            <div id="profile-div">
                <p>Profile:</p>
                {#each Object.entries(userData.profile) as [key, value]}
                <p>{ key }: { value }</p>
                {/each}
            </div>
            <div id="actionBtns-div">
                <Button color="warning" disabled>Lock User</Button>
                <Button color="danger" disabled>Delete User</Button>
            </div>
        {:else}
            <div>
                <h1>No Info found for {username}</h1>
            </div>
        {/if}
    </div>
</main>

<style>
    .container {
        display: grid;
        text-align: left;
        row-gap: 10px;
        column-gap: 10px;
        grid-template-rows: auto auto auto auto auto auto minmax(10rem, 100%);
        grid-template-columns: auto auto auto;
        grid-template-areas:
            "username . actionBtns"
            "email . ."
            "createdTime updatedTime ."
            "ipAddr ipCountry ."
            "access . ."
            "labs . ."
            "profileEditBtn commentsEditBtn ."
            "profile profile profile" 
            "comments comments .";
    }

    #username-div {
        grid-area: username;
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

    #profile-div {
        border: 1px solid black;
        grid-area: profile;
        font-size: 10pt;
    }

    #actionBtns-div {
        grid-area: actionBtns;
    }
</style>