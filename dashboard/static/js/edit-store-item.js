document.addEventListener('DOMContentLoaded', function() {
    initializeFileInputs();
    initializeVariationHandlers();
    initializeModalHandlers();
    updateFormIndexes();
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

// Variation handlers initialization
function initializeVariationHandlers() {
    // Add variation button handler
    document.getElementById('add-variation')?.addEventListener('click', handleAddVariation);

    // Initialize existing variation buttons
    document.querySelectorAll('.add-variation-btn').forEach(btn => {
        btn.addEventListener('click', handleVariationPopup);
    });

    // Remove variation button handler
    document.querySelectorAll('.remove-variation').forEach(btn => {
        btn.addEventListener('click', handleRemoveVariation);
    });

    // Initialize choice handlers
    document.querySelectorAll('.remove-choice').forEach(btn => {
        btn.addEventListener('click', handleChoiceDelete);
    });

    document.querySelectorAll('.add-choice-link').forEach(btn => {
        btn.addEventListener('click', handleAddChoice);
    });
}

// Modal handlers initialization
function initializeModalHandlers() {
    const modal = document.getElementById('variation-popup');
    
    // Close button handlers
    document.querySelectorAll('.close, .close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    });

    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Variation form submission
    document.getElementById('variation-form')?.addEventListener('submit', handleVariationSubmit);
}

// Variation handlers
function handleVariationPopup(e) {
    e.preventDefault();
    const modal = document.getElementById('variation-popup');
    const variationForm = this.closest('.variation-form');
    modal.dataset.triggerFormIndex = variationForm.dataset.index;
    modal.style.display = 'block';
}

async function handleAddVariation(e) {
    e.preventDefault();
    const container = document.getElementById('variation-container');
    const nextIndex = container.querySelectorAll('.variation-form').length;

    try {
        const response = await fetch(`/dashboard/add-variation-with-choices/?form_index=${nextIndex}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const html = await response.text();
        container.insertAdjacentHTML('beforeend', html);
        
        const newVariation = container.lastElementChild;
        initializeVariationHandlers();
        updateFormIndexes();
    } catch (error) {
        console.error('Error adding variation:', error);
    }
}

function handleRemoveVariation(e) {
    e.preventDefault();
    const variationForm = this.closest('.variation-form');
    const deleteInput = variationForm.querySelector('input[name$="-DELETE"]');
    
    if (deleteInput) {
        // If this is an existing variation, mark for deletion
        deleteInput.value = 'on';
        variationForm.style.display = 'none';
    } else {
        // If this is a new variation, remove it entirely
        variationForm.remove();
    }
    
    updateFormIndexes();
}

// Choice handlers
async function handleAddChoice(e) {
    e.preventDefault();
    const variationForm = this.closest('.variation-form');
    const variationIndex = this.getAttribute('variation-index');
    const choicesContainer = variationForm.querySelector('.choices-container');
    const choiceCount = choicesContainer.querySelectorAll('.choice-row:not([style*="display: none"])').length;

    try {
        const response = await fetch(`/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${choiceCount}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        // Remove plus icon from current last row
        const currentPlusIcon = choicesContainer.querySelector('.add-choice-link');
        if (currentPlusIcon) {
            currentPlusIcon.remove();
        }
        
        const html = await response.text();
        choicesContainer.insertAdjacentHTML('beforeend', html);
        
        const newRow = choicesContainer.lastElementChild;
        newRow.querySelector('.remove-choice')?.addEventListener('click', handleChoiceDelete);
        updateFormIndexes();
    } catch (error) {
        console.error('Error adding choice:', error);
    }
}

function handleChoiceDelete(e) {
    e.preventDefault();
    const choiceRow = this.closest('.choice-row');
    const deleteInput = choiceRow.querySelector('input[name$="-DELETE"]');
    const choicesContainer = choiceRow.closest('.choices-container');
    
    if (deleteInput) {
        // If this is an existing choice, mark for deletion
        deleteInput.value = 'on';
        choiceRow.style.display = 'none';
    } else {
        // If this is a new choice, remove it entirely
        choiceRow.remove();
    }
    
    // Update the last visible row with plus icon
    const visibleRows = choicesContainer.querySelectorAll('.choice-row:not([style*="display: none"])');
    const lastVisibleRow = visibleRows[visibleRows.length - 1];
    
    if (lastVisibleRow) {
        choicesContainer.querySelectorAll('.add-choice-link').forEach(link => link.remove());
        const nameCell = lastVisibleRow.querySelector('td:first-child');
        if (!nameCell.querySelector('.add-choice-link')) {
            const plusIcon = document.createElement('a');
            plusIcon.href = '#';
            plusIcon.className = 'add-choice-link fa fa-plus';
            plusIcon.style.cssText = 'text-decoration: none; color:#4caf50; margin-left:10px';
            plusIcon.setAttribute('variation-index', lastVisibleRow.closest('.variation-form').dataset.index);
            plusIcon.addEventListener('click', handleAddChoice);
            nameCell.appendChild(plusIcon);
        }
    }
    
    updateFormIndexes();
}

// Form management
function updateFormIndexes() {
    const container = document.getElementById('variation-container');
    const variations = container.querySelectorAll('.variation-form');
    
    // Update variation total forms
    const variationTotal = document.querySelector('input[name="variation-TOTAL_FORMS"]');
    if (variationTotal) {
        variationTotal.value = variations.length;
    }
    
    variations.forEach((variation, index) => {
        variation.dataset.index = index;
        
        // Update variation fields
        variation.querySelectorAll('[name*="variation-"]').forEach(field => {
            field.name = field.name.replace(/variation-\d+/, `variation-${index}`);
            if (field.id) {
                field.id = field.id.replace(/variation-\d+/, `variation-${index}`);
            }
        });
        
        // Update choices formset
        const choicesContainer = variation.querySelector('.choices-container');
        if (choicesContainer) {
            const choices = choicesContainer.querySelectorAll('.choice-row');
            const choicesTotal = variation.querySelector(`input[name="choices_${index}-TOTAL_FORMS"]`);
            
            if (choicesTotal) {
                choicesTotal.value = choices.length;
                
                choices.forEach((choice, choiceIndex) => {
                    choice.querySelectorAll('[name*="choices_"]').forEach(field => {
                        field.name = field.name.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                        if (field.id) {
                            field.id = field.id.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                        }
                    });
                });
            }
        }
    });
}

async function handleVariationSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const modal = document.getElementById('variation-popup');
    
    try {
        const response = await fetch('/dashboard/add-variation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            // Add the new option to variation dropdowns
            const selects = document.querySelectorAll('select[name*="variation"]');
            const option = new Option(data.variation.name, data.variation.id);
            
            selects.forEach(select => {
                select.add(option.cloneNode(true));
                if (select.closest('.variation-form')?.dataset.index === modal.dataset.triggerFormIndex) {
                    select.value = data.variation.id;
                }
            });
            
            modal.style.display = 'none';
            e.target.reset();
        } else {
            alert('Error creating variation: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error creating variation');
    }
}
document.addEventListener('DOMContentLoaded', function() {
    initializeVariationHandlers();
    updatePlusIcons();
});

function initializeVariationHandlers() {
    // Initialize delete handlers for existing elements
    document.querySelectorAll('.remove-choice').forEach(btn => {
        btn.addEventListener('click', handleChoiceDelete);
    });

    document.querySelectorAll('.remove-variation').forEach(btn => {
        btn.addEventListener('click', handleVariationDelete);
    });

    // Initialize add choice handlers
    document.querySelectorAll('.add-choice-link').forEach(btn => {
        btn.addEventListener('click', handleAddChoice);
    });
}

async function handleChoiceDelete(e) {
    e.preventDefault();
    const choiceRow = e.target.closest('.choice-row');
    const choiceId = choiceRow.dataset.choiceId;
    const variationForm = choiceRow.closest('.variation-form');
    
    if (choiceId) {
        // Existing choice, delete from database
        try {
            const response = await fetch(`/dashboard/delete-choice/${choiceId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                }
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
        } catch (error) {
            console.error('Error deleting choice:', error);
            return;
        }
    }
    
    // Remove the row from DOM
    choiceRow.remove();
    
    // Update form management
    updateFormIndexes();
    updatePlusIcons();
}

async function handleVariationDelete(e) {
    e.preventDefault();
    const variationForm = e.target.closest('.variation-form');
    const variationId = variationForm.dataset.variationId;
    
    if (variationId) {
        // Existing variation, delete from database
        try {
            const response = await fetch(`/dashboard/delete-variation/${variationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                }
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
        } catch (error) {
            console.error('Error deleting variation:', error);
            return;
        }
    }
    
    // Remove the form from DOM
    variationForm.remove();
    
    // Update form management
    updateFormIndexes();
    updatePlusIcons();
}

function updatePlusIcons() {
    // Remove all existing plus icons first
    document.querySelectorAll('.add-choice-link').forEach(icon => icon.remove());
    
    // Add plus icon to the last choice row of each variation
    document.querySelectorAll('.variation-form').forEach(variationForm => {
        const choiceRows = variationForm.querySelectorAll('.choice-row');
        if (choiceRows.length === 0) {
            // If no choices, add plus icon to the variation form itself
            addPlusIconToVariation(variationForm);
        } else {
            // Add plus icon to the last choice row
            addPlusIconToChoice(choiceRows[choiceRows.length - 1], variationForm);
        }
    });
}

function addPlusIconToChoice(choiceRow, variationForm) {
    const nameField = choiceRow.querySelector('[name*="name"]').closest('td');
    const plusIcon = document.createElement('a');
    plusIcon.href = '#';
    plusIcon.className = 'add-choice-link fa fa-plus';
    plusIcon.style.cssText = 'text-decoration: none; color:#4caf50; margin-left:10px';
    plusIcon.dataset.variationIndex = variationForm.dataset.index;
    plusIcon.addEventListener('click', handleAddChoice);
    nameField.appendChild(plusIcon);
}

function addPlusIconToVariation(variationForm) {
    const variationFields = variationForm.querySelector('.variation-fields');
    const plusIcon = document.createElement('a');
    plusIcon.href = '#';
    plusIcon.className = 'add-choice-link fa fa-plus';
    plusIcon.style.cssText = 'text-decoration: none; color:#4caf50; margin-left:10px';
    plusIcon.dataset.variationIndex = variationForm.dataset.index;
    plusIcon.addEventListener('click', handleAddChoice);
    variationFields.appendChild(plusIcon);
}

async function handleAddChoice(e) {
    e.preventDefault();
    const variationForm = e.target.closest('.variation-form');
    const variationIndex = variationForm.dataset.index;
    const choicesContainer = variationForm.querySelector('.choices-container');
    const nextIndex = choicesContainer ? choicesContainer.querySelectorAll('.choice-row').length : 0;

    try {
        const response = await fetch(`/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${nextIndex}`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const html = await response.text();
        
        if (!choicesContainer) {
            // Create choices container if it doesn't exist
            const container = document.createElement('div');
            container.className = 'choices-container';
            variationForm.appendChild(container);
        }
        
        choicesContainer.insertAdjacentHTML('beforeend', html);
        
        // Initialize the new choice row
        const newRow = choicesContainer.lastElementChild;
        const deleteBtn = newRow.querySelector('.remove-choice');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', handleChoiceDelete);
        }
        
        updateFormIndexes();
        updatePlusIcons();
    } catch (error) {
        console.error('Error adding choice:', error);
    }
}
