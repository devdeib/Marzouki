// ----------------------- Initializations ----------------------------
let triggeringSelect = null;
let variationCounter = 1;
let activeUploads = new Map();
let isProcessingVariation = false;

// Add after the initial variable declarations
function checkRequiredElements() {
  const requiredElements = {
    variationContainer: document.getElementById("variation-container"),
    imagesContainer: document.getElementById("images-container"),
    videosContainer: document.getElementById("videos-container"),
    variationPopup: document.getElementById("variation-popup"),
  };

  const missingElements = Object.entries(requiredElements)
    .filter(([, element]) => !element)
    .map(([name]) => name);

  if (missingElements.length > 0) {
    console.warn("Missing required elements:", missingElements.join(", "));
  }

  return requiredElements;
}

// Call this in your DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", function () {
  const elements = checkRequiredElements();
  if (elements.variationContainer) {
    initializeFileInputs();
    initializeFormManagement();
    bindEventListeners();
    updateAllFormIndexes();
    initializeVariationPopup();
    initializeVariationHandlers();
    initializeMediaButtons();
    initializeExistingMediaHandlers();
    initializeModalHandlers();
    initializeFormSubmission();
    console.log("DOM loaded and initialized");
  }
});

function initializeFileInputs() {
  const fileInput = document.querySelector("#id_item_photo");
  const fileNameSpan = document.querySelector(".file-name");

  if (fileInput && fileNameSpan) {
    fileInput.addEventListener("change", function () {
      const fileName = this.files[0] ? this.files[0].name : "No file chosen";
      fileNameSpan.textContent = fileName;
    });
  }
}

function initializeFormManagement() {
  updateManagementForms();
  initializeExistingForms();
}

function initializeExistingForms() {
  const variationForms = document.querySelectorAll(".variation-form");
  variationForms.forEach((form, index) => {
    form.dataset.index = index;
    initializeDeleteButtons(form);
    initializeChoiceForms(form);
  });
}

function initializeDeleteButtons(form) {
  const deleteBtn = form.querySelector(".remove-variation");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", function () {
      handleVariationDelete(form);
    });
  }
}

function bindEventListeners() {
  const addVariationBtn = document.getElementById("add-variation");
  if (addVariationBtn) {
    addVariationBtn.addEventListener("click", addNewVariation);
  }

  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      if (validateForm()) {
        const formData = new FormData(this);
        try {
          const response = await fetch(this.action, {
            method: "POST",
            body: formData,
            headers: {
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
          });

          if (response.redirected) {
            window.location.href = response.url;
          } else if (response.ok) {
            window.location.href = "/dashboard/store_items/";
          }
        } catch (error) {
          console.error("Error:", error);
          alert("An error occurred while submitting the form.");
        }
      }
    });
  }
}

// Replace the existing initializeModalHandlers() with this version
function initializeModalHandlers() {
  const modal = document.getElementById("variation-popup");

  // Close button handlers
  document.querySelectorAll(".close, .close-modal").forEach((btn) => {
    btn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  });

  // Click outside modal to close
  window.addEventListener("click", function (e) {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });

  // Variation form submission
  const variationForm = document.getElementById("variation-form");
  if (variationForm) {
    variationForm.addEventListener("submit", handleVariationSubmit);
  }
}

