
// Resellpur AI Assistant - Enhanced Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Get DOM elements
    const priceForm = document.getElementById('price-form');
    const moderationForm = document.getElementById('moderation-form');
    const loadingModal = document.getElementById('loading-modal');
    const priceResult = document.getElementById('price-result');
    const moderationResult = document.getElementById('moderation-result');

    // Initialize event listeners
    if (priceForm) {
        priceForm.addEventListener('submit', handlePriceAnalysis);
    }
    
    if (moderationForm) {
        moderationForm.addEventListener('submit', handleModerationAnalysis);
    }

    // Load statistics on page load
    loadStatistics();
    
    // Refresh statistics every 30 seconds
    setInterval(loadStatistics, 30000);
}

// Smooth scroll to section function
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
        
        // Add a subtle highlight effect
        element.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.3)';
        setTimeout(() => {
            element.style.boxShadow = '';
        }, 2000);

        // Temporarily highlight the corresponding nav button
        highlightNavButton(sectionId);
    }
}

// Highlight navigation button
function highlightNavButton(sectionId) {
    // Remove active class from all buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked button (simplified mapping)
    const navButtons = document.querySelectorAll('.nav-btn');
    const sectionMap = {
        'capabilities-overview': 0,
        'price-analyst': 1,
        'content-moderator': 2,
        'metrics-section': 5,
        'vision-section': 6
    };
    
    const buttonIndex = sectionMap[sectionId];
    if (buttonIndex !== undefined && navButtons[buttonIndex]) {
        navButtons[buttonIndex].classList.add('active');
        
        // Remove active class after 3 seconds
        setTimeout(() => {
            navButtons[buttonIndex].classList.remove('active');
        }, 3000);
    }
}

// Price Analysis Handler
async function handlePriceAnalysis(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        title: formData.get('title'),
        category: formData.get('category'),
        brand: formData.get('brand'),
        condition: formData.get('condition'),
        age_months: parseInt(formData.get('age_months')),
        asking_price: parseInt(formData.get('asking_price')),
        location: formData.get('location')
    };

    // Validate form data
    if (!validatePriceData(data)) {
        return;
    }

    showLoadingModal('Analyzing pricing with AI algorithms...', 
                    'Our machine learning models are processing market data, depreciation patterns, and location factors to provide optimal pricing recommendations.');

    try {
        const response = await fetch('/negotiate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoadingModal();

        if (response.ok && result.success) {
            displayPriceResults(result.result);
        } else {
            displayPriceError(result.error || 'AI analysis temporarily unavailable. Please try again.');
        }

    } catch (error) {
        hideLoadingModal();
        console.error('Price analysis error:', error);
        
        // More specific error handling
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            displayPriceError('Connection issue detected. Our servers are responding. Please refresh the page and try again.');
        } else if (error.message && error.message.includes('timeout')) {
            displayPriceError('Analysis is taking longer than expected. Our AI is processing your request - please try again in a moment.');
        } else {
            displayPriceError('Our AI pricing engine is currently optimizing. Please try again in a few minutes for the most accurate results.');
        }
    }
}

// Moderation Analysis Handler
async function handleModerationAnalysis(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        message: formData.get('message'),
        context: formData.get('context') || 'General content analysis'
    };

    if (!data.message || data.message.trim().length === 0) {
        alert('Please enter a message to analyze.');
        return;
    }

    showLoadingModal('Analyzing content safety...', 
                    'Our NLP models are scanning for policy violations, spam patterns, and safety concerns.');

    try {
        const response = await fetch('/moderate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoadingModal();

        if (response.ok && result.success) {
            displayModerationResults(result.result);
        } else {
            displayModerationError(result.error || 'Moderation analysis failed. Please try again.');
        }

    } catch (error) {
        hideLoadingModal();
        displayModerationError('Network error. Please check your connection and try again.');
        console.error('Moderation analysis error:', error);
    }
}

// Validation Functions
function validatePriceData(data) {
    const requiredFields = ['title', 'category', 'brand', 'condition', 'location'];
    const missingFields = requiredFields.filter(field => !data[field]);
    
    if (missingFields.length > 0) {
        alert(`Please fill in all required fields: ${missingFields.join(', ')}`);
        return false;
    }

    if (!data.age_months || data.age_months < 0) {
        alert('Please enter a valid product age in months.');
        return false;
    }

    if (!data.asking_price || data.asking_price <= 0) {
        alert('Please enter a valid asking price.');
        return false;
    }

    return true;
}

