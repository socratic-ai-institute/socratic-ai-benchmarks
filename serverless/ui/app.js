// Socratic AI Benchmarks - Dashboard JavaScript

// Configuration
const CONFIG = {
    // Set this to your API Gateway URL after deployment
    apiUrl: 'https://YOUR_API_GATEWAY_URL',
    apiKey: 'YOUR_API_KEY', // Get from AWS Console after deployment
};

// State
let currentWeek = getCurrentISOWeek();
let currentRunId = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initWeekSelector();
    loadWeeklyData();
});

// Navigation
function initNavigation() {
    document.getElementById('nav-weekly').addEventListener('click', () => {
        switchView('weekly');
    });

    document.getElementById('nav-runs').addEventListener('click', () => {
        switchView('runs');
    });
}

function switchView(view) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`nav-${view}`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`).classList.add('active');
}

// Week selector
function initWeekSelector() {
    const selector = document.getElementById('week-selector');
    selector.value = currentWeek;

    selector.addEventListener('change', (e) => {
        currentWeek = e.target.value;
        loadWeeklyData();
    });

    document.getElementById('refresh-weekly').addEventListener('click', loadWeeklyData);
}

function getCurrentISOWeek() {
    const now = new Date();
    const year = now.getFullYear();
    const week = getISOWeekNumber(now);
    return `${year}-W${String(week).padStart(2, '0')}`;
}

function getISOWeekNumber(date) {
    const target = new Date(date.valueOf());
    const dayNr = (date.getDay() + 6) % 7;
    target.setDate(target.getDate() - dayNr + 3);
    const firstThursday = target.valueOf();
    target.setMonth(0, 1);
    if (target.getDay() !== 4) {
        target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
    }
    return 1 + Math.ceil((firstThursday - target) / 604800000);
}

// Weekly data loading
async function loadWeeklyData() {
    const loading = document.getElementById('weekly-loading');
    const error = document.getElementById('weekly-error');
    const data = document.getElementById('weekly-data');

    loading.classList.remove('hidden');
    error.classList.add('hidden');
    data.classList.add('hidden');

    try {
        const response = await fetch(
            `${CONFIG.apiUrl}/weekly?week=${currentWeek}`,
            {
                headers: {
                    'x-api-key': CONFIG.apiKey,
                },
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        displayWeeklyData(result);

    } catch (err) {
        console.error('Error loading weekly data:', err);
        error.textContent = `Error: ${err.message}`;
        error.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

function displayWeeklyData(result) {
    const tbody = document.getElementById('weekly-tbody');
    const data = document.getElementById('weekly-data');
    const weekSpan = document.getElementById('current-week');

    weekSpan.textContent = result.week;
    tbody.innerHTML = '';

    if (!result.models || result.models.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No data for this week</td></tr>';
    } else {
        result.models.forEach(model => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${escapeHtml(model.model_id)}</td>
                <td>${model.run_count}</td>
                <td>${formatScore(model.mean_score)}</td>
                <td>${formatPercent(model.mean_compliance)}</td>
                <td>${formatDate(model.updated_at)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    data.classList.remove('hidden');
}

// Run details
document.getElementById('load-run').addEventListener('click', loadRunDetails);
document.getElementById('run-id-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') loadRunDetails();
});

async function loadRunDetails() {
    const runId = document.getElementById('run-id-input').value.trim();
    if (!runId) {
        alert('Please enter a run ID');
        return;
    }

    const loading = document.getElementById('run-loading');
    const error = document.getElementById('run-error');
    const data = document.getElementById('run-data');

    loading.classList.remove('hidden');
    error.classList.add('hidden');
    data.classList.add('hidden');

    try {
        const response = await fetch(
            `${CONFIG.apiUrl}/runs/${runId}/summary`,
            {
                headers: {
                    'x-api-key': CONFIG.apiKey,
                },
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        displayRunDetails(result);

    } catch (err) {
        console.error('Error loading run:', err);
        error.textContent = `Error: ${err.message}`;
        error.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

function displayRunDetails(result) {
    const summary = document.getElementById('run-summary');
    const turnsTbody = document.getElementById('turns-tbody');
    const data = document.getElementById('run-data');

    // Display summary
    const s = result.summary;
    summary.innerHTML = `
        <dl>
            <dt>Run ID:</dt><dd>${escapeHtml(s.run_id)}</dd>
            <dt>Model:</dt><dd>${escapeHtml(s.model_id)}</dd>
            <dt>Scenario:</dt><dd>${escapeHtml(s.scenario_id)} (${s.vector})</dd>
            <dt>Turns:</dt><dd>${s.turn_count}</dd>
            <dt>Overall Score:</dt><dd>${formatScore(s.overall_score)}</dd>
            <dt>Compliance Rate:</dt><dd>${formatPercent(s.compliance_rate)}</dd>
            <dt>Half-Life:</dt><dd>${s.half_life}</dd>
            <dt>Created:</dt><dd>${formatDate(s.created_at)}</dd>
        </dl>
    `;

    // Display turns
    turnsTbody.innerHTML = '';

    result.turns.forEach((turn, idx) => {
        const judge = result.judges[idx] || {};

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${turn.turn_index + 1}</td>
            <td>${Math.round(turn.latency_ms)}ms</td>
            <td>${turn.input_tokens} / ${turn.output_tokens}</td>
            <td>${judge.has_question ? '✓' : '✗'}</td>
            <td>${formatScore(judge.overall_score)}</td>
            <td><button class="btn btn-sm" onclick="viewTurn('${turn.s3_key}')">View</button></td>
        `;
        turnsTbody.appendChild(row);
    });

    data.classList.remove('hidden');
}

// View turn details
async function viewTurn(s3Key) {
    if (!s3Key) {
        alert('Turn data not available');
        return;
    }

    // In production, we'd fetch the signed URL from the API
    // For now, just show a placeholder
    const modal = document.getElementById('turn-modal');
    const detail = document.getElementById('turn-detail');

    detail.innerHTML = '<p>Loading turn data...</p>';
    modal.classList.remove('hidden');

    // TODO: Fetch actual turn data from signed S3 URL
    detail.innerHTML = `
        <p><strong>S3 Key:</strong> ${escapeHtml(s3Key)}</p>
        <p><em>Full turn data viewing will be implemented with signed URLs</em></p>
    `;
}

// Modal close
document.querySelector('.modal-close').addEventListener('click', () => {
    document.getElementById('turn-modal').classList.add('hidden');
});

// Utility functions
function formatScore(score) {
    if (!score) return '<span class="score score-low">—</span>';

    const val = parseFloat(score);
    let className = 'score-low';

    if (val >= 4.0) className = 'score-high';
    else if (val >= 3.0) className = 'score-medium';

    return `<span class="score ${className}">${val.toFixed(2)}</span>`;
}

function formatPercent(value) {
    if (value == null) return '—';
    return `${(value * 100).toFixed(1)}%`;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
