
// Resellpur AI Testing Suite
let bulkTestData = null;
let benchmarkRunning = false;

document.addEventListener('DOMContentLoaded', function() {
    initializeTesting();
    loadExampleCases();
});

function initializeTesting() {
    // Single test form handlers
    document.getElementById('single-price-test').addEventListener('submit', handleSinglePriceTest);
    document.getElementById('single-moderation-test').addEventListener('submit', handleSingleModerationTest);
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.test-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

// Single Test Handlers
async function handleSinglePriceTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testData = {
        title: formData.get('title'),
        category: formData.get('category'),
        brand: formData.get('brand'),
        condition: formData.get('condition'),
        age_months: parseInt(formData.get('age_months')),
        asking_price: parseInt(formData.get('asking_price')),
        location: formData.get('location')
    };
    
    const expectedRange = formData.get('expected_range');
    
    showTestProgress('Running price analysis...');
    
    try {
        const startTime = performance.now();
        const response = await fetch('/negotiate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(testData)
        });
        const endTime = performance.now();
        
        const result = await response.json();
        const responseTime = (endTime - startTime) / 1000;
        
        displaySingleTestResult('price', result, testData, expectedRange, responseTime);
        
    } catch (error) {
        displayTestError('Price analysis test failed: ' + error.message);
    }
}

async function handleSingleModerationTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testData = {
        message: formData.get('message'),
        context: formData.get('context') || 'Testing'
    };
    
    const expectedStatus = formData.get('expected_status');
    
    showTestProgress('Running content moderation...');
    
    try {
        const startTime = performance.now();
        const response = await fetch('/moderate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(testData)
        });
        const endTime = performance.now();
        
        const result = await response.json();
        const responseTime = (endTime - startTime) / 1000;
        
        displaySingleTestResult('moderation', result, testData, expectedStatus, responseTime);
        
    } catch (error) {
        displayTestError('Moderation test failed: ' + error.message);
    }
}

// Bulk Testing
function handleBulkFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            if (file.name.endsWith('.json')) {
                bulkTestData = JSON.parse(e.target.result);
            } else if (file.name.endsWith('.csv')) {
                bulkTestData = parseCSV(e.target.result);
            }
            
            document.getElementById('start-bulk-test').disabled = false;
            updateBulkProgress(`Loaded ${bulkTestData.length} test cases`);
            
        } catch (error) {
            displayTestError('Failed to parse file: ' + error.message);
        }
    };
    reader.readAsText(file);
}

async function startBulkTest() {
    if (!bulkTestData) return;
    
    const testType = document.querySelector('input[name="bulk-type"]:checked').value;
    const batchSize = parseInt(document.getElementById('batch-size').value);
    const parallel = document.getElementById('parallel-processing').checked;
    
    const results = [];
    const total = bulkTestData.length;
    let completed = 0;
    
    updateBulkProgress(`Processing 0/${total} tests...`);
    
    try {
        if (parallel) {
            // Process in parallel batches
            for (let i = 0; i < bulkTestData.length; i += batchSize) {
                const batch = bulkTestData.slice(i, i + batchSize);
                const batchPromises = batch.map(async (testCase, index) => {
                    try {
                        const result = await runSingleTest(testType, testCase);
                        completed++;
                        updateBulkProgress(`Processing ${completed}/${total} tests...`);
                        return { index: i + index, success: true, result, testCase };
                    } catch (error) {
                        completed++;
                        updateBulkProgress(`Processing ${completed}/${total} tests...`);
                        return { index: i + index, success: false, error: error.message, testCase };
                    }
                });
                
                const batchResults = await Promise.all(batchPromises);
                results.push(...batchResults);
            }
        } else {
            // Process sequentially
            for (let i = 0; i < bulkTestData.length; i++) {
                try {
                    const result = await runSingleTest(testType, bulkTestData[i]);
                    results.push({ index: i, success: true, result, testCase: bulkTestData[i] });
                } catch (error) {
                    results.push({ index: i, success: false, error: error.message, testCase: bulkTestData[i] });
                }
                
                completed = i + 1;
                updateBulkProgress(`Processing ${completed}/${total} tests...`);
            }
        }
        
        displayBulkResults(results);
        
    } catch (error) {
        displayTestError('Bulk test failed: ' + error.message);
    }
}

