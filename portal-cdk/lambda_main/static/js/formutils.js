
// Remove option with value === "default" if it is not selected
function removeDropdownDefault(selectElement){
    if (selectElement.value !== "default") {
        const defaultOption = selectElement.querySelector('option[value="default"]');
        if (defaultOption) {
            selectElement.remove(defaultOption.index);
        }
    }
}

function validateDateRange(startInput, endInput, errorDisplay){
    if (startInput.value && endInput.value && new Date(endInput.value) <= new Date(startInput.value)) {
        errorDisplay.textContent = 'End date must be after start date.';
        endInput.setCustomValidity('End date must be after start date.');
    } else {
        errorDisplay.textContent = '';
        endInput.setCustomValidity('');
    }
}