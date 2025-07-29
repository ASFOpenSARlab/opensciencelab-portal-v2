<script>
    import { Spinner } from '@sveltestrap/sveltestrap';
    import UserName from './UserContainer/UserName.svelte';
    import UserButtons from './UserContainer/UserButtons.svelte';
    import UserInfo from './UserContainer/UserInfo.svelte';
    import UserLabsContainer from './UserContainer/UserLabsContainer.svelte';
    import UserProfile from './UserContainer/UserProfile.svelte';
    
    let { username } = $props()
    let userData = $state()

    async function getUserData() {
        //const url = 'https://dq3yyi71b8t6w.cloudfront.net/portal/users/get/'+username;
        const url = '/portal/users/get/'+username;

        return await fetch(url, {
            method: 'GET',
        })
        .then( response => {
            console.log("Container response: ", response)    
            return response.json() 
        })
        .then( data => { 
            console.log("Container data: ", data)
            if (Object.keys(data).length === 0) {
                throw "No user data for " + username;
            }
            userData = data
        })
        .catch( error => { throw error })
    }
      
</script>

<div>
    {#await getUserData()}
        <Spinner type="border" size="" color="primary"/>
    {:then data}
        <div class="container">
            <div id="username-cell">
                <UserName username={ username } bind:userData={ userData }/>
            </div>
             <div id="userbuttons-cell">
                <UserButtons username={ username } bind:userData={ userData }/>
            </div>
            <div id="userinfo-cell">
                <UserInfo username={ username } bind:userData={ userData }/>
            </div>
            <div id="userprofile-cell">
                <UserProfile username={ username } bind:userData={ userData }/>
            </div>
            <div id="userlabs-cell">
                <UserLabsContainer username={ username } bind:userData={ userData }/>
            </div>
        </div>
    {:catch error}
        <div class="container"> 
            <h3 class="color-error">{error}</h3> 
        </div>
    {/await}
</div>

<style>
    .container {
        display: grid;
        grid-row-gap: 2rem;
        grid-template-columns: 70% 30%;
        grid-template-rows: 2rem auto auto auto;
        grid-template-areas:
            "UserName UserButtons"
            "UserInfo UserInfo"
            "UserLabs UserLabs"
            "UserProfile UserProfile";
            
    }

    .color-error {
        color: #df4a4a;
    }

    #username-cell {
        grid-area: UserName;
        justify-self: start;
    }

    #userbuttons-cell {
        grid-area: UserButtons;
        justify-self: end;
    }

    #userinfo-cell {
        grid-area: UserInfo;
        justify-self: auto;
    }

    #userprofile-cell {
        grid-area: UserProfile;
        justify-self: auto;
    }

    #userlabs-cell {
        grid-area: UserLabs;
        justify-self: auto;
    }

</style>

    <!--
    userData = {
        "last_cookie_assignment": "2025-07-14 23:11:13",
        "created_at": "2025-06-03 07:12:32",
        "last_update": "2025-07-14 23:11:13",
        "lab_access": {
            'azdwr-prod-opensarlab': {
                'lab_profiles': [
                    'AZDWR SAR 1',
                    'Debug Profile',
                    'AZDWR SAR 2',
                    'AZDWR SAR 3',
                    'AZDWR SAR 4',
                    'AZDWR SAR 5'
                ], 
                'lab_country_status': 'unrestricted',
                'can_user_access_lab': false,
                'can_user_see_lab_card': false
            }, 
            'smce-prod-opensarlab': {
                'lab_profiles': [
                    'm6a.xlarge', 
                    'm6a.large'
                ],
                'lab_country_status': 'unrestricted',
                'can_user_access_lab': false,
                'can_user_see_lab_card': true,
            }, 
            'ssbw': {
                'lab_profiles': [
                    'SSBW Workspace 1', 
                    'SSBW Workspace 2'
                ],
                'lab_country_status': 'unrestricted', 
                'can_user_access_lab': false,
                'can_user_see_lab_card': false,
            }, 
            'ssbw2': {
                'lab_profiles': [
                    'SSBW Workspace 1',
                    'SSBW Workspace 2'
                ], 
                'lab_country_status': 'unrestricted',
                'can_user_access_lab': true,
                'can_user_see_lab_card': true,
            }
        }, 
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
        "roles": ["user", "admin"], 
        "is_locked": true, 
        "some_int_without_default": null, 
        "username": "emlundell", 
        "some_int_with_default": "42", 
        "require_profile_update": false
    };
    -->