// ----------------------- Variations Management ----------------------------
function initializeVariationPopup() {
    console.log("Initializing variation popup...");
    const modal = document.getElementById("variation-popup");
    const variationForm = document.getElementById("variation-form");

    // Remove all existing event listeners
    const newForm = variationForm.cloneNode(true);
    variationForm.parentNode.replaceChild(newForm, variationForm);

    // Add single event listener for form submission
    newForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        e.stopPropagation();

        if (isProcessingVariation) {
            console.log("Already processing a variation - preventing duplicate");
            return;
        }

        isProcessingVariation = true;
        const formData = new FormData(this);

        try {
            const response = await fetch("/dashboard/add-variation/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                console.log("Variation created successfully:", data.variation);

                if (triggeringSelect) {
                    // Check if option already exists
                    let existingOption = Array.from(triggeringSelect.options)
                        .find(option => option.value === data.variation.id.toString());

                    if (!existingOption) {
                        const option = new Option(data.variation.name, data.variation.id);
                        triggeringSelect.add(option);
                    }
                    triggeringSelect.value = data.variation.id;
                }

                modal.style.display = "none";
                this.reset();
            } else {
                console.error("Error creating variation:", data.error);
                alert("Error creating variation: " + data.error);
            }
        } catch (error) {
            console.error("Error in variation submission:", error);
            alert("Error creating variation");
        } finally {
            isProcessingVariation = false;
            triggeringSelect = null;
        }
    });

    // Initialize variation add buttons
    document.querySelectorAll(".add-variation-btn").forEach(btn => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (isProcessingVariation) return;

            const variationForm = this.closest(".variation-form");
            if (!variationForm) return;

            triggeringSelect = variationForm.querySelector('select[name*="variation"]');
            if (!triggeringSelect) return;

            modal.style.display = "block";
            modal.dataset.triggerFormIndex = variationForm.dataset.index;
        });
    });

    // Modal close handlers
    const closeModal = () => {
        modal.style.display = "none";
        isProcessingVariation = false;
        triggeringSelect = null;
        newForm.reset();
    };

    document.querySelectorAll(".close, .close-modal").forEach(btn => {
        btn.addEventListener("click", closeModal);
    });

    window.addEventListener("click", function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function initializeVariationHandlers() {
    initializeVariationPopup();

    // Initialize delete buttons
    document.querySelectorAll(".remove-variation").forEach(btn => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleVariationDelete(this.closest(".variation-form"));
        });
    });
}

function handleVariationDelete(variationForm) {
  const allVisibleVariations = document.querySelectorAll(
    '.variation-form:not([style*="display: none"])'
  );

  if (allVisibleVariations.length > 1) {
    const deleteInput = variationForm.querySelector('input[name$="-DELETE"]');
    if (deleteInput) {
      deleteInput.value = "on";
      variationForm.style.display = "none";
    } else {
      variationForm.remove();
    }
    updateAllFormIndexes();
  }   
}


async function addNewVariation(e) {
    e.preventDefault();
    const container = document.getElementById("variation-container");
    if (!container) return;

    const variationCount = container.querySelectorAll(".variation-form").length;
    isProcessingVariation = true;

    try {
        const response = await fetch(`/dashboard/add-variation-with-choices/?form_index=${variationCount}`);
        if (!response.ok) throw new Error("Network response was not ok");

        const html = await response.text();
        container.insertAdjacentHTML("beforeend", html);

        const newForm = container.lastElementChild;
        newForm.dataset.index = variationCount;

        initializeVariationHandlers();
        initializeDeleteButtons(newForm);
        initializeChoiceForms(newForm);
        updateAllFormIndexes();
    } catch (error) {
        console.error("Error adding variation:", error);
    } finally {
        isProcessingVariation = false;
    }
}

// Single DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", function() {
    console.log("Document loaded - initializing variations");
    initializeVariationHandlers();

    // Add variation button handler
    const addVariationBtn = document.getElementById("add-variation");
    if (addVariationBtn) {
        const newBtn = addVariationBtn.cloneNode(true);
        addVariationBtn.parentNode.replaceChild(newBtn, addVariationBtn);

        newBtn.addEventListener("click", async function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (isProcessingVariation) {
                console.log("Already processing a variation - preventing duplicate");
                return;
            }

            await addNewVariation(e);
        });
    }
});

// --------------------------- Choice Management ---------------------------
function initializeChoiceForms(variationForm) {
  const choicesContainer = variationForm.querySelector(".choices-container");
  if (!choicesContainer) return;

  choicesContainer
    .querySelectorAll(".remove-choice, .remove-choice i")
    .forEach((element) => {
      element.addEventListener("click", handleRemoveChoice);
    });

  const addChoiceLink = choicesContainer.querySelector(".add-choice-link");
  if (addChoiceLink) {
    addChoiceLink.addEventListener("click", handleAddChoice);
  }
}

function handleAddChoice(e) {
  e.preventDefault();
  const variationForm = e.target.closest(".variation-form");
  const variationIndex = variationForm.dataset.index;
  const choicesContainer = variationForm.querySelector(".choices-container");
  const choiceCount = choicesContainer.querySelectorAll(".choice-row").length;

  fetch(
    `/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${choiceCount}`
  )
    .then((response) => response.text())
    .then((html) => {
      choicesContainer.insertAdjacentHTML("beforeend", html);
      const newRow = choicesContainer.lastElementChild;
      newRow
        .querySelector(".remove-choice")
        .addEventListener("click", handleRemoveChoice);
      updateChoiceIndexes(choicesContainer, variationForm);
      updatePlusIcon(choicesContainer, variationIndex);
    });
}

