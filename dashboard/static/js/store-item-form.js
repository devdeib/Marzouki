let variationCounter = 1;

  // Add Variation button handler
  document.getElementById('add-variation').addEventListener('click', function(e) {
      e.preventDefault();
      
      // Create modal dynamically
      const modalHTML = `
        <div id="variation-popup" class="modal">
          <div class="modal-content">
            <div class="modal-header">
              <h3>Add New Variation</h3>
              <span class="close">&times;</span>
            </div>
            <div class="modal-body">
              <form id="variation-form" method="POST">
                {% csrf_token %}
                <div class="form-group">
                  <label for="variation-name" class="form-label">Variation Name</label>
                  <input type="text" id="variation-name" name="name" class="form-control" required>
                </div>
                <div class="form-actions">
                  <button type="submit" class="btn btn-primary">Save</button>
                  <button type="button" class="btn btn-secondary close-modal">Cancel</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;

      // Add modal to the document
      document.body.insertAdjacentHTML('beforeend', modalHTML);
      
      // Get the modal element
      const modal = document.getElementById('variation-popup');
      modal.style.display = 'block';

      // Add event listeners for the modal
      const closeModal = function() {
          modal.remove(); // Remove modal from DOM completely
      };

      // Close button handler
      modal.querySelector('.close').addEventListener('click', closeModal);
      
      // Cancel button handler
      modal.querySelector('.close-modal').addEventListener('click', closeModal);
      
      // Click outside modal handler
      window.addEventListener('click', function(event) {
          if (event.target === modal) {
              closeModal();
          }
      });

      // Form submission handler
      modal.querySelector('#variation-form').addEventListener('submit', function(event) {
          event.preventDefault();
          const variationName = this.querySelector('#variation-name').value;
          const nextIndex = variationCounter++;
          
          fetch(`/dashboard/add-variation-with-choices/?form_index=${nextIndex}&variation_name=${encodeURIComponent(variationName)}`)
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`HTTP error! status: ${response.status}`);
                  }
                  return response.text();
              })
              .then(html => {
                  document.getElementById('variation-container').insertAdjacentHTML('beforeend', html);
                  updateFormIndexes();
                  closeModal();
                  console.log('Successfully added new variation');
              })
              .catch(error => {
                  console.error('Error adding variation:', error);
              });
      });
  });

  // Add Choice and Remove Choice handlers
  document.addEventListener('click', function(e) {
      // Handle Add Choice
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
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`HTTP error! status: ${response.status}`);
                  }
                  return response.text();
              })
              .then(html => {
                  // Remove plus icon from current last row
                  const currentLastRow = choicesContainer.querySelector('.choice-row:last-child .add-choice-link');
                  if (currentLastRow) {
                      currentLastRow.remove();
                  }
                  
                  // Add new row
                  choicesContainer.insertAdjacentHTML('beforeend', html);
                  
                  // Add plus icon to new last row
                  const newLastRow = choicesContainer.querySelector('.choice-row:last-child td:first-child');
                  if (newLastRow) {
                      newLastRow.insertAdjacentHTML(
                          'beforeend',
                          `<a href="#" class="add-choice-link fa fa-plus" 
                              style="text-decoration: none; color:#4caf50; margin-left:10px" 
                              data-variation-index="${variationIndex}"></a>`
                      );
                  }
                  
                  // Update management form
                  managementForm.value = nextIndex + 1;
              })
              .catch(error => {
                  console.error('Error adding choice:', error);
              });
      }
      
      // Handle Remove Choice
      if (e.target.classList.contains('remove-choice')) {
          const row = e.target.closest('.choice-row');
          const variationForm = row.closest('.variation-form');
          const choicesContainer = variationForm.querySelector('.choices-container');
          const managementForm = variationForm.querySelector('[name*="TOTAL_FORMS"]');
          const variationIndex = variationForm.dataset.index;
          
          // If this was the last row with the plus icon, move the plus icon to the new last row
          const wasLastRow = !row.nextElementSibling;
          if (wasLastRow && row.previousElementSibling) {
              const plusIcon = row.querySelector('.add-choice-link');
              if (plusIcon) {
                  const newLastRow = row.previousElementSibling.querySelector('td:first-child');
                  newLastRow.appendChild(plusIcon);
              }
          }
          
          row.remove();
          managementForm.value = parseInt(managementForm.value) - 1;
          
          // Update remaining choices' indices
          choicesContainer.querySelectorAll('.choice-row').forEach((row, index) => {
              row.querySelectorAll('input').forEach((input) => {
                  const oldName = input.name;
                  const newName = oldName.replace(/choices_\d+-\d+/, `choices_${variationIndex}-${index}`);
                  input.name = newName;
                  if (input.id) {
                      input.id = input.id.replace(/choices_\d+-\d+/, `choices_${variationIndex}-${index}`);
                  }
              });
          });
      }
  });

  function updateFormIndexes() {
      // Update variation management form
      const totalFormsInput = document.querySelector('[name="variation-TOTAL_FORMS"]');
      if (totalFormsInput) {
          totalFormsInput.value = variationCounter;
      }
      
      // Update each variation form's indices
      document.querySelectorAll('.variation-form').forEach((form, index) => {
          form.dataset.index = index;
          
          // Update variation fields
          form.querySelectorAll('[name*="variation-"]').forEach((input) => {
              const oldName = input.name;
              const newName = oldName.replace(/variation-\d+/, `variation-${index}`);
              input.name = newName;
              if (input.id) {
                  input.id = input.id.replace(/variation-\d+/, `variation-${index}`);
              }
          });
          
          // Update choices fields and plus icon
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

  // Form submission handler for debugging
  document.getElementById('store-item-form').addEventListener('submit', function(e) {
      const formData = new FormData(this);
      for (let pair of formData.entries()) {
          console.log(pair[0], pair[1]);
      }
  });