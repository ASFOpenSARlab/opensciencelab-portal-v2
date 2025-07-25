<script>
    import { Toast, ToastHeader, ToastBody } from '@sveltestrap/sveltestrap';

    let toastText = $state("");
    let toastType = $state("info");
    let toastDelay = $state("5000");
    let isToastOpen = $state(false);

    function giveAToast(event) {

        console.log("Give a toast: " + JSON.stringify(event.detail, null, 2))

        toastText = event.detail.text;
        toastType = event.detail.type;
        isToastOpen = true;

        const timeoutId = setTimeout(() => {isToastOpen = false}, toastDelay);
    }

</script>

<svelte:window on:giveAToast={giveAToast}/>

<main id="toast-container">
    <Toast isOpen={isToastOpen} autohide=true delay={toastDelay}>
        {#if toastType == "success"}
            <ToastHeader icon="success">
                Congrats!!
            </ToastHeader>
        {:else if toastType == "error"}
            <ToastHeader icon="danger">
                Oh no!!!
            </ToastHeader>
        {/if}
         <ToastBody>
            <p>
                { toastText }
            </p>
        </ToastBody>
    </Toast>
</main>

<style>
    #toast-container {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 10000;
    }
</style>
