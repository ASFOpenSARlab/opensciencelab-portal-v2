export const giveAToast = (type, text) => {
  window.dispatchEvent(
    new CustomEvent("giveAToast", {
      bubbles: true,
      detail: {
        type: type,
        text: text,
      },
    })
  );
};
