// From https://svelte.dev/playground/667d8ac94e2349f3a1b7b8c5fa4c0082?version=5.36.14

export function clickToCopy(node, target) {
  async function copyText() {
    let text = target
      ? document.querySelector(target).innerText
      : node.innerText;

    try {
      await navigator.clipboard.writeText(text);

      node.dispatchEvent(
        new CustomEvent("copysuccess", {
          bubbles: true,
        })
      );
    } catch (error) {
      node.dispatchEvent(
        new CustomEvent("copyerror", {
          bubbles: true,
          detail: error,
        })
      );
    }
  }

  node.addEventListener("click", copyText);

  return {
    destroy() {
      node.removeEventListener("click", copyText);
    },
  };
}
