document.addEventListener("DOMContentLoaded", () => {
  let chart = null;

  function updateSummary() {
    const calText = document.getElementById("calorie-result").textContent;
    const foodText = document.getElementById("food-result").textContent;
    const petText = document.getElementById("pet-result").textContent;

    const hasil = [calText, foodText, petText].filter(Boolean).join(". ");
    document.getElementById("summary-result").textContent = hasil || "...";

    updateChart(calText, foodText, petText);
  }

  function updateChart(calText, foodText, petText) {
    const labels = [];
    const data = [];

    // Ambil angka dari kalori
    const calMatch = calText.match(/(\d+(\.\d+)?)/);
    if (calMatch) {
      labels.push("Kalori");
      data.push(parseFloat(calMatch[1]));
    }

    // Ambil confidence (%) dari prediksi makanan
    const foodMatch = foodText.match(/\((\d+)%\)/);
    if (foodMatch) {
      labels.push("Confidence Makanan");
      data.push(parseFloat(foodMatch[1]));
    }

    // Ubah status hewan ke skor numerik (demo visual)
    if (petText.includes("Sehat")) {
      labels.push("Status Hewan");
      data.push(100);
    } else if (petText.includes("Perlu perhatian")) {
      labels.push("Status Hewan");
      data.push(50);
    }

    const canvas = document.getElementById("nutritionChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Ringkasan",
          data,
          backgroundColor: ["#34d399", "#60a5fa", "#fbbf24"],
        }],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 1000,
          },
        },
      },
    });
  }

  // Form kalori
  document.getElementById("calorie-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const age = +document.getElementById("age").value;
    const weight = +document.getElementById("weight").value;
    const height = +document.getElementById("height").value;

    fetch("/calorie_needs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age, weight, height }),
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("calorie-result").textContent =
          `Kebutuhan kalori harian: ${data.calorie_needs} kkal`;
        updateSummary();
      })
      .catch(() => {
        document.getElementById("calorie-result").textContent =
          "Gagal menghitung kalori.";
      });
  });

  // Form klasifikasi makanan
  document.getElementById("food-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const input = document.getElementById("food-image");
    if (!input.files.length) {
      document.getElementById("food-result").textContent = "Silakan unggah gambar terlebih dahulu.";
      return;
    }

    const formData = new FormData();
    formData.append("image", input.files[0]);

    fetch("/predict_food", {
      method: "POST",
      body: formData,
    })
      .then(res => {
        if (!res.ok) throw new Error("Server error");
        return res.json();
      })
      .then(data => {
        document.getElementById("food-result").textContent =
          `Makanan terdeteksi: ${data.nama_makanan} (${Math.round(data.confidence * 100)}%), Status: ${data.status_sehat ? "Sehat" : "Tidak Sehat"}`;
        updateSummary();
      })
      .catch(() => {
        document.getElementById("food-result").textContent = "Gagal mengklasifikasikan gambar.";
      });
  });

  // Form status hewan
  document.getElementById("pet-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const last_meal_hours = +document.getElementById("last-meal").value;
    const healthy_food_score = +document.getElementById("healthy-score").value;

    fetch("/pet_status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ last_meal_hours, healthy_food_score }),
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("pet-result").textContent =
          `Status hewan peliharaan: ${data.status}`;
        updateSummary();
      })
      .catch(() => {
        document.getElementById("pet-result").textContent = "Gagal memeriksa status.";
      });
  });
});
