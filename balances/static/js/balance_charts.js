// Кольори для культур (яскрава палітра)
const cultureColors = {};
const colorPalette = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
  '#6366f1', '#a855f7', '#22c55e', '#eab308', '#f43f5e'
];

// Кольори для складів (більш спокійна палітра для нового графіка)
const warehousePalette = [
  '#475569', '#64748b', '#94a3b8', '#334155', '#1e293b', 
  '#0f172a', '#cbd5e1', '#57534e', '#78716c', '#a8a29e'
];

let colorIndex = 0;
function getColorForCulture(culture) {
  if (!cultureColors[culture]) {
    cultureColors[culture] = colorPalette[colorIndex % colorPalette.length];
    colorIndex++;
  }
  return cultureColors[culture];
}

let stackedBarChart, pieChart, horizontalBarChart, warehouseShareChart;
let activePlaceFilters = []; 

// 1. Обчислення статистики
function calculateStats() {
  if (typeof balancesData === 'undefined' || balancesData.length === 0) return;

  let totalGrain = 0;
  let totalWaste = 0;

  balancesData.forEach(b => {
    const qty = parseFloat(b.quantity);
    if (b.balanceType === 'stock') {
      totalGrain += qty;
    } else if (b.balanceType === 'waste') {
      totalWaste += qty;
    }
  });

  const grandTotal = totalGrain + totalWaste;

  // Використовуємо toLocaleString для кращого формату, якщо доступно
  const formatNumber = (num) => num.toLocaleString('uk-UA', {minimumFractionDigits: 3, maximumFractionDigits: 3});

  document.getElementById('grandTotal').innerHTML = formatNumber(grandTotal) + '<span class="mini-stat-suffix">т</span>';
  document.getElementById('totalGrain').innerHTML = formatNumber(totalGrain) + '<span class="mini-stat-suffix">т</span>';
  document.getElementById('totalWaste').innerHTML = formatNumber(totalWaste) + '<span class="mini-stat-suffix">т</span>';
}

function initCharts() {
  if (typeof balancesData === 'undefined' || balancesData.length === 0) return;

  const uniquePlaces = [...new Set(balancesData.map(b => b.place))].sort();
  activePlaceFilters = [...uniquePlaces];

  initStackedBarChart(uniquePlaces);
  initPieChart(uniquePlaces);
  initHorizontalBarChart();
  initWarehouseShareChart();
}

// ---------------------------------------------------------
// Chart 1: Stacked Bar Chart (з красивими "чіпами")
// ---------------------------------------------------------
function initStackedBarChart(uniquePlaces) {
  const canvas = document.getElementById('stackedBarChart');
  if (!canvas) return; // Захист від помилок
  const ctx = canvas.getContext('2d');
  
  renderPlaceChips(uniquePlaces);

  document.getElementById('showGrain').addEventListener('change', updateStackedBarChart);
  document.getElementById('showWaste').addEventListener('change', updateStackedBarChart);

  stackedBarChart = new Chart(ctx, {
    type: 'bar',
    data: getStackedBarData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', align: 'end' },
        tooltip: {
          callbacks: {
            label: function(context) { return ' ' + context.dataset.label + ': ' + context.parsed.y.toFixed(3) + ' т'; }
          }
        }
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, title: { display: true, text: 'Вага (т)' } }
      }
    }
  });
}

// Допоміжна функція для створення кнопок-чіпів
function renderPlaceChips(places) {
  const container = document.getElementById('placeChipsContainer');
  if (!container) return; // Захист
  container.innerHTML = '';
  
  // 1. Кнопка "Вибрати всі"
  const allBtn = document.createElement('div');
  allBtn.className = 'filter-chip active';
  allBtn.textContent = 'Всі склади';
  
  // Додаємо логіку вибору/зняття вибору
  const toggleAllChips = (isActivating) => {
    const chips = document.querySelectorAll('#placeChipsContainer .filter-chip:not(:first-child)');
    chips.forEach(chip => {
      if (isActivating) chip.classList.add('active');
      else chip.classList.remove('active');
    });
    // Оновлюємо фільтри та графік
    updateActiveFilters();
    updateStackedBarChart();
  };

  allBtn.onclick = () => {
    const isActivating = !allBtn.classList.contains('active');
    allBtn.classList.toggle('active');
    allBtn.textContent = isActivating ? 'Всі склади' : 'Зняти вибір';
    toggleAllChips(isActivating);
  };
  container.appendChild(allBtn);

  // 2. Чіпи для складів
  places.forEach(place => {
    const chip = document.createElement('div');
    chip.className = 'filter-chip active';
    chip.textContent = place;
    chip.dataset.value = place;
    chip.onclick = function() {
      this.classList.toggle('active');
      
      if (!this.classList.contains('active')) {
        allBtn.classList.remove('active');
        allBtn.textContent = 'Вибрати всі';
      } else {
        // Якщо всі активні, активуємо "Всі склади"
        const allActive = Array.from(document.querySelectorAll('#placeChipsContainer .filter-chip:not(:first-child)')).every(c => c.classList.contains('active'));
        if (allActive) {
           allBtn.classList.add('active');
           allBtn.textContent = 'Всі склади';
        }
      }
      
      updateActiveFilters();
      updateStackedBarChart();
    };
    container.appendChild(chip);
  });
}

