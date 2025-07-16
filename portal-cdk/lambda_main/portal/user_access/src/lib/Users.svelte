<script>
    import { onMount } from 'svelte';

    async function getData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(error.message);
        }
    }

    let usernames = $state();
    let userData = $state(); // Reactive variable to store fetched data

    onMount(async () => {
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

        usernames = await getData('/portal/users/all/usernames')

        userData = await getData('/portal/users/all/users');
    });
</script>

<div>
    <h1>List of Usernames</h1>
    {#each usernames as username}
    <p>{ username }</p>
    {/each}
</div>

<div>
    <h1>User Info</h1>
    {#each userData as userData }
    <div>
        <h2>Username</h2> 
        <p>{ userData.username }</p>
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
    {/each }
</div>

<style>

</style>