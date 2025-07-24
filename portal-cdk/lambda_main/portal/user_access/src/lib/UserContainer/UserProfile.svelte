<script>
    let { username, userData } = $props();
</script>

<main>
    <div>
        <p>Profile:</p>

        {#each Object.entries(userData.profile) as [key, value]}
        <p>{ key }: { value }</p>
        {/each}
    </div>
</main>

<style>

</style>