function handleRemoveChoice(e) {
  e.preventDefault();
  // Handle both icon and button clicks
  const removeBtn = e.target.closest(".remove-choice");
  const choiceRow = removeBtn.closest(".choice-row");
  const choicesContainer = choiceRow.closest(".choices-container");
  const variationForm = choicesContainer.closest(".variation-form");
  const variationIndex = variationForm.dataset.index;
  const choiceId = choiceRow.dataset.choiceId;

  if (choiceId) {
    fetch(`/dashboard/delete-choice/${choiceId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
          .value,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          choiceRow.remove();
          updateChoiceIndexes(choicesContainer, variationForm);
          updatePlusIcon(choicesContainer, variationIndex);
        }
      });
  } else {
    choiceRow.remove();
    updateChoiceIndexes(choicesContainer, variationForm);
    updatePlusIcon(choicesContainer, variationIndex);
  }
}

function updateChoiceIndexes(choicesContainer, variationForm) {
  const variationIndex = variationForm.dataset.index;
  const choices = choicesContainer.querySelectorAll(".choice-row");

  choices.forEach((choice, index) => {
    choice.querySelectorAll('[name*="choices_"]').forEach((field) => {
      field.name = field.name.replace(
        /choices_\d+-\d+/,
        `choices_${variationIndex}-${index}`
      );
      if (field.id) {
        field.id = field.id.replace(
          /choices_\d+-\d+/,
          `choices_${variationIndex}-${index}`
        );
      }
    });
  });

  const totalFormsInput = variationForm.querySelector(
    `input[name="choices_${variationIndex}-TOTAL_FORMS"]`
  );
  if (totalFormsInput) {
    totalFormsInput.value = choices.length;
  }
}

function updatePlusIcon(choicesContainer, variationIndex) {
  choicesContainer
    .querySelectorAll(".add-choice-link")
    .forEach((icon) => icon.remove());

  const rows = choicesContainer.querySelectorAll(".choice-row");
  if (rows.length === 0) return;

  const lastRow = rows[rows.length - 1];
  const nameCell = lastRow.querySelector("td:first-child");

  const plusIcon = document.createElement("a");
  plusIcon.href = "#";
  plusIcon.className = "add-choice-link fa fa-plus";
  plusIcon.style.cssText =
    "text-decoration: none; color:#4caf50; margin-left:10px";
  plusIcon.setAttribute("data-variation-index", variationIndex);
  plusIcon.addEventListener("click", handleAddChoice);

  nameCell.appendChild(plusIcon);
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".variation-form").forEach(initializeChoiceForms);

  // Re-initialize after adding new variation
  document
    .getElementById("add-variation")
    ?.addEventListener("click", function () {
      setTimeout(() => {
        const newForm = document.querySelector(".variation-form:last-child");
        if (newForm) initializeChoiceForms(newForm);
      }, 100);
    });
});

async function addNewChoice(e) {
  e.preventDefault();
  e.stopPropagation();

  const variationForm = this.closest(".variation-form");
  const variationIndex = this.getAttribute("data-variation-index");
  const choicesContainer = variationForm.querySelector(".choices-container");
  const choiceCount = choicesContainer.querySelectorAll(".choice-row").length;

  try {
    const response = await fetch(
      `/dashboard/add-choice-field/?variation_index=${variationIndex}&choice_index=${choiceCount}`
    );

    if (!response.ok) throw new Error("Network response was not ok");

    const html = await response.text();
    choicesContainer.insertAdjacentHTML("beforeend", html);

    // After adding new row, update the plus icon
    managePlusIcon(choicesContainer, variationIndex);

    // Add delete event listener to new row
    const newRow = choicesContainer.querySelector(".choice-row:last-child");
    const deleteBtn = newRow.querySelector(".remove-choice");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", handleChoiceDelete);
    }

    updateAllFormIndexes();
  } catch (error) {
    console.error("Error adding choice:", error);
  }
}

function initializeChoiceHandlers() {
  // Set up plus icons for all variation forms
  document.querySelectorAll(".variation-form").forEach((form) => {
    const choicesContainer = form.querySelector(".choices-container");
    const variationIndex = form.dataset.index;
    if (choicesContainer) {
      managePlusIcon(choicesContainer, variationIndex);
    }
  });

  // Set up delete handlers
  document.querySelectorAll(".remove-choice").forEach((btn) => {
    btn.addEventListener("click", handleChoiceDelete);
  });
}

// Call initialization when document is ready
document.addEventListener("DOMContentLoaded", function () {
  initializeChoiceHandlers();

  // Re-initialize handlers after adding new variation
  document
    .getElementById("add-variation")
    ?.addEventListener("click", function () {
      // Wait for the new variation to be added to DOM
      setTimeout(initializeChoiceHandlers, 100);
    });
});

function handleChoiceDelete(e) {
  e.preventDefault();
  const choiceRow = e.target.closest(".choice-row");
  const choicesContainer = choiceRow.closest(".choices-container");
  const variationForm = choicesContainer.closest(".variation-form");
  const variationIndex = variationForm.dataset.index;
  const choiceId = choiceRow.dataset.choiceId;

  const hasAddButton = choiceRow.querySelector(".add-choice-link") !== null;

  if (choiceId) {
    fetch(`/dashboard/delete-choice/${choiceId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          choiceRow.remove();
          reindexChoices(choicesContainer, variationForm, variationIndex, hasAddButton);
        }
      })
      .catch((error) => console.error("Error:", error));
  } else {
    choiceRow.remove();
    reindexChoices(choicesContainer, variationForm, variationIndex, hasAddButton);
  }
}

