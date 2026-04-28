const textarea = document.getElementById("rivescript");
const lineNumbers = document.getElementById("lineNumbers");
const chatBox = document.getElementById("chat-box");
const curriculumModules = Array.from(document.querySelectorAll(".curriculum-module"));
const progressValue = document.getElementById("progress-value");
const progressLabel = document.getElementById("progress-label");
const curriculumStorageKey = "rivescript-curriculum-progress";

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

function loadCurriculumProgress() {
  try {
    return JSON.parse(localStorage.getItem(curriculumStorageKey) || "{}");
  } catch (error) {
    return {};
  }
}

function saveCurriculumProgress(progress) {
  localStorage.setItem(curriculumStorageKey, JSON.stringify(progress));
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

  try {
    await navigator.clipboard.writeText(templateText);
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1200);
  } catch (error) {
    if (textarea) {
      textarea.value = templateText;
      textarea.dispatchEvent(new Event("input"));
      textarea.focus();
    }
    copyButton.textContent = "Inserted";
    setTimeout(() => {
      copyButton.textContent = "Copy";
    }, 1200);
  }
}

function toggleModuleDone(moduleElement) {
  const progress = loadCurriculumProgress();
  const moduleId = moduleElement.dataset.moduleId;
  const doneButton = moduleElement.querySelector(".curriculum-done-btn");
  const isDone = !moduleElement.classList.contains("curriculum-module-done");

  moduleElement.classList.toggle("curriculum-module-done", isDone);
  progress[moduleId] = isDone;
  saveCurriculumProgress(progress);

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

const savedProgress = loadCurriculumProgress();
curriculumModules.forEach((moduleElement) => {
  const isDone = Boolean(savedProgress[moduleElement.dataset.moduleId]);
  const doneButton = moduleElement.querySelector(".curriculum-done-btn");
  moduleElement.classList.toggle("curriculum-module-done", isDone);

  if (doneButton) {
    doneButton.textContent = isDone ? "Done" : "Mark Done";
  }
});

updateProgressUi();
