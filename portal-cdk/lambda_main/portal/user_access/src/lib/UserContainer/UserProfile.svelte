<script>
    let { username, userData } = $props();
</script>

<div>
    <fieldset>
        <legend>User Profiles</legend>

        {#each Object.entries(userData.profile) as [key, value]}
        <p>{ key }: { value }</p>
        {/each}
    </fieldset>
</div>

<style>
    fieldset {
        padding: 2rem;
        border: 1px solid grey;
        border-radius: 1rem;
    }

    fieldset legend {
        border-bottom: 1px solid black;
        text-align: left;
    }
</style>