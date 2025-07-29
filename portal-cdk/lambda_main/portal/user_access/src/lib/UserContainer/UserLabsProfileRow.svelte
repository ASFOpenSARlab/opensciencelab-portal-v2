<script>
    import { Icon, Input } from '@sveltestrap/sveltestrap';

    let { profileShortName, profile } = $props();
</script>

<div id="container">

    <div id="activeCheckbox">
        <Input id="activeCheckboxInput" disabled={profile.status == 'default'} type="checkbox" checked={profile.status == 'active'}/>
    </div>

    <div id="blockedCheckbox">
        <Input id="blockedCheckboxInput" type="checkbox" checked={profile.status == 'blocked'}/>
    </div>

    <div id="profileName">
        <span class='color-{profile.status}'>{ profileShortName }</span>
    </div>

    <div id="datesUntilStartDiv">
        <Input id="datesUntilInputStart" type="datetime-local" placeholder="local start time" value={profile.activeDateStart}/>
    </div>

    <div id="datesUntilArrow">
        <Icon name="arrow-right" />
    </div>

    <div id="datesUntilEndDiv">
        <Input id="datesUntilInputEnd" type="datetime-local" placeholder="local end time" value={profile.activeDateEnd}/>
    </div>
</div>

<style>
    #container {
        background-color: lightgrey;
        display: grid;
        grid-template-rows: auto;
        grid-template-columns: auto auto auto auto auto auto;
        grid-template-areas: 
            "activeCheckbox blockedCheckbox profileName datesUntilStartDiv datesUntilArrow datesUntilEndDiv";
    }

    .color-blocked {
        color: red;
        text-decoration: line-through;
    }

    .color-active {
        color: green;
    }

    .color-default {
        color: forestgreen;
    }

    #activeCheckbox {
        grid-area: activeCheckbox;
        justify-self: center;
    }

    #blockedCheckbox {
        grid-area: blockedCheckbox;
        justify-self: center;
    }

    #profileName {
        grid-area: profileName;
        justify-self: center;
    }

    #datesUntilStartDiv {
        grid-area: datesUntilStartDiv;
        width: 11rem;
        justify-self: center;
    }

    #datesUntilArrow {
        grid-area: datesUntilArrow;
        justify-self: center;
    }

    #datesUntilEndDiv {
        grid-area: datesUntilEndDiv;
        width: 11rem;
        justify-self: center;
    }

</style>