function reindexChoices(choicesContainer, variationForm, variationIndex, hasAddButton) {
  const remainingChoices = choicesContainer.querySelectorAll(".choice-row");
  remainingChoices.forEach((choice, index) => {
    choice.querySelectorAll('[name*="choices_"]').forEach((field) => {
      field.name = field.name.replace(
        /choices_\d+-\d+/,
        `choices_${variationIndex}-${index}`
      );
      if (field.id) {
        field.id = field.id.replace(
          /choices_\d+-\d+/,
          `choices_${variationIndex}-${index}`
        );
      }
    });
  });

  const managementForm = variationForm.querySelector('[name*="TOTAL_FORMS"]');
  if (managementForm) {
    managementForm.value = remainingChoices.length;
  }

  if (hasAddButton) {
    addPlusIconToLastRow(choicesContainer, variationIndex);
  }
  
  managePlusIcon(choicesContainer, variationIndex);
}


function updatePlusIconPosition(choicesContainer) {
  choicesContainer
    .querySelectorAll(".add-choice-link")
    .forEach((icon) => icon.remove());

  const visibleChoices = Array.from(
    choicesContainer.querySelectorAll(
      '.choice-row:not([style*="display: none"])'
    )
  );
  const lastVisibleRow = visibleChoices[visibleChoices.length - 1];

  if (lastVisibleRow) {
    const nameCell = lastVisibleRow.querySelector("td:first-child");
    const newPlusIcon = document.createElement("a");
    newPlusIcon.href = "#";
    newPlusIcon.className = "add-choice-link fa fa-plus";
    newPlusIcon.style.cssText =
      "text-decoration: none; color:#4caf50; margin-left:10px";
    newPlusIcon.setAttribute(
      "data-variation-index",
      lastVisibleRow.closest(".variation-form").dataset.index
    );
    newPlusIcon.addEventListener("click", addNewChoice);
    nameCell.appendChild(newPlusIcon);
  }
}

function addPlusIconToLastRow(choicesContainer, variationIndex) {
  const lastRow = choicesContainer.querySelector(".choice-row:last-child");
  if (lastRow) {
    const firstCell = lastRow.querySelector("td:first-child");
    const existingPlusIcon = firstCell.querySelector(".add-choice-link");
    if (!existingPlusIcon) {
      firstCell.insertAdjacentHTML(
        "beforeend",
        `<a href="#" class="add-choice-link fa fa-plus" 
                    style="text-decoration: none; color:#4caf50; margin-left:10px" 
                    data-variation-index="${variationIndex}"></a>`
      );
    }
  }
}

// Form management functions for choices
function updateAllFormIndexes() {
  updateVariationIndexes();
  updateManagementForms();
}

