
// Resellpur AI Dashboard - Real-time Metrics
let requestVolumeChart, confidenceChart;
let activityFeedMaxItems = 50;

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    
    // Refresh dashboard every 30 seconds
    setInterval(refreshDashboard, 30000);
    
    // Start real-time activity feed
    startActivityFeed();
});

async function initializeDashboard() {
    await refreshDashboard();
    initializeCharts();
}

async function refreshDashboard() {
    try {
        // Fetch comprehensive stats
        const [stats, metrics, marketData] = await Promise.all([
            fetch('/api/stats/detailed').then(r => r.json()),
            fetch('/api/metrics/realtime').then(r => r.json()),
            fetch('/api/market/insights').then(r => r.json())
        ]);

        updateMetricsCards(stats, metrics);
        updateCharts(metrics);
        updateMarketData(marketData);
        
        document.getElementById('last-updated').textContent = 
            `Last updated: ${new Date().toLocaleTimeString()}`;
            
    } catch (error) {
        console.error('Dashboard refresh failed:', error);
        showError('Failed to refresh dashboard data');
    }
}

function updateMetricsCards(stats, metrics) {
    // Price Analysis Metrics
    document.getElementById('price-total').textContent = 
        formatNumber(stats.price_suggestor?.total_executions || 0);
    document.getElementById('price-success').textContent = 
        Math.round((stats.price_suggestor?.success_rate || 0) * 100) + '%';
    
    // Moderation Metrics
    document.getElementById('moderation-total').textContent = 
        formatNumber(stats.chat_moderator?.total_executions || 0);
    document.getElementById('moderation-accuracy').textContent = 
        Math.round((stats.chat_moderator?.success_rate || 0) * 100) + '%';
    
    // Response Time
    document.getElementById('avg-response-time').textContent = 
        (stats.avg_response_time || 0).toFixed(2) + 's';
    document.getElementById('p95-time').textContent = 
        (metrics.p95_response_time || 0).toFixed(2) + 's';
    
    // AI Confidence
    document.getElementById('avg-confidence').textContent = 
        Math.round((metrics.avg_confidence || 0) * 100) + '%';
    document.getElementById('high-conf-rate').textContent = 
        Math.round((metrics.high_confidence_rate || 0) * 100) + '%';
}

function initializeCharts() {
    // Request Volume Chart
    const ctx1 = document.getElementById('requestVolumeChart').getContext('2d');
    requestVolumeChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Price Analysis',
                data: [],
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                tension: 0.4
            }, {
                label: 'Content Moderation',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Confidence Distribution Chart
    const ctx2 = document.getElementById('confidenceChart').getContext('2d');
    confidenceChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['High (80-100%)', 'Medium (60-80%)', 'Low (0-60%)'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
            }]
        },
        options: {
            responsive: true
        }
    });
}

function updateCharts(metrics) {
    if (metrics.hourly_requests && requestVolumeChart) {
        requestVolumeChart.data.labels = metrics.hourly_requests.labels || [];
        requestVolumeChart.data.datasets[0].data = metrics.hourly_requests.price_analysis || [];
        requestVolumeChart.data.datasets[1].data = metrics.hourly_requests.moderation || [];
        requestVolumeChart.update();
    }

    if (metrics.confidence_distribution && confidenceChart) {
        confidenceChart.data.datasets[0].data = [
            metrics.confidence_distribution.high || 0,
            metrics.confidence_distribution.medium || 0,
            metrics.confidence_distribution.low || 0
        ];
        confidenceChart.update();
    }
}

function updateMarketData(marketData) {
    // Top Categories
    const categoriesHtml = marketData.top_categories?.map(cat => 
        `<div class="category-item">
            <span class="category-name">${cat.name}</span>
            <span class="category-count">${formatNumber(cat.count)}</span>
        </div>`
    ).join('') || 'No data available';
    document.getElementById('top-categories').innerHTML = categoriesHtml;

    // Price Trends
    const trendsHtml = marketData.price_trends?.map(trend => 
        `<div class="trend-item ${trend.direction}">
            <span class="trend-category">${trend.category}</span>
            <span class="trend-change">${trend.change}%</span>
        </div>`
    ).join('') || 'No data available';
    document.getElementById('price-trends').innerHTML = trendsHtml;

    // Fraud Alerts
    const alertsHtml = marketData.fraud_alerts?.map(alert => 
        `<div class="alert-item severity-${alert.severity}">
            <span class="alert-type">${alert.type}</span>
            <span class="alert-count">${alert.count}</span>
        </div>`
    ).join('') || 'No alerts';
    document.getElementById('fraud-alerts').innerHTML = alertsHtml;
}

async function startActivityFeed() {
    try {
        const response = await fetch('/api/activity/stream');
        const activities = await response.json();
        
        activities.forEach(addActivityItem);
        
        // Poll for new activities every 5 seconds
        setInterval(async () => {
            try {
                const newActivities = await fetch('/api/activity/recent').then(r => r.json());
                newActivities.forEach(addActivityItem);
            } catch (error) {
                console.error('Failed to fetch recent activities:', error);
            }
        }, 5000);
        
    } catch (error) {
        console.error('Failed to start activity feed:', error);
    }
}

function addActivityItem(activity) {
    const feed = document.getElementById('activity-feed');
    const activityElement = document.createElement('div');
    activityElement.className = `activity-item ${activity.type}`;
    
    const timeAgo = formatTimeAgo(new Date(activity.timestamp));
    const icon = getActivityIcon(activity.type);
    
    activityElement.innerHTML = `
        <div class="activity-icon">${icon}</div>
        <div class="activity-content">
            <div class="activity-title">${activity.title}</div>
            <div class="activity-details">${activity.details}</div>
        </div>
        <div class="activity-time">${timeAgo}</div>
    `;
    
    feed.insertBefore(activityElement, feed.firstChild);
    
    // Limit feed items
    while (feed.children.length > activityFeedMaxItems) {
        feed.removeChild(feed.lastChild);
    }
}

function getActivityIcon(type) {
    const icons = {
        'price_analysis': '💰',
        'moderation': '🛡️',
        'fraud_detection': '🚨',
        'batch_processing': '📦',
        'system': '⚙️'
    };
    return icons[type] || '📊';
}

function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

function showError(message) {
    console.error(message);
    // Could add toast notification here
}