function updateActiveFilters() {
  const chips = document.querySelectorAll('#placeChipsContainer .filter-chip:not(:first-child)');
  activePlaceFilters = [];
  chips.forEach(chip => {
    if (chip.classList.contains('active')) {
      activePlaceFilters.push(chip.dataset.value);
    }
  });
  // Якщо фільтри порожні, залишаємо пустий масив, Chart.js коректно відобразить це.
}

function getStackedBarData() {
  const showGrain = document.getElementById('showGrain').checked;
  const showWaste = document.getElementById('showWaste').checked;

  const filteredData = balancesData.filter(b => activePlaceFilters.includes(b.place));
  const cultures = [...new Set(filteredData.map(b => b.culture))];

  const datasets = [];

  // ... (логіка формування датасетів залишається без змін) ...
  cultures.forEach(culture => {
    if (showGrain) {
      const grainData = activePlaceFilters.map(place => {
        const item = filteredData.find(b => b.place === place && b.culture === culture && b.balanceType === 'stock');
        return item ? parseFloat(item.quantity) : 0;
      });
      if (grainData.some(v => v > 0)) {
        datasets.push({ label: culture, data: grainData, backgroundColor: getColorForCulture(culture), stack: 'grain' });
      }
    }

    if (showWaste) {
      const wasteData = activePlaceFilters.map(place => {
        const item = filteredData.find(b => b.place === place && b.culture === culture && b.balanceType === 'waste');
        return item ? parseFloat(item.quantity) : 0;
      });
      if (wasteData.some(v => v > 0)) {
        datasets.push({ label: culture + ' (Відх.)', data: wasteData, backgroundColor: getColorForCulture(culture) + '66', borderColor: getColorForCulture(culture), borderWidth: 1, stack: 'waste' });
      }
    }
  });

  return { labels: activePlaceFilters, datasets: datasets };
}

function updateStackedBarChart() {
  stackedBarChart.data = getStackedBarData();
  stackedBarChart.update();
}

// ---------------------------------------------------------
// Chart 2: Pie Chart (з фільтром складів)
// ---------------------------------------------------------
function initPieChart(uniquePlaces) {
  const canvas = document.getElementById('pieChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  const placeSelect = document.getElementById('piePlaceSelect');
  uniquePlaces.forEach(place => {
    const opt = document.createElement('option');
    opt.value = place;
    opt.textContent = place;
    placeSelect.appendChild(opt);
  });

  document.getElementById('pieTypeSelect').addEventListener('change', updatePieChart);
  document.getElementById('piePlaceSelect').addEventListener('change', updatePieChart);

  pieChart = new Chart(ctx, {
    type: 'pie',
    data: getPieChartData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right' },
        tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const pct = ((val / total) * 100).toFixed(1);
                return ` ${context.label}: ${val.toFixed(3)} т (${pct}%)`;
              }
            }
        }
      }
    }
  });
}

function getPieChartData() {
  const typeFilter = document.getElementById('pieTypeSelect').value;
  const placeFilter = document.getElementById('piePlaceSelect').value;
  
  let filteredData = balancesData;

  if (typeFilter === 'stock') filteredData = filteredData.filter(b => b.balanceType === 'stock');
  else if (typeFilter === 'waste') filteredData = filteredData.filter(b => b.balanceType === 'waste');

  if (placeFilter !== 'all') {
    filteredData = filteredData.filter(b => b.place === placeFilter);
  }

  const cultureData = {};
  filteredData.forEach(b => {
    if (!cultureData[b.culture]) cultureData[b.culture] = 0;
    cultureData[b.culture] += parseFloat(b.quantity);
  });

  const labels = Object.keys(cultureData);
  const data = Object.values(cultureData);
  const colors = labels.map(l => getColorForCulture(l));

  if (data.length === 0) {
     return { labels: ['Немає даних'], datasets: [{ data: [1], backgroundColor: ['#e2e8f0'], borderWidth: 0 }] };
  }

  return { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderWidth: 1 }] };
}

function updatePieChart() {
  pieChart.data = getPieChartData();
  pieChart.update();
}

