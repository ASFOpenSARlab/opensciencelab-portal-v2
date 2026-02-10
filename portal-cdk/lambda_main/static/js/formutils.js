
// Remove option with value === "default" if it is not selected
function removeDropdownDefault(selectElement){
    if (selectElement.value !== "default") {
        const defaultOption = selectElement.querySelector('option[value="default"]');
        if (defaultOption) {
            selectElement.remove(defaultOption.index);
        }
    }
}