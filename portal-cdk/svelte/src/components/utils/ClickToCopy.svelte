<script>
  import { giveAToast } from "$lib/utils/giveAToast";
  import { onMount } from "svelte";

  /** @type {import('./$types').PageProps} */
  let { target } = $props();
  let mySpan;

  // From https://svelte.dev/playground/667d8ac94e2349f3a1b7b8c5fa4c0082?version=5.36.14
  async function copyText() {
    let text = target
      ? document.querySelector(target).innerText
      : this.innerText;

    try {
      await navigator.clipboard.writeText(text);

      this.dispatchEvent(
        new CustomEvent("copysuccess", {
          bubbles: true,
          detail: {
            message: text,
          },
        })
      );

      giveAToast("success", "Copied text: " + text);

      console.log(`Text '${text}' has been written to the clipboard`);
    } catch (error) {
      this.dispatchEvent(
        new CustomEvent("copyerror", {
          bubbles: true,
          detail: {
            message: error,
          },
        })
      );

      giveAToast("error", "Error! " + text);

      console.log(`Text '${text}' has had a copy error: ${error}`);
    }
  }

  onMount(() => {
    mySpan.addEventListener("click", copyText);

    return {
      destroy() {
        mySpan.removeEventListener("click", copyText);
      },
    };
  });
</script>

<!--Copy Content Icon from Google. This is intended to be temp until a proper icon set is decided. Then that icon set should be installed globally to make importing much faster.-->
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&icon_names=content_copy"
/>

<span class="material-symbols-outlined point-cursor roomy" bind:this={mySpan}>
  content_copy
</span>

<style>
  .roomy {
    margin-left: 3px;
    margin-right: 3px;
  }
  .point-cursor {
    cursor: pointer;
  }
</style>
