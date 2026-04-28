const textarea = document.getElementById("rivescript");
const lineNumbers = document.getElementById("lineNumbers");
const chatBox = document.getElementById("chat-box");
const curriculumModules = Array.from(document.querySelectorAll(".curriculum-module"));
const progressValue = document.getElementById("progress-value");
const progressLabel = document.getElementById("progress-label");

function updateLineNumbers() {
  const lines = textarea.value.split("\n").length;
  lineNumbers.textContent = Array.from({ length: lines }, (_, i) => i + 1).join(
    "\n"
  );
}

textarea.addEventListener("input", updateLineNumbers);
textarea.addEventListener("scroll", () => {
  lineNumbers.scrollTop = textarea.scrollTop;
});

updateLineNumbers(); // Initial line numbers

function scrollChatToBottom() {
  if (!chatBox) {
    return;
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}

async function submitScriptAndFocusChat() {
  const messageInput = document.getElementById("message");

  const saved = await saveCurrentRiveScript();
  if (!saved) {
    return;
  }

  if (messageInput) {
    messageInput.focus();
  }
}

if (chatBox) {
  chatBox.addEventListener("htmx:afterSwap", scrollChatToBottom);
  scrollChatToBottom();
}

function updateProgressUi() {
  if (!curriculumModules.length || !progressValue || !progressLabel) {
    return;
  }

  const doneCount = curriculumModules.filter((module) =>
    module.classList.contains("curriculum-module-done")
  ).length;
  const percentage = Math.round((doneCount / curriculumModules.length) * 100);

  progressValue.style.width = `${percentage}%`;
  progressLabel.textContent = `${percentage}%`;
}

async function copyTemplateToClipboard(moduleElement) {
  const templateElement = moduleElement.querySelector(".curriculum-template");
  const copyButton = moduleElement.querySelector(".curriculum-copy-btn");
  if (!templateElement || !copyButton) {
    return;
  }

  const templateText = templateElement.innerText.trim();

  if (textarea) {
    textarea.value = templateText;
    textarea.dispatchEvent(new Event("input"));
    textarea.focus();
  }

  try {
    await navigator.clipboard.writeText(templateText);
    copyButton.textContent = "Copied to Editor";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1200);
  } catch (error) {
    copyButton.textContent = "Inserted";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1200);
  }
}

async function toggleModuleDone(moduleElement) {
  const moduleId = moduleElement.dataset.moduleId;
  const unitName = moduleElement.dataset.unitName || moduleId;
  const doneButton = moduleElement.querySelector(".curriculum-done-btn");
  const isDone = !moduleElement.classList.contains("curriculum-module-done");
  const status = isDone ? "done" : "in_progress";

  try {
    const formData = new FormData();
    formData.append("unit_id", moduleId);
    formData.append("unit_name", unitName);
    formData.append("status", status);

    const response = await fetch("/progress", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.message || "Gagal menyimpan progress.");
    }
  } catch (error) {
    alert("Gagal menyimpan progress ke server.");
    return;
  }

  moduleElement.classList.toggle("curriculum-module-done", isDone);

  if (doneButton) {
    doneButton.textContent = isDone ? "Done" : "Mark Done";
  }

  updateProgressUi();
}

curriculumModules.forEach((moduleElement) => {
  const copyButton = moduleElement.querySelector(".curriculum-copy-btn");
  const doneButton = moduleElement.querySelector(".curriculum-done-btn");

  if (copyButton) {
    copyButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      copyTemplateToClipboard(moduleElement);
    });
  }

  if (doneButton) {
    doneButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleModuleDone(moduleElement);
    });
  }
});

async function loadServerProgress() {
  try {
    const response = await fetch("/progress");
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      return;
    }

    curriculumModules.forEach((moduleElement) => {
      const doneButton = moduleElement.querySelector(".curriculum-done-btn");
      const status = payload.progress[moduleElement.dataset.moduleId];
      const isDone = status === "done";
      moduleElement.classList.toggle("curriculum-module-done", isDone);

      if (doneButton) {
        doneButton.textContent = isDone ? "Done" : "Mark Done";
      }
    });
    updateProgressUi();
  } catch (error) {
    console.error("Failed to load progress", error);
  }
}

loadServerProgress();