function updateVariationIndexes() {
  const container = document.getElementById("variation-container");
  if (!container) return;

  const variations = container.querySelectorAll(".variation-form");
  variations.forEach((variation, index) => {
    variation.dataset.index = index;

    variation.querySelectorAll('[name*="variation-"]').forEach((field) => {
      field.name = field.name.replace(/variation-\d+/, `variation-${index}`);
      if (field.id) {
        field.id = field.id.replace(/variation-\d+/, `variation-${index}`);
      }
    });

    const choicesContainer = variation.querySelector(".choices-container");
    if (choicesContainer) {
      const choices = choicesContainer.querySelectorAll(".choice-row");
      choices.forEach((choice, choiceIndex) => {
        choice.querySelectorAll('[name*="choices_"]').forEach((field) => {
          field.name = field.name.replace(
            /choices_\d+-\d+/,
            `choices_${index}-${choiceIndex}`
          );
          if (field.id) {
            field.id = field.id.replace(
              /choices_\d+-\d+/,
              `choices_${index}-${choiceIndex}`
            );
          }
        });
      });
    }
  });
}

function updateManagementForms() {
  const container = document.getElementById("variation-container");
  if (!container) return;

  const variations = container.querySelectorAll(
    '.variation-form:not([style*="display: none"])'
  );
  const variationTotal = document.querySelector(
    'input[name="variation-TOTAL_FORMS"]'
  );
  if (variationTotal) {
    variationTotal.value = variations.length;
  }

  variations.forEach((variation, index) => {
    const choicesContainer = variation.querySelector(".choices-container");
    if (choicesContainer) {
      const choices = choicesContainer.querySelectorAll(
        '.choice-row:not([style*="display: none"])'
      );
      const choicesTotal = variation.querySelector(
        `input[name="choices_${index}-TOTAL_FORMS"]`
      );
      if (choicesTotal) {
        choicesTotal.value = choices.length;
      }
    }
  });
}

// Event listener for choices

function managePlusIcon(choicesContainer, variationIndex) {
  // Remove all existing plus icons in this container
  choicesContainer
    .querySelectorAll(".add-choice-link")
    .forEach((icon) => icon.remove());

  // Get all visible choice rows
  const visibleRows = Array.from(
    choicesContainer.querySelectorAll(
      '.choice-row:not([style*="display: none"])'
    )
  );

  if (visibleRows.length > 0) {
    // Get the last visible row
    const lastRow = visibleRows[visibleRows.length - 1];
    const nameCell = lastRow.querySelector("td:first-child");

    // Create and append new plus icon
    const plusIcon = document.createElement("a");
    plusIcon.href = "#";
    plusIcon.className = "add-choice-link fa fa-plus";
    plusIcon.style.cssText =
      "text-decoration: none; color:#4caf50; margin-left:10px";
    plusIcon.setAttribute("data-variation-index", variationIndex);

    // Add event listener to the new plus icon
    plusIcon.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      addNewChoice.call(this, e);
    });

    nameCell.appendChild(plusIcon);
  }
}
// -------------------------- Media Management --------------------------
function initializeMediaButtons() {
  const addImageBtn = document.querySelector(".add-image-btn");
  if (addImageBtn) {
    addImageBtn.addEventListener("click", function () {
      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = "image/*";
      fileInput.style.display = "none";

      fileInput.addEventListener("change", function () {
        if (this.files && this.files[0]) {
          addNewImageForm(this.files[0]);
          addImageToList(
            this.files[0],
            document.querySelectorAll(".image-form").length - 1
          );
        }
      });

      document.body.appendChild(fileInput);
      fileInput.click();
      document.body.removeChild(fileInput);
    });
  }

  const addVideoBtn = document.querySelector(".add-video-btn");
  if (addVideoBtn) {
    addVideoBtn.addEventListener("click", function () {
      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = "video/*";
      fileInput.style.display = "none";

      fileInput.addEventListener("change", function () {
        if (this.files && this.files[0]) {
          addNewVideoForm(this.files[0]);
        }
      });

      document.body.appendChild(fileInput);
      fileInput.click();
      document.body.removeChild(fileInput);
    });
  }
}

