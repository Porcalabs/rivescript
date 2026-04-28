const textarea = document.getElementById("rivescript");
const lineNumbers = document.getElementById("lineNumbers");

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
