<script>
  import { onMount } from 'svelte';
  import {
    Chart as ChartJS, Title, Tooltip, Legend, BarElement, 
    CategoryScale, LinearScale, LineElement, PointElement, ArcElement
  } from 'chart.js';
  import { Bar, Line, Doughnut } from 'svelte-chartjs';

  ChartJS.register(
    Title, Tooltip, Legend, BarElement, CategoryScale, 
    LinearScale, LineElement, PointElement, ArcElement
  );

  let pgcbData = [];
  let bpdbData = [];
  let loading = true;
  let error = null;
  let isDarkMode = false;

  let generationChartData = { labels: [], datasets: [] };
  let capacityChartData = { labels: [], datasets: [] };
  let fuelMixChartData = { labels: [], datasets: [] };

  // Insights
  let currentGen = 0;
  let maxGen24h = 0;
  let avgGen24h = 0;
  
  // Loadshedding
  let totalPresentCapacity = 0;
  let loadSheddingProb = 0; 
  let loadSheddingStatus = "Low";
  let loadSheddingColor = "var(--success-color)";

  function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    ChartJS.defaults.color = isDarkMode ? '#94a3b8' : '#64748b';
    ChartJS.defaults.borderColor = isDarkMode ? '#334155' : '#e2e8f0';
    // Trigger reactivity to re-render charts with new theme
    generationChartData = { ...generationChartData };
    capacityChartData = { ...capacityChartData };
    fuelMixChartData = { ...fuelMixChartData };
  }

  onMount(async () => {
    // Check system preference for dark mode
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      isDarkMode = true;
      document.documentElement.setAttribute('data-theme', 'dark');
      ChartJS.defaults.color = '#94a3b8';
      ChartJS.defaults.borderColor = '#334155';
    }

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';
      const [pgcbRes, bpdbRes] = await Promise.all([
        fetch(`${API_URL}/api/generation`),
        fetch(`${API_URL}/api/daily-generation`)
      ]);

      if (!pgcbRes.ok || !bpdbRes.ok) throw new Error('Failed to fetch data');

      let rawPgcb = await pgcbRes.json();
      let rawBpdb = await bpdbRes.json();
      
      pgcbData = rawPgcb.reverse();
      bpdbData = rawBpdb;

      if (pgcbData.length > 0) {
        const latest = pgcbData[pgcbData.length - 1];
        currentGen = latest.generation_mw;
        
        let sum = 0;
        let max = 0;
        pgcbData.forEach(d => {
          sum += d.generation_mw;
          if (d.generation_mw > max) max = d.generation_mw;
        });
        avgGen24h = Math.round(sum / pgcbData.length);
        maxGen24h = max;

        // Fuel Mix Doughnut
        fuelMixChartData = {
          labels: ['Gas', 'Liquid Fuel', 'Coal', 'Hydro', 'Solar', 'Imports'],
          datasets: [{
            data: [
              latest.gas, 
              latest.liquid_fuel, 
              latest.coal, 
              latest.hydro, 
              latest.solar, 
              latest.india_bheramara + latest.india_tripura + latest.india_adani + latest.nepal
            ],
            backgroundColor: ['#10b981', '#f59e0b', '#3b82f6', '#0ea5e9', '#eab308', '#8b5cf6'],
            borderWidth: 0
          }]
        };
      }

      if (bpdbData.length > 0) {
        totalPresentCapacity = bpdbData.reduce((acc, curr) => acc + (curr.present_capacity || 0), 0);
        
        // Loadshedding calculation logic: Gen / Capacity ratio
        // We add an arbitrary safe margin (e.g., if generation is > 85% of total capacity, risk is high)
        if (totalPresentCapacity > 0) {
          const ratio = (currentGen / totalPresentCapacity) * 100;
          loadSheddingProb = Math.min(Math.round(ratio), 100);
          
          if (loadSheddingProb > 85) {
            loadSheddingStatus = "High";
            loadSheddingColor = "var(--danger-color)";
          } else if (loadSheddingProb > 70) {
            loadSheddingStatus = "Moderate";
            loadSheddingColor = "var(--warning-color)";
          } else {
            loadSheddingStatus = "Low";
            loadSheddingColor = "var(--success-color)";
          }
        }
      }

      generationChartData = {
        labels: pgcbData.map(d => d.time),
        datasets: [
          {
            label: 'Total Generation (MW)',
            data: pgcbData.map(d => d.generation_mw),
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.4
          }
        ]
      };

      capacityChartData = {
        labels: bpdbData.slice(0, 10).map(d => d.station_name),
        datasets: [
          {
            label: 'Present Capacity (MW)',
            data: bpdbData.slice(0, 10).map(d => d.present_capacity),
            backgroundColor: '#fbbf24'
          }
        ]
      };

      loading = false;
    } catch (err) {
      console.error(err);
      error = err.message;
      loading = false;
    }
  });
</script>

