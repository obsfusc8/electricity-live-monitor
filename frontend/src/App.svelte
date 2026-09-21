<script>
  import { onMount } from 'svelte';
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale,
    LineElement,
    PointElement
  } from 'chart.js';
  import { Bar, Line } from 'svelte-chartjs';

  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale,
    LineElement,
    PointElement
  );

  let pgcbData = [];
  let bpdbData = [];
  let loading = true;
  let error = null;

  let generationChartData = {
    labels: [],
    datasets: []
  };

  let capacityChartData = {
    labels: [],
    datasets: []
  };

  onMount(async () => {
    try {
      const [pgcbRes, bpdbRes] = await Promise.all([
        fetch('http://localhost:3000/api/generation'),
        fetch('http://localhost:3000/api/daily-generation')
      ]);

      if (!pgcbRes.ok || !bpdbRes.ok) throw new Error('Failed to fetch data');

      let rawPgcb = await pgcbRes.json();
      let rawBpdb = await bpdbRes.json();
      
      // Data arrives from latest to oldest in limit 24, we reverse for chronologic chart
      pgcbData = rawPgcb.reverse();
      bpdbData = rawBpdb;

      // Prepare PGCB Line Chart Data
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
          },
          {
            label: 'Gas (MW)',
            data: pgcbData.map(d => d.gas),
            borderColor: '#16a34a',
            backgroundColor: 'rgba(22, 163, 74, 0.1)',
            fill: true,
            tension: 0.4
          }
        ]
      };

      // Prepare BPDB Bar Chart Data
      capacityChartData = {
        labels: bpdbData.slice(0, 10).map(d => d.station_name),
        datasets: [
          {
            label: 'Installed Capacity (MW)',
            data: bpdbData.slice(0, 10).map(d => d.installed_capacity),
            backgroundColor: '#3b82f6'
          },
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
    <div class="status">
      {#if loading}
        <span class="material-icons spinner">sync</span> Syncing...
      {:else if error}
        <span class="material-icons error-icon">error</span> {error}
      {:else}
        <span class="material-icons success-icon">check_circle</span> Live
      {/if}
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
      <section class="overview">
        <div class="card">
          <div class="card-icon"><span class="material-icons">electric_meter</span></div>
          <div class="card-content">
            <h3>Current Generation</h3>
            <p class="value">{pgcbData[pgcbData.length - 1]?.generation_mw || 0} <span>MW</span></p>
          </div>
        </div>
        <div class="card">
          <div class="card-icon"><span class="material-icons">factory</span></div>
          <div class="card-content">
            <h3>Top Station Capacity</h3>
            <p class="value">{bpdbData[0]?.installed_capacity || 0} <span>MW</span></p>
            <p class="subtitle">{bpdbData[0]?.station_name || 'N/A'}</p>
          </div>
        </div>
      </section>

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

  .logo span {
    font-size: 2rem;
  }

  .status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .success-icon { color: #10b981; }
  .error-icon { color: #ef4444; }
  
  .spinner {
    animation: spin 2s linear infinite;
  }
  @keyframes spin { 100% { transform: rotate(360deg); } }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .card {
    background: var(--surface-color);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    display: flex;
    align-items: center;
    gap: 1.5rem;
    border: 1px solid var(--border-color);
  }

  .card-icon {
    width: 60px;
    height: 60px;
    background: rgba(37, 99, 235, 0.1);
    color: var(--primary-color);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .card-icon span { font-size: 2rem; }

  .card-content h3 {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
  }

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

  .loader, .error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem;
    color: var(--text-secondary);
    gap: 1rem;
  }

  .loader .large { font-size: 3rem; color: var(--primary-color); }
  .error span { font-size: 3rem; color: #ef4444; }

  @media (max-width: 768px) {
    .charts { grid-template-columns: 1fr; }
  }
</style>
