// Image upload management
function initializeImageUpload() {
  const addImageBtn = document.querySelector(".add-image-btn");
  if (!addImageBtn) {
    console.warn("Add image button not found");
    return;
  }

  addImageBtn.addEventListener("click", function () {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.multiple = true; // Allow multiple file selection
    fileInput.style.display = "none";

    fileInput.addEventListener("change", function () {
      if (this.files && this.files.length > 0) {
        Array.from(this.files).forEach((file) => {
          const formCount = document.querySelectorAll(".image-form").length;
          addNewImageForm(file, formCount);
          addImageToList(file, formCount);
        });
      }
    });

    document.body.appendChild(fileInput);
    fileInput.click();
    document.body.removeChild(fileInput);
  });
}

function addNewImageForm(file, formCount) {
  const container = document.getElementById("images-container");
  if (!container) {
    console.error("Images container not found");
    return;
  }

  const totalForms = document.querySelector('[name="images-TOTAL_FORMS"]');
  const template = document.querySelector(".empty-form.image-form");

  if (!template) {
    console.error("Image form template not found");
    return;
  }

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
    totalForms.value = parseInt(totalForms.value) + 1;
  }
}

function addImageToList(file, formIndex) {
  let imageList = document.getElementById("image-list");
  if (!imageList) {
    imageList = document.createElement("ul");
    imageList.id = "image-list";
    imageList.className = "image-list";
    const imageSection = document.querySelector(".additional-photos-section");
    if (imageSection) {
      imageSection.appendChild(imageList);
    }
  }

  const li = createImageListItem(file, formIndex);
  imageList.appendChild(li);
}

function createImageListItem(file, formIndex) {
  const li = document.createElement("li");
  li.dataset.formIndex = formIndex;
  li.className = "d-flex align-items-center p-2 mb-2";

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
  removeBtn.className = "remove-image btn btn-link text-danger p-0 ml-2";
  removeBtn.title = "Remove image";
  

  removeBtn.addEventListener("click", function () {
    handleMediaRemoval("image", formIndex, li);
  });

  li.appendChild(removeBtn);
  return li;
}

// Add this to your DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", function () {
  initializeImageUpload();
});