// Display Functions
function displayPriceResults(result) {
    const priceResult = document.getElementById('price-result');
    if (!priceResult) return;

    const priceRange = result.suggested_price_range;
    const confidence = result.confidence;
    const marketPosition = result.market_position;

    // Determine confidence level
    let confidenceClass = 'confidence-low';
    let confidenceText = 'Low Confidence';
    if (confidence >= 0.8) {
        confidenceClass = 'confidence-high';
        confidenceText = 'High Confidence';
    } else if (confidence >= 0.6) {
        confidenceClass = 'confidence-medium';
        confidenceText = 'Medium Confidence';
    }

    // Determine market position class
    const positionClass = `position-${marketPosition.replace('_', '-')}`;

    priceResult.innerHTML = `
        <div class="price-analysis">
            <div class="price-header">
                <h3 class="price-title">AI Price Recommendation</h3>
                <div class="confidence-badge ${confidenceClass}">
                    ${confidenceText} (${Math.round(confidence * 100)}%)
                </div>
            </div>
            
            <div class="price-range">
                <div class="price-min">
                    <div class="price-label">Minimum Fair Price</div>
                    <div class="price-value">₹${formatNumber(priceRange.min)}</div>
                </div>
                <div class="price-separator">—</div>
                <div class="price-max">
                    <div class="price-label">Maximum Fair Price</div>
                    <div class="price-value">₹${formatNumber(priceRange.max)}</div>
                </div>
            </div>

            <div class="market-position ${positionClass}">
                <span>📊</span>
                Market Assessment: ${formatMarketPosition(marketPosition)}
            </div>

            <div class="reasoning">
                <h4>AI Analysis Reasoning</h4>
                <p>${result.reasoning}</p>
            </div>

            ${result.recommendations && result.recommendations.length > 0 ? `
                <div class="recommendations">
                    <h4>Smart Recommendations</h4>
                    <ul>
                        ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${result.metadata ? `
                <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.9rem; color: var(--text-muted); text-align: center;">
                    Analysis completed in ${result.metadata.processing_time?.toFixed(2) || 'N/A'}s using ${formatAgentType(result.metadata.agent_type)}
                </div>
            ` : ''}
        </div>
    `;

    // Update statistics after successful analysis
    setTimeout(loadStatistics, 1000);
}

function displayModerationResults(result) {
    const moderationResult = document.getElementById('moderation-result');
    if (!moderationResult) return;

    const status = result.status;
    const severity = result.severity;
    
    // Determine status styling
    let statusClass = 'moderation-safe';
    let statusIcon = '✅';
    let statusIconClass = 'status-safe';
    
    if (status === 'abusive' || status === 'policy_violation') {
        statusClass = 'moderation-danger';
        statusIcon = '🚫';
        statusIconClass = 'status-danger';
    } else if (status === 'phone_detected') {
        statusClass = 'moderation-warning';
        statusIcon = '⚠️';
        statusIconClass = 'status-warning';
    }

    const severityClass = `severity-${severity}`;
    const actionText = formatActionRecommendation(result.action_recommended);

    moderationResult.innerHTML = `
        <div class="moderation-analysis ${statusClass}">
            <div class="status-header">
                <div class="status-icon ${statusIconClass}">${statusIcon}</div>
                <div>
                    <div class="status-title">${formatModerationStatus(status)}</div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        Confidence: ${Math.round(result.confidence * 100)}%
                    </div>
                </div>
                <div class="severity-badge ${severityClass}">
                    ${severity.charAt(0).toUpperCase() + severity.slice(1)} Severity
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.8); padding: 1.5rem; border-radius: var(--radius); margin-bottom: 1rem;">
                <h4 style="margin-bottom: 0.5rem; font-weight: 600;">Analysis Reasoning</h4>
                <p style="color: var(--text-secondary); margin: 0;">${result.reason}</p>
            </div>

            ${result.detected_elements && result.detected_elements.length > 0 ? `
                <div style="background: rgba(255,255,255,0.8); padding: 1.5rem; border-radius: var(--radius); margin-bottom: 1rem;">
                    <h4 style="margin-bottom: 1rem; font-weight: 600;">Detected Issues</h4>
                    <ul style="margin: 0; padding-left: 1.5rem;">
                        ${result.detected_elements.map(element => `<li style="margin-bottom: 0.5rem; color: var(--text-secondary);">${element}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <div style="background: rgba(255,255,255,0.8); padding: 1.5rem; border-radius: var(--radius);">
                <h4 style="margin-bottom: 0.5rem; font-weight: 600;">Recommended Action</h4>
                <p style="color: var(--text-secondary); margin: 0; font-weight: 500;">${actionText}</p>
            </div>

            ${result.metadata ? `
                <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.3); font-size: 0.9rem; opacity: 0.8; text-align: center;">
                    Analysis completed in ${result.metadata.processing_time?.toFixed(2) || 'N/A'}s using AI Content Moderator
                </div>
            ` : ''}
        </div>
    `;

    // Update statistics after successful analysis
    setTimeout(loadStatistics, 1000);
}

// Error Display Functions
function displayPriceError(error) {
    const priceResult = document.getElementById('price-result');
    if (!priceResult) return;
    
    priceResult.innerHTML = `
        <div class="error-message">
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
                <strong>AI Analysis Temporarily Unavailable</strong>
                <p>${error}</p>
                <p style="margin-top: 1rem; font-size: 0.9rem; color: #0ea5e9;">💡 <strong>Tip:</strong> Our AI systems are continuously learning and improving. Refresh the page and try again for optimal results.</p>
                <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #0ea5e9; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    ↻ Refresh & Try Again
                </button>
            </div>
        </div>
    `;
}

function displayModerationError(error) {
    const moderationResult = document.getElementById('moderation-result');
    if (!moderationResult) return;
    
    moderationResult.innerHTML = `
        <div class="error-message">
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
                <strong>Content Analysis Failed</strong>
                <p>${error}</p>
                <p style="margin-top: 1rem; font-size: 0.9rem;">Our AI moderation systems are working to resolve this issue. Please try again in a moment.</p>
            </div>
        </div>
    `;
}

// Loading Modal Functions
function showLoadingModal(title, description) {
    const modal = document.getElementById('loading-modal');
    const titleElement = document.querySelector('#loading-modal h3');
    const textElement = document.getElementById('loading-text');
    
    if (titleElement) titleElement.textContent = title;
    if (textElement) textElement.textContent = description;
    if (modal) modal.style.display = 'block';
}

function hideLoadingModal() {
    const modal = document.getElementById('loading-modal');
    if (modal) modal.style.display = 'none';
}

// Statistics Functions
async function loadStatistics() {
    try {
        const response = await fetch('/stats');
        if (!response.ok) return;

        const stats = await response.json();
        updateStatisticsDisplay(stats);
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

function updateStatisticsDisplay(stats) {
    // Update price analysis stats
    const priceExecutions = document.getElementById('price-executions');
    const priceSuccessRate = document.getElementById('price-success-rate');
    
    if (priceExecutions && stats.price_suggestor) {
        priceExecutions.textContent = formatNumber(stats.price_suggestor.total_executions);
    }
    
    if (priceSuccessRate && stats.price_suggestor) {
        priceSuccessRate.textContent = Math.round(stats.price_suggestor.success_rate * 100) + '%';
    }

    // Update moderation stats
    const moderationExecutions = document.getElementById('moderation-executions');
    const moderationSuccessRate = document.getElementById('moderation-success-rate');
    
    if (moderationExecutions && stats.chat_moderator) {
        moderationExecutions.textContent = formatNumber(stats.chat_moderator.total_executions);
    }
    
    if (moderationSuccessRate && stats.chat_moderator) {
        moderationSuccessRate.textContent = Math.round(stats.chat_moderator.success_rate * 100) + '%';
    }
}

// Utility Functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
}

function formatMarketPosition(position) {
    const positions = {
        'underpriced': 'Underpriced - Great Deal for Buyers',
        'fairly_priced': 'Fair Market Price - Well Positioned',
        'fairly-priced': 'Fair Market Price - Well Positioned',
        'overpriced': 'Overpriced - Consider Price Reduction'
    };
    return positions[position] || position;
}

function formatModerationStatus(status) {
    const statuses = {
        'safe': 'Content Approved',
        'abusive': 'Policy Violation Detected',
        'phone_detected': 'Contact Information Detected',
        'policy_violation': 'Platform Policy Violation'
    };
    return statuses[status] || status;
}

function formatActionRecommendation(action) {
    const actions = {
        'none': 'No action required - content is safe and compliant.',
        'warn': 'Issue warning to user about policy guidelines.',
        'block': 'Block content and prevent publication.',
        'review': 'Flag for manual review by moderation team.'
    };
    return actions[action] || action;
}

function formatAgentType(type) {
    const types = {
        'price_suggestor': 'Advanced AI Pricing Engine',
        'price_suggestor_fallback': 'Fallback Pricing Algorithm',
        'price_suggestor_emergency': 'Emergency Pricing Mode'
    };
    return types[type] || 'AI System';
}

// Handle modal clicks to close
document.addEventListener('click', function(event) {
    const modal = document.getElementById('loading-modal');
    if (event.target === modal) {
        hideLoadingModal();
    }
});