function initializeExistingMediaHandlers() {
  document
    .querySelectorAll(".remove-media, .remove-image, .remove-video")
    .forEach((btn) => {
      btn.addEventListener("click", function () {
        const mediaForm = this.closest(".image-form, .video-form");
        const li = this.closest("li");

        if (mediaForm) {
          const deleteInput = mediaForm.querySelector('input[name$="-DELETE"]');
          if (deleteInput) {
            deleteInput.value = "on";
            mediaForm.style.display = "none";
          } else {
            const fileInput = mediaForm.querySelector('input[type="file"]');
            if (fileInput) {
              fileInput.value = "";
              const dataTransfer = new DataTransfer();
              fileInput.files = dataTransfer.files;
            }
            mediaForm.remove();
          }

          const formType = mediaForm.classList.contains("image-form")
            ? "images"
            : "videos";
          updateFormCount(formType);
        }

        if (li) {
          li.remove();
        }
      });
    });
}

function addImageToList(file, formIndex) {
  let imageList = document.getElementById("image-list");
  if (!imageList) {
    imageList = document.createElement("ul");
    imageList.id = "image-list";
    imageList.className = "image-list";
    const imageSection = document.querySelector(".main-photo-section");
    if (imageSection) {
      imageSection.appendChild(imageList);
    }
  }

  const li = createMediaListItem(file, formIndex, "image");
  imageList.appendChild(li);
}

function addVideoToList(file, formIndex) {
  let videoList = document.getElementById("video-list");
  if (!videoList) {
    videoList = document.createElement("ul");
    videoList.id = "video-list";
    videoList.className = "video-list";
    const videoSection = document.querySelector(".media-upload-section");
    if (videoSection) {
      videoSection.insertBefore(videoList, videoSection.firstChild);
    }
  }

  const li = createMediaListItem(file, formIndex, "video");
  videoList.appendChild(li);
}

function createMediaListItem(file, formIndex, type) {
  const li = document.createElement("li");
  li.dataset.formIndex = formIndex;
  li.className = "d-flex align-items-center p-2 mb-2";

  if (type === "video") {
    const videoIcon = document.createElement("i");
    videoIcon.className = "fa fa-video-camera mr-2";
    li.appendChild(videoIcon);
  }

  const fileNameSpan = document.createElement("span");
  fileNameSpan.className = "file-name flex-grow-1";
  fileNameSpan.textContent = file.name;
  li.appendChild(fileNameSpan);

  const sizeSpan = document.createElement("span");
  sizeSpan.className = "file-size mr-3";
  sizeSpan.textContent = formatFileSize(file.size);
  li.appendChild(sizeSpan);

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = `remove-${type} btn btn-link text-danger p-0 ml-2`;
  removeBtn.title = `Remove ${type}`;
  

  removeBtn.addEventListener("click", function () {
    handleMediaRemoval(type, formIndex, li);
  });

  li.appendChild(removeBtn);
  return li;
}

function handleMediaRemoval(type, formIndex, li) {
  const forms = document.querySelectorAll(`.${type}-form`);
  const form = forms[parseInt(formIndex)];

  if (form) {
    const deleteInput = form.querySelector('input[name$="-DELETE"]');
    if (deleteInput) {
      deleteInput.value = "on";
      form.style.display = "none";
    } else {
      const fileInput = form.querySelector('input[type="file"]');
      if (fileInput) {
        fileInput.value = "";
        const dataTransfer = new DataTransfer();
        fileInput.files = dataTransfer.files;
      }
      form.remove();
    }
  }

  li.remove();
  updateFormCount(type + "s");
}

function updateFormCount(type) {
  const container = document.getElementById(`${type}-container`);
  if (!container) return;

  const visibleForms = container.querySelectorAll(
    `.${type.slice(0, -1)}-form:not([style*="display: none"])`
  );
  const totalForms = document.querySelector(`[name="${type}-TOTAL_FORMS"]`);
  if (totalForms) {
    totalForms.value = visibleForms.length;
  }
}

function addNewImageForm(file) {
  const container = document.getElementById("images-container");
  if (!container) return;

  const formCount = container.querySelectorAll(".image-form").length;
  const totalForms = document.querySelector('[name="images-TOTAL_FORMS"]');
  const template = document.querySelector(".empty-form.image-form");

  if (template) {
    const newForm = template.cloneNode(true);
    newForm.classList.remove("empty-form");
    newForm.style.display = "block";
    newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, formCount);

    const fileInput = newForm.querySelector('input[type="file"]');
    if (fileInput) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
    }

    container.appendChild(newForm);

    if (totalForms) {
      totalForms.value = formCount + 1;
    }
  }
}

