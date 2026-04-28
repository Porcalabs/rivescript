const form = document.getElementById("chat-form");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");

// Handle Send Button
form.addEventListener("submit", async function (e) {
  // Cegah submit jika tombol sedang disable
  if (sendBtn.disabled || micBtn.disabled) {
    e.preventDefault();
    return;
  }

  if (typeof isScriptDirty !== "undefined" && isScriptDirty) {
    e.preventDefault();
    const saved = await saveCurrentRiveScript();
    if (!saved) {
      return;
    }
    form.requestSubmit();
    return;
  }

  sendBtn.disabled = true;
  micBtn.disabled = true;

  setTimeout(() => {
    sendBtn.disabled = false;
    micBtn.disabled = false;
  }, 5000); // 5 detik
});
