<script>
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

    /*
    [{
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
    }]
    */   
</script>

<div>
    <p>=== User info: { JSON.stringify(userData, null, 2) }</p>

    {#if userData }
        <div>
            <h2>Username</h2> 
            <p>{ username }</p>
        </div>
        <div>
            <h2>Email</h2>
            <p>{ userData.email }</p>
        </div>
        <div>
            <h2>Profile</h2>
            {#each Object.entries(userData.profile) as [key, value]}
            <p>{ key }: { value }</p>
            {/each}
        </div>
    {:else}
        <p>No Info found for {username}</p>
    {/if}
</div>

<style>

</style>