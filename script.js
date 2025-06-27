// Form Kalori
document.getElementById('calorieForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  const res = await fetch('/calorie_needs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const result = await res.json();
  document.getElementById('result-calorie').innerText = `Kebutuhan kalori: ${result.calorie_needs} kcal`;
});

// Form Prediksi Makanan
document.getElementById('predictForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const res = await fetch('/predict_food', {
    method: 'POST',
    body: formData
  });
  const result = await res.json();
  document.getElementById('result-predict').innerText = `Makanan: ${result.nama_makanan}, Sehat: ${result.status_sehat}`;
});

// Form Status Hewan
document.getElementById('statusForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  const res = await fetch('/pet_status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const result = await res.json();
  document.getElementById('result-status').innerText = `Status: ${result.status}`;
});