<main>
  <header>
    <div class="logo">
      <span class="material-icons">bolt</span>
      <h1>BD Power Monitor</h1>
    </div>
    
    <div class="header-controls">
      <div class="status">
        {#if loading}
          <span class="material-icons spinner">sync</span> Syncing...
        {:else if error}
          <span class="material-icons error-icon">error</span> {error}
        {:else}
          <span class="material-icons success-icon">check_circle</span> Live
        {/if}
      </div>
      <button class="theme-toggle" on:click={toggleTheme}>
        <span class="material-icons">{isDarkMode ? 'light_mode' : 'dark_mode'}</span>
      </button>
    </div>
  </header>

  <div class="dashboard">
    {#if loading}
      <div class="loader">
        <span class="material-icons spinner large">sync</span>
        <p>Loading power data...</p>
      </div>
    {:else if error}
      <div class="error">
        <span class="material-icons">warning</span>
        <p>Could not load dashboard. Please make sure the backend is running and data is scraped.</p>
      </div>
    {:else}
      <!-- Statistical Insights Top Row -->
      <section class="overview">
        <div class="card">
          <div class="card-icon" style="color: var(--primary-color); background: rgba(37,99,235,0.1);"><span class="material-icons">electric_meter</span></div>
          <div class="card-content">
            <h3>Current Generation</h3>
            <p class="value">{currentGen} <span>MW</span></p>
          </div>
        </div>
        <div class="card">
          <div class="card-icon" style="color: #8b5cf6; background: rgba(139,92,246,0.1);"><span class="material-icons">trending_up</span></div>
          <div class="card-content">
            <h3>24h Peak Generation</h3>
            <p class="value">{maxGen24h} <span>MW</span></p>
          </div>
        </div>
        <div class="card">
          <div class="card-icon" style="color: #0ea5e9; background: rgba(14,165,233,0.1);"><span class="material-icons">data_usage</span></div>
          <div class="card-content">
            <h3>24h Average</h3>
            <p class="value">{avgGen24h} <span>MW</span></p>
          </div>
        </div>
      </section>

      <!-- Second Row: Loadshedding and Fuel Mix -->
      <section class="insights-row">
        <div class="card loadshedding-card">
          <div class="loadshedding-header">
            <h3>Loadshedding Probability</h3>
            <span class="material-icons" style="color: {loadSheddingColor}">power_off</span>
          </div>
          <div class="prob-display">
            <h2 style="color: {loadSheddingColor}">{loadSheddingStatus} Risk</h2>
            <p>Grid Stress Level: <strong>{loadSheddingProb}%</strong></p>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {loadSheddingProb}%; background: {loadSheddingColor}"></div>
          </div>
          <p class="subtitle">Based on {totalPresentCapacity} MW total operational capacity.</p>
        </div>

        <div class="card chart-card-small">
          <h3>Current Fuel Mix</h3>
          <div class="doughnut-container">
            <Doughnut data={fuelMixChartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }} />
          </div>
        </div>
      </section>

      <!-- Third Row: Large Charts -->
      <section class="charts">
        <div class="chart-card">
          <h2><span class="material-icons">timeline</span> Generation Trend (Last 24h)</h2>
          <div class="chart-container">
            <Line data={generationChartData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
        
        <div class="chart-card">
          <h2><span class="material-icons">bar_chart</span> Top 10 Stations by Capacity</h2>
          <div class="chart-container">
            <Bar data={capacityChartData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </section>
    {/if}
  </div>
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--primary-color);
  }
  .logo span { font-size: 2rem; }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .theme-toggle {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    border-radius: 50%;
    transition: background 0.2s;
  }
  .theme-toggle:hover { background: var(--border-color); }

  .status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .success-icon { color: var(--success-color); }
  .error-icon { color: var(--danger-color); }
  
  .spinner { animation: spin 2s linear infinite; }
  @keyframes spin { 100% { transform: rotate(360deg); } }

  .dashboard { display: flex; flex-direction: column; gap: 2rem; }

  .overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  .insights-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .card {
    background: var(--surface-color);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--border-color);
  }

  .overview .card {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .card-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card-icon span { font-size: 2rem; }

  .card-content h3, .card h3 {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
  }
  .card h3 { margin-bottom: 1rem; }

  .value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  .value span {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-secondary);
  }
  .subtitle {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 1rem;
  }

  .loadshedding-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .loadshedding-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .loadshedding-header span { font-size: 2rem; }
  
  .prob-display { margin-top: 0.5rem; margin-bottom: 1.5rem; }
  .prob-display h2 { font-size: 2rem; margin-bottom: 0.25rem; }
  
  .progress-bar-bg {
    width: 100%;
    height: 12px;
    background: var(--border-color);
    border-radius: 6px;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 1s ease-in-out, background-color 0.3s;
  }

  .doughnut-container {
    height: 200px;
    position: relative;
  }

  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 1.5rem;
  }

  .chart-card {
    background: var(--surface-color);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--border-color);
  }
  .chart-card h2 {
    font-size: 1.25rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .chart-container {
    height: 300px;
    position: relative;
  }

  @media (max-width: 768px) {
    .charts, .insights-row { grid-template-columns: 1fr; }
  }
</style>
