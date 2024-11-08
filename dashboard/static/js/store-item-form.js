document.addEventListener('DOMContentLoaded', function() {
    initializeFileInputs();
    initializeFormManagement();
    bindEventListeners();
    updateAllFormIndexes();
});

// File input handling
function initializeFileInputs() {
    const fileInput = document.querySelector('#id_item_photo');
    const fileNameSpan = document.querySelector('.file-name');
    
    if (fileInput && fileNameSpan) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            fileNameSpan.textContent = fileName;
        });
    }
}

// Form management initialization
function initializeFormManagement() {
    updateManagementForms();
    initializeExistingForms();
}

function initializeExistingForms() {
    const variationForms = document.querySelectorAll('.variation-form');
    variationForms.forEach((form, index) => {
        // Set proper indexes
        form.dataset.index = index;
        
        // Initialize delete buttons
        initializeDeleteButtons(form);
        
        // Initialize choice forms within this variation
        initializeChoiceForms(form);
    });
}

function initializeDeleteButtons(form) {
    // Variation delete button
    const deleteBtn = form.querySelector('.remove-variation');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            handleVariationDelete(form);
        });
    }
    
    // Choice delete buttons
    const choiceDeleteBtns = form.querySelectorAll('.remove-choice');
    choiceDeleteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            handleChoiceDelete(e.target.closest('.choice-row'));
        });
    });
}

function initializeChoiceForms(variationForm) {
    const choicesContainer = variationForm.querySelector('.choices-container');
    if (choicesContainer) {
        const addChoiceBtn = choicesContainer.querySelector('.add-choice-link');
        if (addChoiceBtn) {
            addChoiceBtn.addEventListener('click', function(e) {
                e.preventDefault();
                addNewChoice(variationForm);
            });
        }
    }
}

// Event listeners
function bindEventListeners() {
    // Add variation button
    const addVariationBtn = document.getElementById('add-variation');
    if (addVariationBtn) {
        addVariationBtn.addEventListener('click', addNewVariation);
    }
    
    // Form submission
    const form = document.getElementById('edit-store-item-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validateForm()) {
                this.submit();
            }
        });
    }
}

// Add new variation
async function addNewVariation(e) {
    e.preventDefault();
    const container = document.getElementById('variation-container');
    if (!container) return;

    const variationCount = container.querySelectorAll('.variation-form').length;
    
    try {
        const response = await fetch(`/dashboard/add-variation-with-choices/?form_index=${variationCount}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const html = await response.text();
        container.insertAdjacentHTML('beforeend', html);
        
        // Initialize the new variation form
        const newForm = container.lastElementChild;
        newForm.dataset.index = variationCount;
        initializeDeleteButtons(newForm);
        initializeChoiceForms(newForm);
        
        updateAllFormIndexes();
    } catch (error) {
        console.error('Error adding variation:', error);
    }
}

// Add new choice to variation
async function addNewChoice(variationForm) {
    const choicesContainer = variationForm.querySelector('.choices-container');
    if (!choicesContainer) return;

    const variationIndex = variationForm.dataset.index;
    const choiceCount = choicesContainer.querySelectorAll('.choice-row').length;
    
    try {
        const response = await fetch(`/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${choiceCount}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const html = await response.text();
        
        // Remove add button from current last row
        const currentLastRow = choicesContainer.querySelector('.choice-row:last-child .add-choice-link');
        if (currentLastRow) {
            currentLastRow.remove();
        }
        
        choicesContainer.insertAdjacentHTML('beforeend', html);
        
        // Initialize delete button for new choice
        const newRow = choicesContainer.lastElementChild;
        const deleteBtn = newRow.querySelector('.remove-choice');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                handleChoiceDelete(newRow);
            });
        }
        
        updateAllFormIndexes();
    } catch (error) {
        console.error('Error adding choice:', error);
    }
}

// Handle deletion
function handleVariationDelete(variationForm) {
    const deleteInput = variationForm.querySelector('input[name$="-DELETE"]');
    if (deleteInput) {
        // If this is an existing variation, mark for deletion
        deleteInput.value = 'on';
        variationForm.style.display = 'none';
    } else {
        // If this is a new variation, remove it entirely
        variationForm.remove();
    }
    updateAllFormIndexes();
}

function handleChoiceDelete(choiceRow) {
    const deleteInput = choiceRow.querySelector('input[name$="-DELETE"]');
    if (deleteInput) {
        // If this is an existing choice, mark for deletion
        deleteInput.value = 'on';
        choiceRow.style.display = 'none';
    } else {
        // If this is a new choice, remove it entirely
        choiceRow.remove();
    }
    updateAllFormIndexes();
}

// Form management
function updateAllFormIndexes() {
    updateVariationIndexes();
    updateManagementForms();
}

function updateVariationIndexes() {
    const container = document.getElementById('variation-container');
    if (!container) return;

    const variations = container.querySelectorAll('.variation-form');
    variations.forEach((variation, index) => {
        variation.dataset.index = index;
        
        // Update variation form fields
        variation.querySelectorAll('[name*="variation-"]').forEach(field => {
            field.name = field.name.replace(/variation-\d+/, `variation-${index}`);
            if (field.id) {
                field.id = field.id.replace(/variation-\d+/, `variation-${index}`);
            }
        });
        
        // Update choice form fields
        const choicesContainer = variation.querySelector('.choices-container');
        if (choicesContainer) {
            const choices = choicesContainer.querySelectorAll('.choice-row');
            choices.forEach((choice, choiceIndex) => {
                choice.querySelectorAll('[name*="choices_"]').forEach(field => {
                    field.name = field.name.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                    if (field.id) {
                        field.id = field.id.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                    }
                });
            });
        }
    });
}

function updateManagementForms() {
    const container = document.getElementById('variation-container');
    if (!container) return;

    // Update variation management form
    const variations = container.querySelectorAll('.variation-form:not([style*="display: none"])');
    const variationTotal = document.querySelector('input[name="variation-TOTAL_FORMS"]');
    if (variationTotal) {
        variationTotal.value = variations.length;
    }
    
    // Update choices management forms
    variations.forEach((variation, index) => {
        const choicesContainer = variation.querySelector('.choices-container');
        if (choicesContainer) {
            const choices = choicesContainer.querySelectorAll('.choice-row:not([style*="display: none"])');
            const choicesTotal = variation.querySelector(`input[name="choices_${index}-TOTAL_FORMS"]`);
            if (choicesTotal) {
                choicesTotal.value = choices.length;
            }
        }
    });
}

// Form validation
function validateForm() {
    let isValid = true;
    const container = document.getElementById('variation-container');
    
    if (!container) return true;
    
    const variations = container.querySelectorAll('.variation-form:not([style*="display: none"])');
    variations.forEach(variation => {
        const variationSelect = variation.querySelector('select[name*="variation"]');
        if (!variationSelect || !variationSelect.value) {
            isValid = false;
            variationSelect.classList.add('is-invalid');
        }
        
        const choices = variation.querySelectorAll('.choice-row:not([style*="display: none"])');
        choices.forEach(choice => {
            const nameInput = choice.querySelector('input[name*="name"]');
            if (!nameInput || !nameInput.value.trim()) {
                isValid = false;
                nameInput.classList.add('is-invalid');
            }
        });
    });
    
    return isValid;
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

