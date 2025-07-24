<script>
    let { username, userData } = $props();

    import { Accordion, AccordionItem } from '@sveltestrap/sveltestrap';
</script>

<main>
    <div>
        {#each Object.entries(userData.lab_access) as [key,value]}
        <Accordion>
            <AccordionItem header={ value }>
                { key }: { value }
            </AccordionItem>
        </Accordion>
        {/each}
    </div>
</main>

<style>

</style>
