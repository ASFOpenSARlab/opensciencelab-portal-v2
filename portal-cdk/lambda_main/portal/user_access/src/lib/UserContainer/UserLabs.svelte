<script>
    let { username, userData } = $props();

    console.log("Labs userData: ", $state.snapshot(userData))

    import { Accordion, AccordionItem } from '@sveltestrap/sveltestrap';
</script>

<div>
    <fieldset>
        <legend>Labs Assigned</legend>
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