async function runSingleTest(testType, testData) {
    const endpoint = testType === 'price' ? '/negotiate' : '/moderate';
    
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(testData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

// Performance Benchmarking
async function startBenchmark() {
    if (benchmarkRunning) return;
    
    benchmarkRunning = true;
    const startBtn = document.getElementById('start-benchmark');
    startBtn.disabled = true;
    startBtn.textContent = 'Running Benchmark...';
    
    const benchmarkType = document.getElementById('benchmark-type').value;
    const concurrentRequests = parseInt(document.getElementById('concurrent-requests').value);
    const totalRequests = parseInt(document.getElementById('total-requests').value);
    const stressTest = document.getElementById('stress-test').checked;
    
    try {
        const results = await runBenchmark(benchmarkType, concurrentRequests, totalRequests, stressTest);
        displayBenchmarkResults(results);
        
    } catch (error) {
        displayTestError('Benchmark failed: ' + error.message);
    } finally {
        benchmarkRunning = false;
        startBtn.disabled = false;
        startBtn.textContent = 'Start Benchmark';
    }
}

async function runBenchmark(testType, concurrent, total, stressTest) {
    const testData = generateBenchmarkData(testType, total);
    const results = {
        total_requests: total,
        concurrent_requests: concurrent,
        start_time: Date.now(),
        responses: [],
        errors: [],
        response_times: []
    };
    
    const chunks = [];
    for (let i = 0; i < testData.length; i += concurrent) {
        chunks.push(testData.slice(i, i + concurrent));
    }
    
    for (const chunk of chunks) {
        const chunkPromises = chunk.map(async (data) => {
            const startTime = performance.now();
            try {
                const result = await runSingleTest(testType === 'mixed' ? (Math.random() > 0.5 ? 'price' : 'moderation') : testType, data);
                const endTime = performance.now();
                const responseTime = endTime - startTime;
                
                results.responses.push(result);
                results.response_times.push(responseTime);
                
                return { success: true, responseTime };
            } catch (error) {
                const endTime = performance.now();
                const responseTime = endTime - startTime;
                
                results.errors.push(error.message);
                results.response_times.push(responseTime);
                
                return { success: false, error: error.message, responseTime };
            }
        });
        
        await Promise.all(chunkPromises);
        
        if (stressTest) {
            // Minimal delay in stress test mode
            await new Promise(resolve => setTimeout(resolve, 10));
        } else {
            // Normal delay between batches
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    results.end_time = Date.now();
    results.total_time = results.end_time - results.start_time;
    
    return results;
}

function generateBenchmarkData(testType, count) {
    const priceData = {
        title: 'iPhone 12 Pro',
        category: 'Mobile',
        brand: 'Apple',
        condition: 'Good',
        age_months: 18,
        asking_price: 45000,
        location: 'Mumbai'
    };
    
    const moderationData = {
        message: 'Is this product safe to buy?',
        context: 'Product inquiry'
    };
    
    const data = [];
    for (let i = 0; i < count; i++) {
        if (testType === 'price') {
            data.push({ ...priceData, asking_price: priceData.asking_price + (Math.random() * 10000) });
        } else if (testType === 'moderation') {
            data.push({ ...moderationData, message: moderationData.message + ` ${i}` });
        } else { // mixed
            data.push(Math.random() > 0.5 ? 
                { ...priceData, asking_price: priceData.asking_price + (Math.random() * 10000) } :
                { ...moderationData, message: moderationData.message + ` ${i}` }
            );
        }
    }
    
    return data;
}

// Example Cases
function loadExampleCases() {
    const priceExamples = [
        {
            title: 'High-End Phone Test',
            data: { title: 'iPhone 14 Pro Max', category: 'Mobile', brand: 'Apple', condition: 'Like New', age_months: 6, asking_price: 80000, location: 'Mumbai' },
            description: 'Tests pricing for premium devices'
        },
        {
            title: 'Old Laptop Test',
            data: { title: 'Dell Inspiron 5000', category: 'Laptop', brand: 'Dell', condition: 'Fair', age_months: 48, asking_price: 20000, location: 'Delhi' },
            description: 'Tests depreciation for older devices'
        }
    ];
    
    const moderationExamples = [
        {
            title: 'Safe Message',
            data: { message: 'Is this product available for pickup?', context: 'Buyer inquiry' },
            description: 'Normal buyer inquiry - should be safe'
        },
        {
            title: 'Phone Number Detection',
            data: { message: 'Call me at 9876543210 for quick deal', context: 'Seller message' },
            description: 'Contains phone number - should be flagged'
        }
    ];
    
    displayExamples('price-examples', priceExamples, 'price');
    displayExamples('moderation-examples', moderationExamples, 'moderation');
}

function displayExamples(containerId, examples, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = examples.map(example => `
        <div class="example-case">
            <h5>${example.title}</h5>
            <p class="example-description">${example.description}</p>
            <pre class="example-data">${JSON.stringify(example.data, null, 2)}</pre>
            <button class="example-btn" onclick="runExampleTest('${type}', ${JSON.stringify(example.data).replace(/"/g, '&quot;')})">
                Run Test
            </button>
        </div>
    `).join('');
}

async function runExampleTest(type, data) {
    showTestProgress(`Running ${type} example test...`);
    
    try {
        const startTime = performance.now();
        const result = await runSingleTest(type, data);
        const endTime = performance.now();
        const responseTime = (endTime - startTime) / 1000;
        
        displaySingleTestResult(type, result, data, null, responseTime);
        
    } catch (error) {
        displayTestError(`Example test failed: ${error.message}`);
    }
}

// Display Functions
function displaySingleTestResult(type, result, testData, expected, responseTime) {
    const container = document.getElementById('single-test-results');
    
    const resultHtml = `
        <div class="test-result ${result.success ? 'success' : 'error'}">
            <div class="result-header">
                <h4>${type === 'price' ? 'Price Analysis' : 'Content Moderation'} Test Result</h4>
                <span class="response-time">⏱️ ${responseTime.toFixed(2)}s</span>
            </div>
            
            <div class="result-content">
                ${result.success ? formatTestResult(type, result.result, expected) : `<div class="error">Error: ${result.error}</div>`}
            </div>
            
            <div class="test-input">
                <h5>Test Input:</h5>
                <pre>${JSON.stringify(testData, null, 2)}</pre>
            </div>
        </div>
    `;
    
    container.innerHTML = resultHtml;
}

function formatTestResult(type, result, expected) {
    if (type === 'price') {
        const confidence = Math.round(result.confidence * 100);
        const range = result.suggested_price_range;
        
        return `
            <div class="price-result">
                <div class="price-range">
                    <strong>Suggested Range:</strong> ₹${range.min.toLocaleString()} - ₹${range.max.toLocaleString()}
                </div>
                <div class="confidence">
                    <strong>Confidence:</strong> ${confidence}%
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                </div>
                <div class="market-position">
                    <strong>Market Position:</strong> ${result.market_position}
                </div>
                <div class="reasoning">
                    <strong>Reasoning:</strong> ${result.reasoning}
                </div>
                ${expected ? `<div class="validation">Expected: ${expected}</div>` : ''}
            </div>
        `;
    } else {
        const confidence = Math.round(result.confidence * 100);
        
        return `
            <div class="moderation-result">
                <div class="status ${result.status}">
                    <strong>Status:</strong> ${result.status}
                </div>
                <div class="confidence">
                    <strong>Confidence:</strong> ${confidence}%
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                </div>
                <div class="reason">
                    <strong>Reason:</strong> ${result.reason}
                </div>
                <div class="action">
                    <strong>Recommended Action:</strong> ${result.action_recommended}
                </div>
                ${expected ? `<div class="validation">Expected: ${expected}</div>` : ''}
            </div>
        `;
    }
}

function displayBulkResults(results) {
    const container = document.getElementById('bulk-test-results');
    const successCount = results.filter(r => r.success).length;
    const errorCount = results.length - successCount;
    
    const summary = `
        <div class="bulk-summary">
            <h4>Bulk Test Results</h4>
            <div class="summary-stats">
                <span class="stat success">✅ ${successCount} Passed</span>
                <span class="stat error">❌ ${errorCount} Failed</span>
                <span class="stat total">📊 ${results.length} Total</span>
            </div>
        </div>
    `;
    
    const resultsList = results.map((result, index) => `
        <div class="bulk-result-item ${result.success ? 'success' : 'error'}">
            <span class="result-index">#${index + 1}</span>
            <span class="result-status">${result.success ? '✅' : '❌'}</span>
            <span class="result-details">
                ${result.success ? 'Success' : `Error: ${result.error}`}
            </span>
        </div>
    `).join('');
    
    container.innerHTML = summary + '<div class="bulk-results-list">' + resultsList + '</div>';
}

function displayBenchmarkResults(results) {
    const container = document.getElementById('benchmark-results');
    const avgResponseTime = results.response_times.reduce((a, b) => a + b, 0) / results.response_times.length;
    const successRate = ((results.total_requests - results.errors.length) / results.total_requests * 100).toFixed(2);
    
    const benchmarkHtml = `
        <div class="benchmark-summary">
            <h4>Performance Benchmark Results</h4>
            <div class="benchmark-stats">
                <div class="stat-card">
                    <div class="stat-value">${avgResponseTime.toFixed(2)}ms</div>
                    <div class="stat-label">Avg Response Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${successRate}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(results.total_requests / (results.total_time / 1000)).toFixed(2)}</div>
                    <div class="stat-label">Requests/Second</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(results.total_time / 1000).toFixed(2)}s</div>
                    <div class="stat-label">Total Time</div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = benchmarkHtml;
}

// Utility Functions
function showTestProgress(message) {
    // Could implement a progress indicator here
    console.log(message);
}

function displayTestError(message) {
    const container = document.getElementById('single-test-results');
    container.innerHTML = `
        <div class="test-result error">
            <div class="error">${message}</div>
        </div>
    `;
}

function updateBulkProgress(message) {
    document.getElementById('bulk-progress-text').textContent = message;
}

function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim()) {
            const values = lines[i].split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index];
            });
            data.push(row);
        }
    }
    
    return data;
}
