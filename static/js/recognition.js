let recognition;

function startListening() {
  if (!("webkitSpeechRecognition" in window)) {
    alert("Browser tidak mendukung speech recognition. Gunakan Chrome.");
    return;
  }

  if (!recognition) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "id-ID";
    // recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function (event) {
      const text = event.results[0][0].transcript;
      document.getElementById("message").value = text;
      document.getElementById("chat-form").requestSubmit();
    };

    recognition.onerror = function (event) {
      alert("Terjadi kesalahan: " + event.error);
    };

    recognition.onstart = () => {
      sendBtn.disabled = true;
      micBtn.disabled = true;
    };

    recognition.onend = () => {
      sendBtn.disabled = false;
      micBtn.disabled = false;
    };
  }

  recognition.start();
}
