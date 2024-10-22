// Global variable to track which select triggered the popup
        let triggeringSelect = null;
        let variationCounter = 1;
              
        // Function to initialize file input handlers
        function initializeFileInputs() {
            document.querySelector('#id_item_photo').addEventListener('change', function() {
                let fileName = this.files[0] ? this.files[0].name : 'No file chosen';
                document.querySelector('.file-name').textContent = fileName;
            });
          
            const fileInput = document.querySelector('.custom-file-input');
            const fileNameSpan = document.querySelector('.file-name');
            if (fileInput && fileNameSpan) {
                fileInput.addEventListener('change', function() {
                    fileNameSpan.textContent = fileInput.files.length > 0 
                        ? fileInput.files[0].name 
                        : 'No file chosen';
                });
            }
        }
        
        // Function to initialize variation buttons
        function initializeVariationButtons() {
            const modal = document.getElementById('variation-popup');
            const addVariationBtns = document.querySelectorAll('.add-variation-btn');
            const closeButtons = document.querySelectorAll('.close, .close-modal');
        
            // Remove existing event listeners
            addVariationBtns.forEach(btn => {
                btn.replaceWith(btn.cloneNode(true));
            });
          
            // Add new event listeners
            document.querySelectorAll('.add-variation-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Store the select element associated with this button
                    triggeringSelect = btn.closest('.variation-form').querySelector('select[name*="variation"]');
                    modal.style.display = 'block';
                });
            });
          
            // Close modal handlers
            closeButtons.forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    modal.style.display = 'none';
                });
            });
        }
        
        // Function to add plus icon to the last choice row
        function addPlusIconToLastRow(choicesContainer, variationIndex) {
            const lastRow = choicesContainer.querySelector('.choice-row:last-child');
            if (lastRow) {
                const firstCell = lastRow.querySelector('td:first-child');
                const existingPlusIcon = firstCell.querySelector('.add-choice-link');
                if (!existingPlusIcon) {
                    firstCell.insertAdjacentHTML(
                        'beforeend',
                        `<a href="#" class="add-choice-link fa fa-plus" 
                            style="text-decoration: none; color:#4caf50; margin-left:10px" 
                            data-variation-index="${variationIndex}"></a>`
                    );
                }
            }
        }
        
        // Function to update form indexes
        function updateFormIndexes() {
            const totalFormsInput = document.querySelector('[name="variation-TOTAL_FORMS"]');
            if (totalFormsInput) {
                totalFormsInput.value = variationCounter;
            }
          
            document.querySelectorAll('.variation-form').forEach((form, index) => {
                form.dataset.index = index;
            
                form.querySelectorAll('[name*="variation-"]').forEach((input) => {
                    const oldName = input.name;
                    const newName = oldName.replace(/variation-\d+/, `variation-${index}`);
                    input.name = newName;
                    if (input.id) {
                        input.id = input.id.replace(/variation-\d+/, `variation-${index}`);
                    }
                });
              
                const choicesContainer = form.querySelector('.choices-container');
                if (choicesContainer) {
                    const plusIcon = choicesContainer.querySelector('.add-choice-link');
                    if (plusIcon) {
                        plusIcon.dataset.variationIndex = index;
                    }
                  
                    choicesContainer.querySelectorAll('.choice-row').forEach((row, choiceIndex) => {
                        row.querySelectorAll('input').forEach((input) => {
                            const oldName = input.name;
                            const newName = oldName.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                            input.name = newName;
                            if (input.id) {
                                input.id = input.id.replace(/choices_\d+-\d+/, `choices_${index}-${choiceIndex}`);
                            }
                        });
                    });
                }
            });
        }
        
        // Event Listeners
        document.addEventListener('DOMContentLoaded', function() {
            initializeFileInputs();
            initializeVariationButtons();
        
            // Close modal when clicking outside
            window.addEventListener('click', function(e) {
                const modal = document.getElementById('variation-popup');
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
        
        // Add Variation button handler
        document.getElementById('add-variation').addEventListener('click', function() {
            const nextIndex = variationCounter++;
        
            fetch(`/dashboard/add-variation-with-choices/?form_index=${nextIndex}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(html => {
                    document.getElementById('variation-container').insertAdjacentHTML('beforeend', html);
                    updateFormIndexes();
                    initializeVariationButtons();
                })
                .catch(error => {
                    console.error('Error adding variation:', error);
                });
        });
        
        // Add Choice and Remove Choice handlers
        document.addEventListener('click', function(e) {
            // Add choice handler
            if (e.target.classList.contains('add-choice-link')) {
                e.preventDefault();
                e.stopPropagation();
            
                const variationIndex = e.target.dataset.variationIndex;
                const variationForm = e.target.closest('.variation-form');
                const choicesContainer = variationForm.querySelector('.choices-container');
                const managementForm = variationForm.querySelector('[name*="TOTAL_FORMS"]');
            
                if (!managementForm) {
                    console.error('Management form not found');
                    return;
                }
              
                const nextIndex = parseInt(managementForm.value);
              
                fetch(`/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${nextIndex}`)
                    .then(response => response.text())
                    .then(html => {
                        // Remove plus icon from current last row
                        const currentLastRow = choicesContainer.querySelector('.choice-row:last-child .add-choice-link');
                        if (currentLastRow) {
                            currentLastRow.remove();
                        }
                      
                        // Add new row
                        choicesContainer.insertAdjacentHTML('beforeend', html);
                        
                        // Add plus icon to new last row
                        addPlusIconToLastRow(choicesContainer, variationIndex);
                        
                        managementForm.value = nextIndex + 1;
                    })
                    .catch(error => {
                        console.error('Error adding choice:', error);
                    });
            }
          
            // Remove choice handler
            if (e.target.classList.contains('remove-choice')) {
                e.preventDefault();
                e.stopPropagation();
            
                const choiceRow = e.target.closest('.choice-row');
                const choicesContainer = choiceRow.closest('.choices-container');
                const variationForm = choicesContainer.closest('.variation-form');
                const managementForm = variationForm.querySelector('[name*="TOTAL_FORMS"]');
                const variationIndex = variationForm.dataset.index;
            
                // Check if this row has the plus icon
                const hasAddButton = choiceRow.querySelector('.add-choice-link') !== null;
                
                // Remove the row
                choiceRow.remove();
            
                // Update management form count
                if (managementForm) {
                    managementForm.value = parseInt(managementForm.value) - 1;
                }
              
                // If the removed row had the plus icon, add it to the new last row
                if (hasAddButton) {
                    addPlusIconToLastRow(choicesContainer, variationIndex);
                }
            }
        });
        
        // Variation form submission handler
        document.getElementById('variation-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
        
            fetch('/dashboard/add-variation/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Add the new option to all variation dropdowns
                    const selects = document.querySelectorAll('select[name*="variation"]');
                    selects.forEach(select => {
                        const option = new Option(data.variation.name, data.variation.id);
                        select.add(option);
                        
                        // Only set the value for the dropdown that triggered the popup
                        if (select === triggeringSelect) {
                            select.value = data.variation.id;
                        }
                    });
                  
                    // Reset the triggering select
                    triggeringSelect = null;
                    
                    // Close modal and reset form
                    document.getElementById('variation-popup').style.display = 'none';
                    this.reset();
                } else {
                    alert('Error creating variation: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating variation');
            });
        });