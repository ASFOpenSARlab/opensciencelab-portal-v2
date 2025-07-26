<script>
    let { username, userData } = $props();

    console.log("Labs userData: ", $state.snapshot(userData))

    import { Accordion, AccordionItem } from '@sveltestrap/sveltestrap';
</script>

<main>
    <div>
        {#if userData.lab_access == undefined || userData.lab_access == [] }
            <h3>No labs assigned</h3>
        {:else}
            {#each Object.entries(userData.lab_access) as [key,value]}
            <Accordion>
                <AccordionItem header={ value }>
                    { key }: { value }
                </AccordionItem>
            </Accordion>
            {/each}
        {/if}
    </div>
</main>

<style>

</style>