function addNewVideoForm(file) {
  const container = document.getElementById("videos-container");
  if (!container) return;

  const formCount = container.querySelectorAll(".video-form").length;
  const loadingItem = addLoadingIndicator(file);
  const template = document.querySelector(".empty-form.video-form");

  const newForm = template
    ? template.cloneNode(true)
    : createVideoForm(formCount);
  handleVideoUpload(file, formCount, newForm, container, loadingItem);
}

function createVideoForm(formCount) {
  const newForm = document.createElement("div");
  newForm.className = "video-form";
  newForm.innerHTML = `
    <input type="file" name="videos-${formCount}-video_file" id="id_videos-${formCount}-video_file">
    <input type="hidden" name="videos-${formCount}-id" id="id_videos-${formCount}-id">
  `;
  return newForm;
}

function addLoadingIndicator(file) {
  let videoList = document.getElementById("video-list");
  if (!videoList) {
    videoList = document.createElement("ul");
    videoList.id = "video-list";
    videoList.className = "video-list";
    const videoSection = document.querySelector(
      ".video-section, .media-upload-section"
    );
    if (videoSection) {
      videoSection.insertBefore(videoList, videoSection.firstChild);
    }
  }

  const li = document.createElement("li");
  li.dataset.fileName = file.name;
  li.className = "d-flex align-items-center p-2 mb-2 upload-progress-item";

  const videoIcon = document.createElement("i");
  videoIcon.className = "fa fa-video-camera mr-2";
  li.appendChild(videoIcon);

  const fileNameSpan = document.createElement("span");
  fileNameSpan.className = "file-name flex-grow-1";
  fileNameSpan.textContent = file.name;
  li.appendChild(fileNameSpan);

  const sizeSpan = document.createElement("span");
  sizeSpan.className = "file-size mr-3";
  sizeSpan.textContent = formatFileSize(file.size);
  li.appendChild(sizeSpan);

  const progressInfo = document.createElement("span");
  progressInfo.className = "progress-info mr-2";
  progressInfo.textContent = "0%";
  li.appendChild(progressInfo);

  const progressContainer = document.createElement("div");
  progressContainer.className = "progress mx-2";
  progressContainer.style.width = "200px";

  const progressBar = document.createElement("div");
  progressBar.className =
    "progress-bar progress-bar-striped progress-bar-animated";
  progressBar.role = "progressbar";
  progressBar.style.width = "0%";
  progressBar.setAttribute("aria-valuenow", "0");
  progressBar.setAttribute("aria-valuemin", "0");
  progressBar.setAttribute("aria-valuemax", "100");

  progressContainer.appendChild(progressBar);
  li.appendChild(progressContainer);

  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "btn btn-link text-danger p-0 ml-2 cancel-upload";
  cancelBtn.title = "Cancel upload";
  cancelBtn.innerHTML = '<i class="fa fa-times"></i>';
  cancelBtn.addEventListener("click", () => {
    if (activeUploads.has(file.name)) {
      const controller = activeUploads.get(file.name);
      controller.abort();
      activeUploads.delete(file.name);
    }
  });
  li.appendChild(cancelBtn);

  videoList.appendChild(li);
  return { progressBar, li, progressInfo };
}

function handleVideoUpload(file, formCount, newForm, container, loadingItem) {
  const totalForms = document.querySelector('[name="videos-TOTAL_FORMS"]');
  const fileInput = newForm.querySelector('input[type="file"]');

  if (fileInput) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    const formData = new FormData();
    formData.append(`videos-${formCount}-video_file`, file);
    formData.append(
      "csrfmiddlewaretoken",
      document.querySelector("[name=csrfmiddlewaretoken]").value
    );

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        const progress = (event.loaded / event.total) * 100;
        updateLoadingProgress(loadingItem.progressBar, progress);
      }
    });

    xhr.onload = function () {
      if (xhr.status === 200) {
        container.appendChild(newForm);
        if (totalForms) {
          totalForms.value = formCount + 1;
        }
        loadingItem.li.remove();
        addVideoToList(file, formCount);
        activeUploads.delete(file.name);
      } else {
        console.error("Upload failed");
        loadingItem.li.remove();
        showUploadMessage("Upload failed", "error");
      }
    };

    xhr.onerror = function () {
      console.error("Upload failed");
      loadingItem.li.remove();
      showUploadMessage("Upload failed", "error");
      activeUploads.delete(file.name);
    };

    const controller = {
      abort: () => {
        xhr.abort();
        loadingItem.li.remove();
        activeUploads.delete(file.name);
      },
    };
    activeUploads.set(file.name, controller);

    xhr.open("POST", window.location.pathname);
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    xhr.send(formData);
  }
}

