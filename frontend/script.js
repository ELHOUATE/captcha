let captchaId = null;
let selectedIndices = new Set();
let captchaValidated = false;

const checkbox = document.getElementById("checkbox");
const recaptchaBox = document.getElementById("recaptchaBox");
const captchaPopup = document.getElementById("captchaPopup");
const captchaGrid = document.getElementById("captchaGrid");
const targetClass = document.getElementById("targetClass");
const verifyBtn = document.getElementById("verifyBtn");
const refreshBtn = document.getElementById("refreshBtn");
const submitBtn = document.getElementById("submitBtn");
const errorMsg = document.getElementById("errorMsg");
const mainForm = document.getElementById("mainForm");

submitBtn.disabled = true;

recaptchaBox.addEventListener("click", () => {
  if (!captchaValidated) {
    openCaptcha();
  }
});

refreshBtn.addEventListener("click", openCaptcha);
verifyBtn.addEventListener("click", verifyCaptcha);

function resetCaptchaState() {
  captchaId = null;
  selectedIndices.clear();
  captchaValidated = false;

  checkbox.classList.remove("checked");
  submitBtn.disabled = true;

  captchaPopup.hidden = true;
  captchaGrid.innerHTML = "";
  targetClass.textContent = "Chargement...";
  errorMsg.textContent = "";
}

async function openCaptcha() {
  selectedIndices.clear();
  captchaGrid.innerHTML = "";
  errorMsg.textContent = "";

  captchaPopup.hidden = false;
  targetClass.textContent = "Chargement...";
  captchaGrid.innerHTML = "<div class='loading-text'>Chargement des images...</div>";

  try {
    const response = await fetch("http://localhost:8000/api/captcha/challenge");

    if (!response.ok) {
      throw new Error("Cannot load challenge");
    }

    const data = await response.json();

    captchaGrid.innerHTML = "";
    captchaId = data.id;

    targetClass.textContent =
      data.label_fr || data.target_class.replace("_", " ");

    captchaGrid.style.gridTemplateColumns =
      `repeat(${data.grid_size.cols}, 1fr)`;

    data.images.forEach((base64Image, index) => {
      const cell = document.createElement("div");
      cell.className = "captcha-cell";

      const img = document.createElement("img");
      img.src = "data:image/jpeg;base64," + base64Image;

      cell.appendChild(img);

      cell.addEventListener("click", () => {
        if (selectedIndices.has(index)) {
          selectedIndices.delete(index);
          cell.classList.remove("selected");
        } else {
          selectedIndices.add(index);
          cell.classList.add("selected");
        }
      });

      captchaGrid.appendChild(cell);
    });

  } catch (error) {
    captchaGrid.innerHTML = "";
    errorMsg.textContent =
      "Cannot load CAPTCHA. Check backend, models, or dataset.";
  }
}

async function verifyCaptcha() {
  if (!captchaId) {
    errorMsg.textContent = "CAPTCHA not loaded.";
    return;
  }

  try {
    const response = await fetch("http://localhost:8000/api/captcha/verify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        captcha_id: captchaId,
        selected_indices: Array.from(selectedIndices)
      })
    });

    const data = await response.json();

    if (data.success) {
      captchaValidated = true;
      captchaPopup.hidden = true;
      checkbox.classList.add("checked");
      submitBtn.disabled = false;
      errorMsg.textContent = "";
    } else {
      errorMsg.textContent =
        data.error || "CAPTCHA incorrect. Essayez encore.";

      openCaptcha();
    }

  } catch (error) {
    errorMsg.textContent =
      "Verification failed. Check backend.";
  }
}

mainForm.addEventListener("submit", function (e) {
  e.preventDefault();

  if (!captchaValidated) {
    alert("Veuillez valider le CAPTCHA avant de créer le compte.");
    openCaptcha();
    return;
  }

  alert("Utilisateur a été créé avec succès !");

  mainForm.reset();
  resetCaptchaState();
});