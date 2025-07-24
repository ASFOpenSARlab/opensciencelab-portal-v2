<script>
    import { Toast, ToastHeader, ToastBody } from '@sveltestrap/sveltestrap';

    let toastText = $state("");
    let toastType = $state("");
    let isToastOpen = $state(true);

    function giveAToast(event) {
        toastText = event.detail.text;
        toastType = event.detail.type;
        isToastOpen = true;
    }

</script>

<svelte:window on:giveAToast={giveAToast}/>

<main id="toast-container">
    <Toast isOpen={isToastOpen} autohide=true delay=5000>
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
