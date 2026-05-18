let batchItems = [];

const form = document.getElementById('item-form');
const batchList = document.getElementById('batch-list');
const orchestrateBtn = document.getElementById('orchestrate-btn');
const resultsCard = document.getElementById('results-card');
const resultsList = document.getElementById('results-list');

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function parseIntegerField(id) {
    return Number.parseInt(document.getElementById(id).value, 10);
}

form.addEventListener('submit', (e) => {
    e.preventDefault();

    const itemId = document.getElementById('itemId').value.trim();
    const warehouseId = document.getElementById('warehouseId').value.trim();
    const demandStr = document.getElementById('historicalDemand').value;
    const currentStock = parseIntegerField('currentStock');
    const reorderLevel = parseIntegerField('reorderLevel');
    const forecastHorizon = parseIntegerField('forecastHorizon');
    const safetyStock = parseIntegerField('safetyStock');
    const supplierLeadTime = parseIntegerField('supplierLeadTime');

    const historicalDemand = demandStr
        .split(',')
        .map(n => Number.parseFloat(n.trim()))
        .filter(n => !Number.isNaN(n));

    if (!itemId || !warehouseId) {
        alert('Item ID and Warehouse ID are required.');
        return;
    }

    if (historicalDemand.length === 0) {
        alert('Please enter valid numbers for historical demand.');
        return;
    }

    const stockValues = [currentStock, reorderLevel, safetyStock, supplierLeadTime];
    if (historicalDemand.some(n => n < 0) || stockValues.some(n => Number.isNaN(n) || n < 0) || Number.isNaN(forecastHorizon) || forecastHorizon <= 0) {
        alert('Numeric values must be valid and non-negative. Forecast horizon must be greater than zero.');
        return;
    }

    batchItems.push({
        item_id: itemId,
        historical_demand: historicalDemand,
        current_stock: currentStock,
        reorder_level: reorderLevel,
        forecast_horizon: forecastHorizon,
        warehouse_id: warehouseId,
        safety_stock: safetyStock,
        supplier_lead_time: supplierLeadTime
    });

    renderBatch();

    document.getElementById('itemId').value = '';
    document.getElementById('historicalDemand').value = '';
    orchestrateBtn.disabled = false;
});

function renderBatch() {
    batchList.innerHTML = '';
    batchItems.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'batch-item';
        div.innerHTML = `
            <span><strong>${escapeHtml(item.item_id)}</strong> Stock: ${item.current_stock} | Warehouse: ${escapeHtml(item.warehouse_id)}</span>
            <button type="button" class="btn-icon" onclick="removeItem(${index})" aria-label="Remove ${escapeHtml(item.item_id)}">x</button>
        `;
        batchList.appendChild(div);
    });
}

window.removeItem = function(index) {
    batchItems.splice(index, 1);
    renderBatch();
    orchestrateBtn.disabled = batchItems.length === 0;
};

orchestrateBtn.addEventListener('click', async () => {
    orchestrateBtn.innerText = 'Processing...';
    orchestrateBtn.disabled = true;

    try {
        const res = await fetch('/api/orchestrate_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: batchItems })
        });

        if (!res.ok) {
            throw new Error(await res.text());
        }

        const data = await res.json();
        renderResults(data.results);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        orchestrateBtn.innerText = 'Run Recommendation';
        orchestrateBtn.disabled = batchItems.length === 0;
    }
});

function renderResults(results) {
    resultsCard.style.display = 'block';
    resultsList.innerHTML = '';

    results.forEach(res => {
        const div = document.createElement('div');
        const actionClass = res.action.toLowerCase();

        div.className = `result-item ${actionClass}`;
        div.innerHTML = `
            <div class="result-header">
                <h3>${escapeHtml(res.item_id)}</h3>
                <span class="badge ${actionClass}">${escapeHtml(res.action)}</span>
            </div>
            <div class="result-stats">
                <div class="stat">
                    <span class="stat-label">Predicted Demand</span>
                    <span class="stat-value">${Number(res.predicted_demand).toFixed(1)}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Reorder Qty</span>
                    <span class="stat-value">${res.reorder_quantity}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Confidence</span>
                    <span class="stat-value">${Math.round(Number(res.forecast_confidence) * 100)}%</span>
                </div>
            </div>
            <div class="result-msg">${escapeHtml(res.explanation)}</div>
        `;
        resultsList.appendChild(div);
    });
}
