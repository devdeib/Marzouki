
// Add this to your existing JavaScript
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('variation-popup');
  const addVariationBtns = document.querySelectorAll('.add-variation-btn');
  const closeButtons = document.querySelectorAll('.close, .close-modal');
  
  // Open modal
  addVariationBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      modal.style.display = 'block';
    });
  });
  
  // Close modal
  closeButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      modal.style.display = 'none';
    });
  });
  
  // Close modal when clicking outside
  window.addEventListener('click', function(e) {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
  
  // Handle form submission
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
        // Update all variation dropdowns
        const selects = document.querySelectorAll('select[name*="variation"]');
        selects.forEach(select => {
          const option = new Option(data.variation.name, data.variation.id);
          select.add(option);
          select.value = data.variation.id;
        });
        
        // Close modal and reset form
        modal.style.display = 'none';
        document.getElementById('variation-form').reset();
      } else {
        alert('Error creating variation: ' + data.error);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error creating variation');
    });
  });
});