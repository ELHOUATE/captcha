let captchaId = null;
let selectedIndices = new Set();

const checkbox = document.getElementById("checkbox");
const recaptchaBox = document.getElementById("recaptchaBox");
const captchaPopup = document.getElementById("captchaPopup");
const captchaGrid = document.getElementById("captchaGrid");
const targetClass = document.getElementById("targetClass");
const verifyBtn = document.getElementById("verifyBtn");
const refreshBtn = document.getElementById("refreshBtn");
const submitBtn = document.getElementById("submitBtn");
const errorMsg = document.getElementById("errorMsg");

recaptchaBox.addEventListener("click", openCaptcha);
refreshBtn.addEventListener("click", openCaptcha);
verifyBtn.addEventListener("click", verifyCaptcha);

async function openCaptcha() {
  selectedIndices.clear();
  captchaGrid.innerHTML = "";
  errorMsg.textContent = "";
  captchaPopup.hidden = false;

  try {
    const response = await fetch("http://localhost:8000/api/captcha/challenge");

    if (!response.ok) {
      throw new Error("Cannot load challenge");
    }

    const data = await response.json();

    captchaId = data.id;
    targetClass.textContent = data.label_fr || data.target_class.replace("_", " ");

    captchaGrid.style.gridTemplateColumns = `repeat(${data.grid_size.cols}, 1fr)`;
    captchaGrid.dataset.type = data.type;

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
    errorMsg.textContent = "Cannot load CAPTCHA. Check backend, models, or dataset.";
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
      captchaPopup.hidden = true;
      checkbox.classList.add("checked");
      submitBtn.disabled = false;
    } else {
      errorMsg.textContent = data.error || "Please try again.";
      openCaptcha();
    }

  } catch (error) {
    errorMsg.textContent = "Verification failed. Check backend.";
  }
}

document.getElementById("mainForm").addEventListener("submit", function (e) {
  e.preventDefault();
  alert("Form submitted successfully!");
});