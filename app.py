import os
import logging
from flask import Flask, request, jsonify, render_template
from flask.logging import default_handler
from agents.price_suggestor import PriceSuggestorAgent
from agents.chat_moderator import ChatModeratorAgent
from utils.data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize agents
price_agent = PriceSuggestorAgent()
chat_agent = ChatModeratorAgent()
data_processor = DataProcessor()

@app.route('/')
def index():
    """Render the main page with both agent interfaces"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test data processor
        data_processor.load_data()
        return jsonify({
            'status': 'healthy',
            'agents': {
                'price_suggestor': 'ready',
                'chat_moderator': 'ready'
            },
            'data': {
                'records_loaded': len(data_processor.df) if data_processor.df is not None else 0
            }
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/stats')
def get_stats():
    """Get agent statistics"""
    try:
        return jsonify({
            'price_suggestor': {
                'total_executions': price_agent.execution_count,
                'success_rate': price_agent.success_rate,
                'avg_processing_time': price_agent.avg_processing_time
            },
            'chat_moderator': {
                'total_executions': chat_agent.execution_count,
                'success_rate': chat_agent.success_rate,
                'avg_processing_time': chat_agent.avg_processing_time
            }
        }), 200
    except Exception as e:
        app.logger.error(f"Stats retrieval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/negotiate', methods=['POST'])
def negotiate_price():
    """Price suggestion endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'category', 'brand', 'condition', 'age_months', 'asking_price', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Process the price suggestion
        result = price_agent.process(data)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
        
    except ValueError as e:
        app.logger.warning(f"Validation error in negotiate: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in negotiate endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/moderate', methods=['POST'])
def moderate_chat():
    """Chat moderation endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'message' not in data:
            return jsonify({'error': 'Missing required field: message'}), 400
        
        # Process the moderation
        result = chat_agent.process(data)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
        
    except ValueError as e:
        app.logger.warning(f"Validation error in moderate: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in moderate endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/batch/negotiate', methods=['POST'])
def batch_negotiate():
    """Batch price suggestion endpoint"""
    try:
        data = request.get_json()
        
        if 'items' not in data or not isinstance(data['items'], list):
            return jsonify({'error': 'Missing or invalid items array'}), 400
        
        results = []
        for i, item in enumerate(data['items']):
            try:
                result = price_agent.process(item)
                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in batch negotiate endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/batch/moderate', methods=['POST'])
def batch_moderate():
    """Batch moderation endpoint"""
    try:
        data = request.get_json()
        
        if 'messages' not in data or not isinstance(data['messages'], list):
            return jsonify({'error': 'Missing or invalid messages array'}), 400
        
        results = []
        for i, message_data in enumerate(data['messages']):
            try:
                result = chat_agent.process(message_data)
                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in batch moderate endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@app.route('/testing')
def testing():
    """Render the testing page"""
    return render_template('testing.html')

@app.route('/api/stats/detailed')
def get_detailed_stats():
    """Get detailed statistics for dashboard"""
    try:
        # Calculate additional metrics
        total_executions = price_agent.execution_count + chat_agent.execution_count
        overall_success_rate = (
            (price_agent.execution_count * price_agent.success_rate + 
             chat_agent.execution_count * chat_agent.success_rate) / 
            max(total_executions, 1)
        )
        
        avg_response_time = (
            (price_agent.avg_processing_time + chat_agent.avg_processing_time) / 2
        )
        
        return jsonify({
            'price_suggestor': {
                'total_executions': price_agent.execution_count,
                'success_rate': price_agent.success_rate,
                'avg_processing_time': price_agent.avg_processing_time,
                'last_execution': getattr(price_agent, 'last_execution_time', None)
            },
            'chat_moderator': {
                'total_executions': chat_agent.execution_count,
                'success_rate': chat_agent.success_rate,
                'avg_processing_time': chat_agent.avg_processing_time,
                'last_execution': getattr(chat_agent, 'last_execution_time', None)
            },
            'overall': {
                'total_executions': total_executions,
                'success_rate': overall_success_rate,
                'avg_response_time': avg_response_time
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Detailed stats retrieval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/realtime')
def get_realtime_metrics():
    """Get real-time performance metrics"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Generate sample hourly data for the last 24 hours
        now = datetime.now()
        hourly_labels = []
        price_data = []
        moderation_data = []
        
        for i in range(24):
            hour_time = now - timedelta(hours=23-i)
            hourly_labels.append(hour_time.strftime('%H:00'))
            price_data.append(random.randint(5, 50))
            moderation_data.append(random.randint(2, 30))
        
        # Mock confidence distribution
        confidence_distribution = {
            'high': random.randint(60, 80),
            'medium': random.randint(15, 25),
            'low': random.randint(5, 15)
        }
        
        return jsonify({
            'hourly_requests': {
                'labels': hourly_labels,
                'price_analysis': price_data,
                'moderation': moderation_data
            },
            'confidence_distribution': confidence_distribution,
            'p95_response_time': round(random.uniform(1.5, 3.0), 2),
            'avg_confidence': round(random.uniform(0.75, 0.95), 2),
            'high_confidence_rate': round(random.uniform(0.70, 0.85), 2)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Real-time metrics failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/insights')
def get_market_insights():
    """Get live market data insights"""
    try:
        # Load market data for insights
        df = data_processor.load_data()
        
        # Top categories by volume
        top_categories = df['category'].value_counts().head(5).to_dict()
        top_categories_list = [{'name': k, 'count': v} for k, v in top_categories.items()]
        
        # Price trends (mock data for demo)
        import random
        price_trends = [
            {'category': 'Mobile', 'change': round(random.uniform(-5, 5), 1), 'direction': 'up' if random.random() > 0.5 else 'down'},
            {'category': 'Laptop', 'change': round(random.uniform(-3, 8), 1), 'direction': 'up' if random.random() > 0.5 else 'down'},
            {'category': 'Electronics', 'change': round(random.uniform(-2, 4), 1), 'direction': 'up' if random.random() > 0.5 else 'down'}
        ]
        
        # Fraud alerts (mock data)
        fraud_alerts = [
            {'type': 'Suspicious Pricing', 'count': random.randint(2, 8), 'severity': 'medium'},
            {'type': 'Contact Info Violations', 'count': random.randint(1, 5), 'severity': 'low'},
            {'type': 'Duplicate Listings', 'count': random.randint(0, 3), 'severity': 'high'}
        ]
        
        return jsonify({
            'top_categories': top_categories_list,
            'price_trends': price_trends,
            'fraud_alerts': fraud_alerts,
            'market_health': {
                'status': 'healthy',
                'confidence': 0.87
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Market insights failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity/stream')
def get_activity_stream():
    """Get recent activity stream"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Generate mock activity data
        activities = []
        activity_types = [
            {'type': 'price_analysis', 'title': 'Price Analysis Completed', 'details': 'iPhone 12 Pro - Suggested range: ₹35,000-42,000'},
            {'type': 'moderation', 'title': 'Content Moderation', 'details': 'Message flagged for phone number detection'},
            {'type': 'fraud_detection', 'title': 'Fraud Alert', 'details': 'Suspicious pricing pattern detected'},
            {'type': 'batch_processing', 'title': 'Bulk Analysis', 'details': '50 items processed successfully'},
            {'type': 'system', 'title': 'System Update', 'details': 'AI model performance optimized'}
        ]
        
        for i in range(20):
            activity = random.choice(activity_types).copy()
            activity['timestamp'] = (datetime.now() - timedelta(minutes=random.randint(1, 180))).isoformat()
            activity['id'] = f"activity_{i}"
            activities.append(activity)
        
        return jsonify(activities), 200
        
    except Exception as e:
        app.logger.error(f"Activity stream failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity/recent')
def get_recent_activity():
    """Get recent activity updates"""
    try:
        import random
        from datetime import datetime
        
        # Simulate new activities
        if random.random() > 0.7:  # 30% chance of new activity
            activities = [{
                'type': 'price_analysis',
                'title': 'New Price Analysis',
                'details': f'Product analyzed at {datetime.now().strftime("%H:%M")}',
                'timestamp': datetime.now().isoformat(),
                'id': f"activity_{datetime.now().timestamp()}"
            }]
        else:
            activities = []
        
        return jsonify(activities), 200
        
    except Exception as e:
        app.logger.error(f"Recent activity failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
