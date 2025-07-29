<script>
    import { Accordion, AccordionItem } from '@sveltestrap/sveltestrap';
    import UserLabsInfo from './UserLabsInfo.svelte';

    let { username, userData } = $props();

    let userLabs = [
        {
            labShortName: "smce-prod-opensarlab",
            labFriendlyName: "SMCE (Prod)",
            labUserProfiles: {
                "sar1": {
                    "status": "active",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar1-max": {
                    "status": "unused",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar2": {
                    "status": "blocked",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar2-max": {
                    "status": "default",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
            },
            comments: "This is for commenting on the provided profiles"
        },
        {
            labShortName: "smce-test-opensarlab",
            labFriendlyName: "SMCE (Test)",
            labUserProfiles: {
                "sar1": {
                    "status": "active",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar1-max": {
                    "status": "unused",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar2": {
                    "status": "blocked",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
                "sar2-max": {
                    "status": "default",
                    "activeDateStart": new Date('1900-01-01T00:00:00Z'),
                    "activeDateEnd": new Date('3000-01-01T00:00:00Z')
                },
            },
            comments: "This is for commenting on the provided profiles"
        }
    ]

    console.log("Labs Container username: ", $state.snapshot(username))
    console.log("Labs Container userData: ", $state.snapshot(userData))
    console.log("Labs Container userLabs: ", $state.snapshot(userLabs))

</script>

<div>
    <fieldset>
        <legend>Labs Assigned</legend>
        <div>
            {#if userLabs == undefined || userLabs == [] }
                <h3>No labs assigned</h3>
            {:else}
                {#each Object.entries(userLabs) as [key,lab]}
                <Accordion>
                    <AccordionItem header={ lab["labFriendlyName"] }>
                        <UserLabsInfo username={username} lab={lab} />
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
