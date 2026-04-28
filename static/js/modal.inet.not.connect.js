// Inisialisasi Bootstrap Modal
const infoModal = new bootstrap.Modal(document.getElementById("infoModal"));
const modalMessage = document.getElementById("modalMessage");

// Tampilkan modal saat form disubmit
document.querySelector("form").addEventListener("submit", function (e) {
  // Cek status koneksi internet
  if (!navigator.onLine) {
    e.preventDefault(); // Hentikan pengiriman form
    modalMessage.innerText =
      "Koneksi internet terputus. Silakan periksa koneksi Anda.";
    infoModal.show();
  }
});

// Tambahan: Event listener untuk perubahan status koneksi
window.addEventListener("offline", () => {
  modalMessage.innerText =
    "Anda sedang offline. Beberapa fitur mungkin tidak tersedia.";
  infoModal.show();
});