// ---------------------------------------------------------
// Chart 3: Horizontal Bar ("Професійний/Бухгалтерський")
// ---------------------------------------------------------
function initHorizontalBarChart() {
  const canvas = document.getElementById('horizontalBarChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  document.getElementById('topCulturesCount').addEventListener('change', updateHorizontalBarChart);
  document.getElementById('topCulturesType').addEventListener('change', updateHorizontalBarChart);

  horizontalBarChart = new Chart(ctx, {
    type: 'bar',
    data: getHorizontalBarData(),
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { family: 'Arial', size: 13 },
          bodyFont: { family: 'Courier New', size: 13 },
          callbacks: {
            label: function(context) { return ' Обсяг: ' + context.parsed.x.toFixed(3) + ' т'; }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: { font: { size: 11 } }
        },
        y: {
          grid: { display: false },
          ticks: { font: { weight: 'bold', size: 12 } }
        }
      }
    }
  });
}

function getHorizontalBarData() {
  const count = document.getElementById('topCulturesCount').value;
  const type = document.getElementById('topCulturesType').value;

  let filteredData = balancesData;
  if (type === 'stock') filteredData = balancesData.filter(b => b.balanceType === 'stock');
  else if (type === 'waste') filteredData = balancesData.filter(b => b.balanceType === 'waste');

  const cultureData = {};
  filteredData.forEach(b => {
    if (!cultureData[b.culture]) cultureData[b.culture] = 0;
    cultureData[b.culture] += parseFloat(b.quantity);
  });

  let sorted = Object.entries(cultureData).sort((a, b) => b[1] - a[1]);
  if (count !== 'all') sorted = sorted.slice(0, parseInt(count));

  const labels = sorted.map(s => s[0]);
  const data = sorted.map(s => s[1]);
  // FIX: Створюємо масив кольорів для кожного бара
  const colors = labels.map(() => '#3b82f6'); 

  return {
    labels: labels,
    datasets: [{
      data: data,
      backgroundColor: colors,
      borderRadius: 4,
      barPercentage: 0.7
    }]
  };
}

function updateHorizontalBarChart() {
  horizontalBarChart.data = getHorizontalBarData();
  horizontalBarChart.update();
}

// ---------------------------------------------------------
// Chart 4: NEW CHART (Warehouse Share - Doughnut)
// ---------------------------------------------------------
function initWarehouseShareChart() {
  const canvas = document.getElementById('warehouseShareChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  warehouseShareChart = new Chart(ctx, {
    type: 'doughnut',
    data: getWarehouseShareData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: { position: 'left', labels: { boxWidth: 15, font: { size: 11 } } },
        tooltip: {
            callbacks: {
                label: function(context) {
                    const val = context.parsed;
                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                    const pct = ((val / total) * 100).toFixed(1);
                    return ` ${context.label}: ${val.toFixed(2)} т (${pct}%)`;
                }
            }
        }
      }
    }
  });
}

function getWarehouseShareData() {
    const placeData = {};
    
    balancesData.forEach(b => {
        if (!placeData[b.place]) placeData[b.place] = 0;
        placeData[b.place] += parseFloat(b.quantity);
    });

    const labels = Object.keys(placeData);
    const data = Object.values(placeData);
    const colors = labels.map((_, i) => warehousePalette[i % warehousePalette.length]);

    if (data.length === 0) {
        return { labels: ['Немає даних'], datasets: [{ data: [1], backgroundColor: ['#e2e8f0'], hoverOffset: 0 }] };
    }

    return {
        labels: labels,
        datasets: [{
            data: data,
            backgroundColor: colors,
            hoverOffset: 4
        }]
    };
}

// Toggle logic
function toggleCharts() {
  const chartsContent = document.getElementById('chartsContent');
  const toggleIcon = document.getElementById('toggleIcon');
  const toggleText = document.getElementById('toggleText');
  
  if (chartsContent.style.display === 'none') {
    chartsContent.style.display = 'grid';
    toggleIcon.textContent = '👁️';
    toggleText.textContent = 'Сховати графіки';
  } else {
    chartsContent.style.display = 'none';
    toggleIcon.textContent = '👁️‍🗨️';
    toggleText.textContent = 'Показати графіки';
  }
}

// Ініціалізація на завантаження сторінки
document.addEventListener('DOMContentLoaded', function() {
  if (typeof balancesData !== 'undefined' && balancesData.length > 0) {
    calculateStats();
    initCharts();
  } else {
      // Якщо дані порожні, це може бути порожній екран,
      // але ми намагаємося ініціалізувати статистику
      if (document.getElementById('grandTotal')) {
        document.getElementById('grandTotal').innerHTML = '0.000<span class="mini-stat-suffix">т</span>';
        document.getElementById('totalGrain').innerHTML = '0.000<span class="mini-stat-suffix">т</span>';
        document.getElementById('totalWaste').innerHTML = '0.000<span class="mini-stat-suffix">т</span>';
      }
  }
});