// Args: payload = dict("type": "success", "text": "A toast!")
export function showToast(payload) {
  console.log(
    "Dispatching 'giveaToast' for payload " + JSON.stringify(payload, null, 2)
  );
  document.dispatchEvent(
    new CustomEvent("giveAToast", {
      bubbles: true,
      detail: {
        type: payload.type,
        text: payload.text,
      },
    })
  );
}
