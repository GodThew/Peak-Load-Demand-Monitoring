const API_URL = 'http://localhost:8000/api/status';

function updateClock() {
    const now = new Date();
    document.getElementById('clock').innerText = now.toLocaleTimeString();
}

function getStatusClass(status) {
    if (status === 'CRITICAL') return 'status-critical';
    if (status === 'WARNING') return 'status-warning';
    return 'status-normal';
}

function getProgressColor(status) {
    if (status === 'CRITICAL') return 'var(--danger)';
    if (status === 'WARNING') return 'var(--warning)';
    return 'var(--success)';
}

function renderCard(factory) {
    const percent = Math.min((factory.current_kw / factory.control_line) * 100, 100);
    const statusClass = getStatusClass(factory.status);
    const progressColor = getProgressColor(factory.status);

    return `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="factory-name">${factory.name}</div>
                    <div class="factory-type">${factory.type} Pricing Scheme</div>
                </div>
                <div class="status-indicator ${statusClass}">${factory.status}</div>
            </div>
            
            <div class="meter-container">
                <div class="peak-badge ${factory.is_peak_time ? 'active' : ''}">ON PEAK</div>
                <div class="kw-value">${factory.current_kw.toFixed(1)}</div>
                <div class="kw-unit">kW Demand</div>
                
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${percent}%; background-color: ${progressColor}"></div>
                </div>
            </div>

            <div class="metrics">
                <div class="metric-item">
                    <div class="metric-label">Control Line</div>
                    <div class="metric-val">${factory.control_line.toLocaleString()} kW</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Usage %</div>
                    <div class="metric-val">${percent.toFixed(1)}%</div>
                </div>
            </div>
        </div>
    `;
}

async function fetchData() {
    const grid = document.getElementById('factory-grid');
    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        
        if (data.length === 0) {
            grid.innerHTML = '<div class="error-message">No factory data received.</div>';
            return;
        }

        grid.innerHTML = data.map(factory => renderCard(factory)).join('');
        
        // Update connection status
        document.getElementById('system-status').innerText = 'System Online';
        document.getElementById('system-status').className = 'badge status-success';
        
    } catch (error) {
        console.error('Error fetching data:', error);
        grid.innerHTML = `
            <div style="color: var(--text-secondary); text-align: center; grid-column: 1/-1; padding: 2rem;">
                <h2>⚠️ Connection Failed</h2>
                <p>Cannot reach the factory simulation server at ${API_URL}</p>
                <br>
                <p>Please ensure you have started the backend:</p>
                <code style="background: #333; padding: 0.5rem; display: block; margin: 1rem auto; max-width: 400px; border-radius: 4px;">uvicorn main:app --reload</code>
            </div>
        `;
        document.getElementById('system-status').innerText = 'Offline';
        document.getElementById('system-status').className = 'badge status-critical';
    }
}

// Initial loop
setInterval(updateClock, 1000);
setInterval(fetchData, 1000);
fetchData(); // First call
updateClock();