function updateLoadingProgress(progressBar, progress) {
  progressBar.style.width = `${progress}%`;
  progressBar.setAttribute("aria-valuenow", progress);

  const li = progressBar.closest("li");
  const progressInfo = li.querySelector(".progress-info");
  if (progressInfo) {
    progressInfo.textContent = `${Math.round(progress)}%`;
  }
}

function showUploadMessage(message, type = "success") {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.role = "alert";
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

  const formContainer = document.querySelector(".form-container");
  if (formContainer) {
    formContainer.insertBefore(alertDiv, formContainer.firstChild);
  }

  setTimeout(() => {
    alertDiv.remove();
  }, 3000);
}

// Add these helper functions after showUploadMessage()
function handleUploadError(file, loadingItem) {
  console.error("Upload failed for:", file.name);
  loadingItem.li.remove();
  showUploadMessage(`Upload failed for ${file.name}`, "error");
  activeUploads.delete(file.name);
}

function handleUploadSuccess(
  file,
  formCount,
  newForm,
  container,
  loadingItem,
  totalForms
) {
  container.appendChild(newForm);
  if (totalForms) {
    totalForms.value = formCount + 1;
  }
  loadingItem.li.remove();
  addVideoToList(file, formCount);
  activeUploads.delete(file.name);
  showUploadMessage(`${file.name} uploaded successfully`, "success");
}
// Utility function for file size formatting
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
// -------------------------------- Styles --------------------------------
const styles = document.createElement("style");
styles.textContent = `
    .image-list, .video-list {
        list-style: none;
        padding: 0;
        margin-bottom: 1rem;
        background-color: #efefef;
    }
    .image-list li, .video-list li {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        background: #f0f0f0;
    }
    .fa-video-camera {
        color: #6c757d;
        font-size: 1.1em;
        flex-shrink: 0;
        width: 20px;
    }
    .file-name {
        flex-shrink: 1;
        color: #495057;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 100px;
        max-width: 200px;
    }
    .file-size {
        color: #6c757d;
        font-size: 0.875rem;
        white-space: nowrap;
        flex-shrink: 0;
        width: 70px;
    }
    .progress {
        height: 8px;
        background-color: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        width: 150px;
        flex-shrink: 0;
    }
    .progress-info {
        min-width: 46px;
        text-align: right;
        font-size: 0.875rem;
        color: #6c757d;
        flex-shrink: 0;
    }
    .remove-image, .remove-video, .cancel-upload {
        background: none;
        border: none;
        color: #dc3545;
        cursor: pointer;
        padding: 0.25rem;
        transition: color 0.15s ease-in-out;
        flex-shrink: 0;
        margin-left: auto;
        width: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }
    .remove-image:hover, .remove-video:hover, .cancel-upload:hover {
        color: #bd2130;
    }
    .progress-bar {
        background-color: #007bff;
        transition: width 0.2s ease;
    }
    .progress-bar-striped {
        background-image: linear-gradient(
            45deg,
            rgba(255,255,255,.15) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255,255,255,.15) 50%,
            rgba(255,255,255,.15) 75%,
            transparent 75%,
            transparent
        );
        background-size: 1rem 1rem;
    }
    .progress-bar-animated {
        animation: progress-bar-stripes 1s linear infinite;
    }
    @keyframes progress-bar-stripes {
        0% { background-position: 1rem 0; }
        100% { background-position: 0 0; }
    }
    .upload-progress-item {
        background: white !important;
        border: 1px solid #dee2e6;
        padding: 0.75rem !important;
    }
    .alert {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1050;
        min-width: 250px;
        box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
    }
    .alert-dismissible .close {
        position: absolute;
        top: 0;
        right: 0;
        padding: 0.75rem 1.25rem;
        color: inherit;
    }
`;
document.head.appendChild(styles);
