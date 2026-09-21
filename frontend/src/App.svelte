<script>
  import { onMount } from 'svelte';
  import {
    Chart as ChartJS, Title, Tooltip, Legend, BarElement, 
    CategoryScale, LinearScale, LineElement, PointElement, ArcElement, Filler
  } from 'chart.js';
  import { Bar, Line, Doughnut } from 'svelte-chartjs';

  ChartJS.register(
    Title, Tooltip, Legend, BarElement, CategoryScale, 
    LinearScale, LineElement, PointElement, ArcElement, Filler
  );

  // Active Tab: 'live' | 'trends' | 'plants' | 'outages' | 'fuel' | 'zones'
  let activeTab = 'live';

  // Core Data States
  let loading = true;
  let refreshing = false;
  let error = null;
  let isDarkMode = false;
  let lastUpdated = '';

  // Data Stores
  let overviewData = { latest: null, trends: [], totals: {} };
  let hourlyRows = [];
  let plantsData = { rows: [], stats: {}, total: 0 };
  let fuelMixData = { totalMw: 0, fuels: [] };
  let importsData = { totalImportMw: 0, breakdown: [] };
  let outagesData = { reasons: [], summary: {} };
  let zonesData = { zones: [] };

  // Plant filtering and search
  let plantSearch = '';
  let selectedArea = 'All';
  let sortBy = 'capacity'; // 'capacity' | 'peak' | 'name'

  // Chart datasets
  let hourlyChartData = { labels: [], datasets: [] };
  let trendsChartData = { labels: [], datasets: [] };
  let fuelDoughnutData = { labels: [], datasets: [] };
  let outagesBarData = { labels: [], datasets: [] };
  let zonesBarData = { labels: [], datasets: [] };

  // Theme Toggle
  function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    updateChartThemeDefaults();
    rebuildCharts();
  }

  function updateChartThemeDefaults() {
    const textColor = isDarkMode ? '#94a3b8' : '#64748b';
    const gridColor = isDarkMode ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.7)';
    
    ChartJS.defaults.color = textColor;
    ChartJS.defaults.borderColor = gridColor;
  }

  // Load All Data from API (with robust fallback)
  async function loadAllData() {
    try {
      refreshing = true;
      const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:3000').replace(/\/$/, '');

      const [
        ovRes, hrRes, plRes, fmRes, impRes, outRes, znRes
      ] = await Promise.all([
        fetch(`${API_URL}/api/overview`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/hourly`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/plants`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/fuel-mix`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/imports`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/outages`).then(r => r.json()).catch(() => null),
        fetch(`${API_URL}/api/zones`).then(r => r.json()).catch(() => null),
      ]);

      if (ovRes) overviewData = ovRes;
      if (hrRes && hrRes.rows) hourlyRows = hrRes.rows;
      if (plRes && plRes.rows) plantsData = plRes;
      if (fmRes && fmRes.fuels) fuelMixData = fmRes;
      if (impRes && impRes.breakdown) importsData = impRes;
      if (outRes && outRes.summary) outagesData = outRes;
      if (znRes && znRes.zones) zonesData = znRes;

      lastUpdated = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      rebuildCharts();
      loading = false;
      refreshing = false;
      error = null;
    } catch (err) {
      console.error("Dashboard load failed:", err);
      error = err.message;
      loading = false;
      refreshing = false;
    }
  }

  // Chart Generators
  function rebuildCharts() {
    // 1. Hourly Chart (PGCB)
    if (hourlyRows.length > 0) {
      const labels = hourlyRows.map(r => r.time.slice(0, 5));
      hourlyChartData = {
        labels,
        datasets: [
          {
            label: 'Total Generation',
            data: hourlyRows.map(r => r.generation_mw),
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5
          },
          {
            label: 'Gas Generation',
            data: hourlyRows.map(r => r.gas),
            borderColor: '#10b981',
            borderWidth: 2,
            tension: 0.35
          },
          {
            label: 'Coal Generation',
            data: hourlyRows.map(r => r.coal),
            borderColor: '#3b82f6',
            borderWidth: 2,
            tension: 0.35
          },
          {
            label: 'Liquid Fuel (HFO/HSD)',
            data: hourlyRows.map(r => r.liquid_fuel),
            borderColor: '#f59e0b',
            borderWidth: 1.5,
            borderDash: [4, 4],
            tension: 0.35
          }
        ]
      };
    }

    // 2. 30-Day Trends Chart
    if (overviewData.trends && overviewData.trends.length > 0) {
      const trendLabels = overviewData.trends.map(t => t.reportDate ? t.reportDate.slice(5) : '');
      trendsChartData = {
        labels: trendLabels,
        datasets: [
          {
            label: 'Evening Peak Demand (MW)',
            data: overviewData.trends.map(t => t.eveningPeakDemandMw),
            borderColor: '#ef4444',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            tension: 0.2
          },
          {
            label: 'Evening Peak Gen (MW)',
            data: overviewData.trends.map(t => t.eveningPeakGenerationMw),
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            borderWidth: 2.5,
            tension: 0.2
          },
          {
            label: 'Loadshedding at Peak (MW)',
            data: overviewData.trends.map(t => t.totalLoadShedMw),
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.2)',
            fill: true,
            borderWidth: 1.5,
            tension: 0.2
          }
        ]
      };
    }

    // 3. Fuel Doughnut
    if (fuelMixData.fuels && fuelMixData.fuels.length > 0) {
      fuelDoughnutData = {
        labels: fuelMixData.fuels.map(f => f.fuel),
        datasets: [{
          data: fuelMixData.fuels.map(f => f.mw),
          backgroundColor: fuelMixData.fuels.map(f => f.color),
          borderWidth: isDarkMode ? 2 : 1,
          borderColor: isDarkMode ? '#111827' : '#ffffff'
        }]
      };
    }

    // 4. Outage Reasons Chart
    if (outagesData.reasons && outagesData.reasons.length > 0) {
      outagesBarData = {
        labels: outagesData.reasons.map(r => r.reason.length > 25 ? r.reason.slice(0, 23) + '…' : r.reason),
        datasets: [
          {
            label: 'Plants Affected',
            data: outagesData.reasons.map(r => r.count),
            backgroundColor: '#f87171',
            borderRadius: 6
          }
        ]
      };
    }

    // 5. Regional Zones Chart
    if (zonesData.zones && zonesData.zones.length > 0) {
      zonesBarData = {
        labels: zonesData.zones.map(z => z.zone),
        datasets: [
          {
            label: 'Gas (MKWHr)',
            data: zonesData.zones.map(z => z.gas),
            backgroundColor: '#10b981',
            borderRadius: 4
          },
          {
            label: 'Coal (MKWHr)',
            data: zonesData.zones.map(z => z.coal),
            backgroundColor: '#3b82f6',
            borderRadius: 4
          },
          {
            label: 'Liquid Fuel (MKWHr)',
            data: zonesData.zones.map(z => z.hfo + z.hsd),
            backgroundColor: '#f59e0b',
            borderRadius: 4
          },
          {
            label: 'Imports (MKWHr)',
            data: zonesData.zones.map(z => z.import),
            backgroundColor: '#8b5cf6',
            borderRadius: 4
          }
        ]
      };
    }
  }

  // Reactive Plant List with Search & Filtering
  $: filteredPlants = (plantsData.rows || [])
    .filter(p => {
      const matchSearch = !plantSearch || 
        p.name.toLowerCase().includes(plantSearch.toLowerCase()) || 
        (p.producer && p.producer.toLowerCase().includes(plantSearch.toLowerCase()));
      const matchArea = selectedArea === 'All' || (p.area && p.area.toLowerCase() === selectedArea.toLowerCase());
      return matchSearch && matchArea;
    })
    .sort((a, b) => {
      if (sortBy === 'capacity') return (b.presentCapacityMw || 0) - (a.presentCapacityMw || 0);
      if (sortBy === 'peak') return (b.peakHourGenerationMw || 0) - (a.peakHourGenerationMw || 0);
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return 0;
    });

  // Loadshedding Risk Computation
  $: latestHour = hourlyRows.length ? hourlyRows[hourlyRows.length - 1] : null;
  $: currentGenerationMw = latestHour ? latestHour.generation_mw : 0;
  $: totalCapacity = plantsData.stats?.totalCapacity || 20555;
  $: gridStressPct = totalCapacity > 0 ? Math.min(Math.round((currentGenerationMw / totalCapacity) * 100), 100) : 0;
  
  $: loadSheddingRisk = 
    gridStressPct > 85 ? { label: 'CRITICAL RISK', color: 'var(--danger)', bg: 'var(--danger-glow)', icon: 'warning' } :
    gridStressPct > 72 ? { label: 'MODERATE STRESS', color: 'var(--warning)', bg: 'var(--warning-glow)', icon: 'report_problem' } :
    { label: 'GRID STABLE', color: 'var(--success)', bg: 'var(--success-glow)', icon: 'check_circle' };

  onMount(() => {
    // Check saved theme or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      isDarkMode = true;
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    updateChartThemeDefaults();
    loadAllData();
  });
</script>

<main class="app-shell">
  <!-- Top Navigation Header -->
  <header class="navbar">
    <div class="nav-container">
      <div class="brand">
        <div class="brand-badge">
          <span class="material-symbols-outlined bolt-icon">bolt</span>
        </div>
        <div class="brand-text">
          <h1>PowerGrid Live Monitor</h1>
          <p class="brand-sub">Bangladesh National Grid & BPDB Analytics</p>
        </div>
      </div>

      <div class="nav-controls">
        <div class="live-pill">
          <span class="live-indicator"></span>
          <span class="live-text">{lastUpdated ? `Sync ${lastUpdated}` : 'Connecting…'}</span>
        </div>

        <button class="btn-icon" on:click={loadAllData} title="Refresh Live Data" class:rotating={refreshing}>
          <span class="material-symbols-outlined">refresh</span>
        </button>

        <button class="btn-icon theme-btn" on:click={toggleTheme} title="Toggle Dark/Light Mode">
          <span class="material-symbols-outlined">{isDarkMode ? 'light_mode' : 'dark_mode'}</span>
        </button>
      </div>
    </div>

    <!-- Navigation Tabs Bar -->
    <div class="tabs-wrapper">
      <nav class="tabs">
        <button class="tab-item" class:active={activeTab === 'live'} on:click={() => activeTab = 'live'}>
          <span class="material-symbols-outlined">speed</span> Live & Hourly
        </button>
        <button class="tab-item" class:active={activeTab === 'trends'} on:click={() => activeTab = 'trends'}>
          <span class="material-symbols-outlined">trending_up</span> 30-Day Trends
        </button>
        <button class="tab-item" class:active={activeTab === 'plants'} on:click={() => activeTab = 'plants'}>
          <span class="material-symbols-outlined">factory</span> Power Plants ({plantsData.total || 0})
        </button>
        <button class="tab-item" class:active={activeTab === 'outages'} on:click={() => activeTab = 'outages'}>
          <span class="material-symbols-outlined">power_off</span> Outages & Load Shed
        </button>
        <button class="tab-item" class:active={activeTab === 'fuel'} on:click={() => activeTab = 'fuel'}>
          <span class="material-symbols-outlined">local_gas_station</span> Fuel & Imports
        </button>
        <button class="tab-item" class:active={activeTab === 'zones'} on:click={() => activeTab = 'zones'}>
          <span class="material-symbols-outlined">grid_view</span> Regional Zones
        </button>
      </nav>
    </div>
  </header>

  <!-- Main Content Container -->
  <div class="content-wrapper">
    <!-- Top Hero KPI Stats Grid -->
    <section class="kpi-grid">
      <!-- KPI 1: Live Generation -->
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">Current Generation</span>
          <div class="kpi-icon-badge" style="background: var(--primary-glow); color: var(--primary);">
            <span class="material-symbols-outlined">electric_meter</span>
          </div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value font-mono">{currentGenerationMw.toLocaleString()} <span class="unit">MW</span></h2>
          <div class="kpi-delta">
            <span class="material-symbols-outlined">schedule</span>
            <span>Latest: {latestHour?.time || 'Live'} (PGCB)</span>
          </div>
        </div>
        <div class="kpi-footer">
          <span>Evening Peak Est: <strong>{overviewData.latest?.eveningPeakGenerationMw || 16455} MW</strong></span>
        </div>
      </div>

      <!-- KPI 2: Loadshedding & Risk -->
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">Loadshedding & Deficit</span>
          <div class="kpi-icon-badge" style="background: {loadSheddingRisk.bg}; color: {loadSheddingRisk.color};">
            <span class="material-symbols-outlined">{loadSheddingRisk.icon}</span>
          </div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value font-mono" style="color: {loadSheddingRisk.color};">
            {outagesData.summary?.totalLoadShedMw || 419} <span class="unit">MW</span>
          </h2>
          <div class="kpi-delta">
            <span class="badge" style="background: {loadSheddingRisk.bg}; color: {loadSheddingRisk.color};">
              {loadSheddingRisk.label}
            </span>
            <span>Stress: <strong>{gridStressPct}%</strong></span>
          </div>
        </div>
        <div class="kpi-footer">
          <span>Unserved Energy: <strong>{overviewData.latest?.energyUnservedMkwhr || 3.8} MKWHr</strong></span>
        </div>
      </div>

      <!-- KPI 3: Operational Fleet -->
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">Active Fleet Capacity</span>
          <div class="kpi-icon-badge" style="background: var(--success-glow); color: var(--success);">
            <span class="material-symbols-outlined">hub</span>
          </div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value font-mono">{totalCapacity.toLocaleString()} <span class="unit">MW</span></h2>
          <div class="kpi-delta">
            <span>Unavailable: <strong style="color: var(--danger);">{outagesData.summary?.totalUnavailableMw || 4100} MW</strong></span>
          </div>
        </div>
        <div class="kpi-footer">
          <span>Idle Plants: <strong>{plantsData.stats?.idleCount || 4} of {plantsData.total || 20}</strong></span>
        </div>
      </div>

      <!-- KPI 4: Gas Supply & Production Cost -->
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">Gas & Economics</span>
          <div class="kpi-icon-badge" style="background: var(--warning-glow); color: var(--warning);">
            <span class="material-symbols-outlined">payments</span>
          </div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value font-mono">৳ {overviewData.latest?.productionCostPerKwhr || 6.85} <span class="unit">/kWh</span></h2>
          <div class="kpi-delta">
            <span>Gas to Grid: <strong>{overviewData.latest?.totalGasSuppliedMmcfd || 1140} MMCFD</strong></span>
          </div>
        </div>
        <div class="kpi-footer">
          <span>Energy: <strong>{overviewData.latest?.energyGeneratedMkwhr || 356.4} MKWHr</strong></span>
        </div>
      </div>
    </section>

    <!-- ============================================== -->
    <!-- TAB 1: LIVE & HOURLY -->
    <!-- ============================================== -->
    {#if activeTab === 'live'}
      <section class="tab-content">
        <div class="grid-2-1">
          <!-- Main Hourly Chart Card -->
          <div class="card chart-card">
            <div class="card-header">
              <div>
                <h3 class="card-title"><span class="material-symbols-outlined">timeline</span> 24-Hour Live Generation Curve</h3>
                <p class="card-desc">Hourly output segmented by Gas, Coal, and Liquid Fuel mix (PGCB)</p>
              </div>
            </div>
            <div class="chart-box">
              <Line 
                data={hourlyChartData} 
                options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  interaction: { mode: 'index', intersect: false },
                  plugins: { legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true } } }
                }} 
              />
            </div>
          </div>

          <!-- Live Fuel Ring Card -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title"><span class="material-symbols-outlined">pie_chart</span> Real-Time Fuel Share</h3>
              <p class="card-desc">{currentGenerationMw.toLocaleString()} MW Total Output</p>
            </div>
            <div class="doughnut-box">
              <Doughnut 
                data={fuelDoughnutData} 
                options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } }
                }} 
              />
            </div>
          </div>
        </div>

        <!-- Imports Snapshot Bar -->
        <div class="card mt-4">
          <div class="card-header">
            <h3 class="card-title"><span class="material-symbols-outlined">sync_alt</span> Cross-Border Power Imports (Live MW)</h3>
            <p class="card-desc">Total Inflow: <strong>{importsData.totalImportMw || 2420} MW</strong> across regional interconnectors</p>
          </div>
          <div class="imports-grid">
            {#each (importsData.breakdown || []) as imp}
              <div class="import-tile">
                <div class="import-top">
                  <span class="import-name">{imp.source}</span>
                  <span class="badge badge-purple">{imp.pct}%</span>
                </div>
                <div class="import-mw font-mono">{imp.mw} MW</div>
                <div class="import-type">{imp.type}</div>
              </div>
            {/each}
          </div>
        </div>
      </section>

    <!-- ============================================== -->
    <!-- TAB 2: 30-DAY TRENDS -->
    <!-- ============================================== -->
    {:else if activeTab === 'trends'}
      <section class="tab-content">
        <div class="card chart-card">
          <div class="card-header">
            <div>
              <h3 class="card-title"><span class="material-symbols-outlined">query_stats</span> Peak Demand vs Peak Generation History</h3>
              <p class="card-desc">30-day historical analysis of system peak, evening demand gap, and unserved energy (BPDB)</p>
            </div>
          </div>
          <div class="chart-box large">
            <Line 
              data={trendsChartData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true } } }
              }} 
            />
          </div>
        </div>

        <div class="grid-3 mt-4">
          <div class="card">
            <div class="card-header"><h4 class="card-title">Average Peak Gen</h4></div>
            <p class="big-metric font-mono">{overviewData.totals?.avgPeakGen || 16250} MW</p>
            <p class="card-desc">Across last 30 daily reports</p>
          </div>
          <div class="card">
            <div class="card-header"><h4 class="card-title">Average Peak Demand</h4></div>
            <p class="big-metric font-mono">{overviewData.totals?.avgPeakDemand || 16580} MW</p>
            <p class="card-desc">Daily system requirement</p>
          </div>
          <div class="card">
            <div class="card-header"><h4 class="card-title">Total Energy Supplied</h4></div>
            <p class="big-metric font-mono">{overviewData.totals?.totalEnergy || 10540} MKWHr</p>
            <p class="card-desc">Cumulative energy generated</p>
          </div>
        </div>
      </section>

    <!-- ============================================== -->
    <!-- TAB 3: POWER PLANTS EXPLORER -->
    <!-- ============================================== -->
    {:else if activeTab === 'plants'}
      <section class="tab-content">
        <!-- Filter Controls -->
        <div class="card filter-bar">
          <div class="search-box">
            <span class="material-symbols-outlined">search</span>
            <input type="text" placeholder="Search plant name, owner (e.g. Payra, BPDB, Rampal)..." bind:value={plantSearch} />
          </div>

          <div class="filter-actions">
            <div class="select-group">
              <label for="areaSelect">Region:</label>
              <select id="areaSelect" bind:value={selectedArea}>
                <option value="All">All Regions</option>
                <option value="Dhaka">Dhaka</option>
                <option value="Chattogram">Chattogram</option>
                <option value="Khulna">Khulna</option>
                <option value="Rajshahi">Rajshahi</option>
                <option value="Barishal">Barishal</option>
                <option value="Sylhet">Sylhet</option>
                <option value="Rangpur">Rangpur</option>
                <option value="Comilla">Comilla</option>
              </select>
            </div>

            <div class="select-group">
              <label for="sortSelect">Sort By:</label>
              <select id="sortSelect" bind:value={sortBy}>
                <option value="capacity">Present Capacity</option>
                <option value="peak">Peak Output (MW)</option>
                <option value="name">Station Name</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Plants Table -->
        <div class="card table-card mt-4">
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Station Name</th>
                  <th>Owner / Producer</th>
                  <th>Area</th>
                  <th>Installed</th>
                  <th>Present Cap.</th>
                  <th>Peak Output</th>
                  <th>Status</th>
                  <th>Remarks / Reason</th>
                </tr>
              </thead>
              <tbody>
                {#if filteredPlants.length === 0}
                  <tr><td colspan="9" class="text-center py-6">No matching power stations found.</td></tr>
                {:else}
                  {#each filteredPlants as plant, idx}
                    <tr>
                      <td class="font-mono text-muted">{plant.sl || idx + 1}</td>
                      <td><strong>{plant.name}</strong></td>
                      <td><span class="producer-badge">{plant.producer || 'BPDB'}</span></td>
                      <td>{plant.area || 'Dhaka'}</td>
                      <td class="font-mono">{plant.installedCapacity || '—'}</td>
                      <td class="font-mono">{plant.presentCapacityMw} MW</td>
                      <td class="font-mono font-bold" style="color: var(--primary);">{plant.peakHourGenerationMw} MW</td>
                      <td>
                        {#if (plant.peakHourGenerationMw || 0) === 0}
                          <span class="badge badge-danger">Offline / Outage</span>
                        {:else if plant.peakHourGenerationMw < (plant.presentCapacityMw * 0.8)}
                          <span class="badge badge-warning">Derated</span>
                        {:else}
                          <span class="badge badge-success">Optimal</span>
                        {/if}
                      </td>
                      <td class="text-muted remarks-cell">{plant.remarks || 'Normal / Running'}</td>
                    </tr>
                  {/each}
                {/if}
              </tbody>
            </table>
          </div>
        </div>
      </section>

    <!-- ============================================== -->
    <!-- TAB 4: OUTAGES & LOAD SHEDDING -->
    <!-- ============================================== -->
    {:else if activeTab === 'outages'}
      <section class="tab-content">
        <div class="grid-2-1">
          <!-- Outage Reasons Chart -->
          <div class="card chart-card">
            <div class="card-header">
              <h3 class="card-title"><span class="material-symbols-outlined">build</span> Top Station Outage Drivers</h3>
              <p class="card-desc">Primary reasons plants are offline or running at derated capacity</p>
            </div>
            <div class="chart-box">
              <Bar 
                data={outagesBarData} 
                options={{ 
                  indexAxis: 'y',
                  responsive: true, 
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } }
                }} 
              />
            </div>
          </div>

          <!-- Unavailable Breakdown Card -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title"><span class="material-symbols-outlined">warning</span> Capacity Bottlenecks</h3>
              <p class="card-desc">Scheduled vs Emergency Forced Outages</p>
            </div>

            <div class="bottleneck-list">
              <div class="bottleneck-item">
                <div class="bottleneck-label">
                  <span>Planned Maintenance</span>
                  <span class="font-mono"><strong>{outagesData.summary?.plannedSdCapacityMw || 1420} MW</strong></span>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width: 35%; background: var(--warning);"></div></div>
              </div>

              <div class="bottleneck-item">
                <div class="bottleneck-label">
                  <span>Forced Shutdown (Breakdowns/Gas)</span>
                  <span class="font-mono"><strong style="color: var(--danger);">{outagesData.summary?.forcedSdCapacityMw || 2680} MW</strong></span>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width: 65%; background: var(--danger);"></div></div>
              </div>

              <div class="bottleneck-total">
                <span>Total Unavailable Capacity:</span>
                <span class="font-mono font-bold text-danger">{outagesData.summary?.totalUnavailableMw || 4100} MW</span>
              </div>
            </div>

            <div class="load-shed-box mt-4">
              <h4>Load Shedding Advisory</h4>
              <p>Evening peak deficit of <strong>{outagesData.summary?.totalLoadShedMw || 419} MW</strong> reported. Major constraint: Gas low pressure in Narayanganj and Chattogram corridors.</p>
            </div>
          </div>
        </div>
      </section>

    <!-- ============================================== -->
    <!-- TAB 5: FUEL & IMPORTS -->
    <!-- ============================================== -->
    {:else if activeTab === 'fuel'}
      <section class="tab-content">
        <div class="fuel-cards-grid">
          {#each (fuelMixData.fuels || []) as fuel}
            <div class="card fuel-card" style="border-top: 4px solid {fuel.color};">
              <div class="fuel-header">
                <span class="fuel-name">{fuel.fuel}</span>
                <span class="fuel-pct badge" style="background: {fuel.color}22; color: {fuel.color};">{fuel.pct}%</span>
              </div>
              <h3 class="fuel-mw font-mono">{fuel.mw.toLocaleString()} <span class="unit">MW</span></h3>
              <p class="card-desc">Contribution to active generation</p>
            </div>
          {/each}
        </div>

        <div class="card mt-4">
          <div class="card-header">
            <h3 class="card-title"><span class="material-symbols-outlined">public</span> Cross-Border Electricity Transmission Details</h3>
            <p class="card-desc">Power imported under Long-Term PPAs & Regional Grid Interconnections</p>
          </div>
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Interconnector Point</th>
                  <th>Country / State</th>
                  <th>Current Capacity (MW)</th>
                  <th>Share of Imports</th>
                  <th>Grid Transmission Technology</th>
                </tr>
              </thead>
              <tbody>
                {#each (importsData.breakdown || []) as imp}
                  <tr>
                    <td><strong>{imp.source}</strong></td>
                    <td>India / Cross-Border</td>
                    <td class="font-mono font-bold">{imp.mw} MW</td>
                    <td><span class="badge badge-purple">{imp.pct}%</span></td>
                    <td>{imp.type}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      </section>

    <!-- ============================================== -->
    <!-- TAB 6: REGIONAL ZONES -->
    <!-- ============================================== -->
    {:else if activeTab === 'zones'}
      <section class="tab-content">
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title"><span class="material-symbols-outlined">map</span> Regional Energy Generation Mix (MKWHr)</h3>
            <p class="card-desc">Energy delivered by divisions across Bangladesh (BPDB Zone Generation Report)</p>
          </div>
          <div class="chart-box large">
            <Bar 
              data={zonesBarData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                scales: { x: { stacked: true }, y: { stacked: true } },
                plugins: { legend: { position: 'top' } }
              }} 
            />
          </div>
        </div>
      </section>
    {/if}
  </div>

  <!-- Footer -->
  <footer class="app-footer">
    <div class="footer-inner">
      <p>Data synchronized from <strong>Power Grid Bangladesh PLC (PGCB)</strong> & <strong>Bangladesh Power Development Board (BPDB)</strong></p>
      <p class="footer-sub">Engineered with Svelte, Fastify & ClickHouse • Modern Material 3 Architecture</p>
    </div>
  </footer>
</main>

<style>
  /* Base Shell */
  .app-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Header & Navigation */
  .navbar {
    position: sticky;
    top: 0;
    z-index: 50;
    background: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
    backdrop-filter: blur(12px);
  }

  .nav-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0.85rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
  }

  .brand-badge {
    width: 42px;
    height: 42px;
    border-radius: var(--radius-md);
    background: var(--primary-glow);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--primary);
  }

  .bolt-icon { font-size: 26px; }

  .brand h1 {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
  }

  .brand-sub {
    font-size: 0.78rem;
    color: var(--text-secondary);
  }

  .nav-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .live-pill {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    background: var(--bg-subtle);
    padding: 0.4rem 0.85rem;
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid var(--border-color);
  }

  .live-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px var(--success);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .btn-icon {
    width: 38px;
    height: 38px;
    border-radius: var(--radius-md);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-icon:hover {
    background: var(--bg-card-hover);
    color: var(--text-primary);
    border-color: var(--border-subtle);
  }

  .rotating {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    100% { transform: rotate(360deg); }
  }

  /* Tabs */
  .tabs-wrapper {
    border-top: 1px solid var(--border-color);
    background: var(--bg-card);
  }

  .tabs {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
  }

  .tab-item {
    background: none;
    border: none;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .tab-item:hover {
    color: var(--text-primary);
  }

  .tab-item.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
    font-weight: 600;
  }

  /* Content Wrapper */
  .content-wrapper {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
    flex: 1;
    width: 100%;
  }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .kpi-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .kpi-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .kpi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }

  .kpi-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-secondary);
  }

  .kpi-icon-badge {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .kpi-value {
    font-size: 1.95rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.1;
  }

  .kpi-value .unit {
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .kpi-delta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.4rem;
  }

  .kpi-footer {
    border-top: 1px solid var(--border-color);
    margin-top: 0.85rem;
    padding-top: 0.65rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  /* Cards Common */
  .card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
  }

  .card-header {
    margin-bottom: 1.25rem;
  }

  .card-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .card-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-top: 0.2rem;
  }

  .chart-box {
    height: 350px;
    position: relative;
  }

  .chart-box.large {
    height: 420px;
  }

  .doughnut-box {
    height: 280px;
    position: relative;
  }

  /* Grid Layouts */
  .grid-2-1 {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
  }

  .grid-3 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .mt-4 { margin-top: 1.25rem; }

  /* Imports Grid */
  .imports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
  }

  .import-tile {
    background: var(--bg-subtle);
    border-radius: var(--radius-md);
    padding: 1rem;
    border: 1px solid var(--border-color);
  }

  .import-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
  }

  .import-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
  }

  .import-mw {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--purple);
  }

  .import-type {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 0.2rem;
  }

  /* Badges & Pills */
  .badge {
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-full);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    display: inline-block;
  }

  .badge-success { background: var(--success-glow); color: var(--success); }
  .badge-warning { background: var(--warning-glow); color: var(--warning); }
  .badge-danger { background: var(--danger-glow); color: var(--danger); }
  .badge-purple { background: rgba(139, 92, 246, 0.15); color: var(--purple); }

  /* Filter Bar */
  .filter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem 1.25rem;
    flex-wrap: wrap;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--bg-subtle);
    padding: 0.5rem 0.85rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    flex: 1;
    min-width: 260px;
  }

  .search-box input {
    background: none;
    border: none;
    outline: none;
    color: var(--text-primary);
    width: 100%;
    font-size: 0.875rem;
  }

  .filter-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .select-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.82rem;
    color: var(--text-secondary);
  }

  .select-group select {
    background: var(--bg-subtle);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.45rem 0.75rem;
    border-radius: var(--radius-md);
    font-size: 0.85rem;
    outline: none;
  }

  /* Tables */
  .table-responsive {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    text-align: left;
  }

  th {
    padding: 0.85rem 1rem;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-secondary);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }

  td {
    padding: 0.85rem 1rem;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-primary);
  }

  tr:hover td {
    background: var(--bg-subtle);
  }

  .producer-badge {
    background: var(--bg-subtle);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }

  .remarks-cell {
    font-size: 0.8rem;
    max-width: 220px;
  }

  /* Outage Bottleneck Progress Bars */
  .bottleneck-list {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .bottleneck-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
    margin-bottom: 0.35rem;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--bg-subtle);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: var(--radius-full);
  }

  .bottleneck-total {
    display: flex;
    justify-content: space-between;
    font-size: 0.95rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
  }

  .text-danger { color: var(--danger); }

  .load-shed-box {
    background: var(--bg-subtle);
    padding: 1rem;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--warning);
  }

  .load-shed-box h4 {
    font-size: 0.9rem;
    margin-bottom: 0.3rem;
    color: var(--text-primary);
  }

  .load-shed-box p {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  /* Fuel Cards Grid */
  .fuel-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .fuel-card {
    padding: 1.25rem;
  }

  .fuel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .fuel-name {
    font-size: 0.9rem;
    font-weight: 600;
  }

  .fuel-mw {
    font-size: 1.8rem;
    font-weight: 700;
  }

  .big-metric {
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--primary);
  }

  /* Footer */
  .app-footer {
    border-top: 1px solid var(--border-color);
    background: var(--bg-card);
    padding: 2rem 1.5rem;
    margin-top: 3rem;
    text-align: center;
  }

  .footer-inner p {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  .footer-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
  }

  /* Responsive Breakpoints */
  @media (max-width: 1024px) {
    .grid-2-1 {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 768px) {
    .nav-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }
    .nav-controls {
      width: 100%;
      justify-content: space-between;
    }
    .filter-bar {
      flex-direction: column;
      align-items: stretch;
    }
    .filter-actions {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>
