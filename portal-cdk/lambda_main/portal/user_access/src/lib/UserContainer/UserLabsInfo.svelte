<script>
    import UserLabsProfileRow from './UserLabsProfileRow.svelte'

    let {username, lab} = $props();
</script>

<div class="container">

    <div id="labShortName">
        <b>{lab['labFriendlyName']} -- <i>{lab['labShortName']}</i> </b>
    </div>

    <!-- User lab profiles -->
    <div id="labUserProfiles">
        {#each Object.entries(lab['labUserProfiles']) as [profileShortName,profile] (profileShortName)}
            <UserLabsProfileRow profileShortName={profileShortName} profile={profile} />
        {/each}
    </div>

    <textarea id="labComments">
        {lab['comments']}
    </textarea>

</div>

<style>

    .container {
        display: grid;
        grid-row-gap: 2rem;
        grid-template-columns: auto auto;
        grid-template-rows: auto auto auto;
        grid-template-areas:
            "labshortName ."
            "labUserProfiles labUserProfiles "
            "labComments labComments";
    }

    #labShortName {
        grid-area: labshortName;
        justify-self: start;
    }

    #labUserProfiles {
        grid-area: labUserProfiles;
        justify-self: auto;
    }

    #labComments {
        grid-area: labComments;
        justify-self: auto;
        min-height: 5rem;
    }

</style>