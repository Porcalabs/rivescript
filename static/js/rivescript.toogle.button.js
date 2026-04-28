const rivescriptTextarea = document.getElementById("rivescript");
const rivescriptForm = document.getElementById("rivescript-form");
const saveScriptBtn = document.getElementById("save-script-btn");
let isScriptDirty = false;

// Fungsi validasi RiveScript
function validateRiveScript(content) {
  const lines = content.split("\n");
  const validStarters = ["+", "-", "*", ">", "<", "!", "^", "%", "@"];

  let isValid = true;
  let errorMessage = "";
  let lastTriggerLine = -1;
  let hasResponseForTrigger = false;

  for (let i = 0; i < lines.length; i++) {
    const lineRaw = lines[i];
    const line = lineRaw.trim();

    if (line === "" || line.startsWith("//")) {
      continue;
    }

    const startsValid = validStarters.some((prefix) => line.startsWith(prefix));
    if (!startsValid) {
      isValid = false;
      errorMessage = `Baris ${
        i + 1
      } tidak valid: harus diawali dengan salah satu dari ${validStarters.join(
        " "
      )}\nIsi: "${lineRaw}"`;
      break;
    }

    if (line.includes("'") && !line.startsWith("-")) {
      isValid = false;
      errorMessage = `Baris ${
        i + 1
      } mengandung tanda (') yang tidak diperbolehkan kecuali di baris jawaban (yang diawali dengan "-").\nIsi: "${lineRaw}"`;
      break;
    }

    if (line.startsWith("+")) {
      if (lastTriggerLine !== -1 && !hasResponseForTrigger) {
        isValid = false;
        errorMessage = `Baris ${
          lastTriggerLine + 1
        } (trigger) tidak memiliki respon (baris dengan "-").`;
        break;
      }
      lastTriggerLine = i;
      hasResponseForTrigger = false;
    } else if (line.startsWith("-")) {
      if (lastTriggerLine === -1) {
        isValid = false;
        errorMessage = `Baris ${i + 1} adalah respon tanpa trigger sebelumnya.`;
        break;
      }
      hasResponseForTrigger = true;
    }
  }

  if (isValid && lastTriggerLine !== -1 && !hasResponseForTrigger) {
    isValid = false;
    errorMessage = `Baris ${
      lastTriggerLine + 1
    } (trigger) tidak memiliki respon (baris dengan "-").`;
  }

  return { isValid, errorMessage };
}

function showModal(message) {
  const modalMessage = document.getElementById("rivescriptErrorMessage");
  if (!modalMessage) {
    alert(message);
    return;
  }

  modalMessage.textContent = message;
  const modalElement = document.getElementById("rivescriptErrorModal");
  if (!modalElement) {
    alert(message);
    return;
  }

  const modal = new bootstrap.Modal(modalElement);
  modal.show();
}

function updateSaveButtonState() {
  if (!saveScriptBtn) {
    return;
  }

  saveScriptBtn.classList.toggle("btn-warning", isScriptDirty);
  saveScriptBtn.classList.toggle("btn-light", !isScriptDirty);
}

async function saveCurrentRiveScript() {
  if (!rivescriptTextarea || !rivescriptForm) {
    return false;
  }

  const content = rivescriptTextarea.value;
  const validation = validateRiveScript(content);

  if (!validation.isValid) {
    showModal(validation.errorMessage);
    return false;
  }

  const formData = new FormData();
  formData.append("rivescript", content);

  try {
    const response = await fetch("/set-rivescript", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      showModal(payload.message || "Gagal menerapkan RiveScript.");
      return false;
    }

    isScriptDirty = false;
    updateSaveButtonState();
    return true;
  } catch (error) {
    showModal("Gagal menghubungi server untuk menerapkan RiveScript.");
    return false;
  }
}

if (rivescriptTextarea) {
  rivescriptTextarea.addEventListener("input", () => {
    isScriptDirty = true;
    updateSaveButtonState();
  });
}

updateSaveButtonState();
