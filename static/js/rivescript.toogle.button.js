// function toggleEditMode() {
//   const textarea = document.getElementById("rivescript");
//   const button = document.getElementById("edit-save-btn");
//   const form = document.getElementById("rivescript-form");

//   if (textarea.disabled) {
//     textarea.disabled = false;
//     button.textContent = "Save";
//     // button.type = "submit";
//     button.classList.remove("btn-warning");
//     button.classList.add("btn-primary");
//   } else if (!textarea.disabled) {
//     form.requestSubmit();
//     textarea.disabled = true;
//     button.textContent = "Edit";
//     button.classList.remove("btn-primary");
//     button.classList.add("btn-warning");
//   }
// }

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
      // Skip komentar/kosong
      continue;
    }

    // Cek awalan valid
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

    // Validasi tanda ' hanya boleh pada baris yang dimulai dengan -
    if (line.includes("'") && !line.startsWith("-")) {
      isValid = false;
      errorMessage = `Baris ${
        i + 1
      } mengandung tanda (') yang tidak diperbolehkan kecuali di baris jawaban (yang diawali dengan "-").\nIsi: "${lineRaw}"`;
      break;
    }

    // Track trigger dan respon
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

  // Cek trigger terakhir punya respon
  if (isValid && lastTriggerLine !== -1 && !hasResponseForTrigger) {
    isValid = false;
    errorMessage = `Baris ${
      lastTriggerLine + 1
    } (trigger) tidak memiliki respon (baris dengan "-").`;
  }

  return { isValid, errorMessage };
}

// Fungsi untuk menampilkan modal error validasi
function showModal(message) {
  const modalMessage = document.getElementById("rivescriptErrorMessage");
  if (!modalMessage) {
    console.error("Modal element with id 'rivescriptErrorMessage' not found.");
    alert(message); // fallback alert jika modal tidak ada
    return;
  }
  modalMessage.textContent = message;

  const modalElement = document.getElementById("rivescriptErrorModal");
  if (!modalElement) {
    console.error("Modal element with id 'rivescriptErrorModal' not found.");
    alert(message);
    return;
  }

  const modal = new bootstrap.Modal(modalElement);
  modal.show();
}

// Fungsi toggle edit/save dengan validasi
function toggleEditMode() {
  const textarea = document.getElementById("rivescript");
  const button = document.getElementById("edit-save-btn");
  const form = document.getElementById("rivescript-form");

  if (textarea.disabled) {
    // Masuk mode edit
    textarea.disabled = false;
    button.textContent = "Save";
    button.classList.remove("btn-warning");
    button.classList.add("btn-primary");
  } else {
    // Mode save → validasi dulu
    const content = textarea.value;
    const validation = validateRiveScript(content);

    if (!validation.isValid) {
      showModal(validation.errorMessage);
      return;
    }

    // Jika valid, submit form dan kunci textarea
    form.requestSubmit();
    textarea.disabled = true;
    button.textContent = "Edit";
    button.classList.remove("btn-primary");
    button.classList.add("btn-warning");
  }
}
