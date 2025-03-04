from flask import Flask, request, jsonify
import sys
import os

# Add the root directory to the path so we can import TrendAnalyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TrendAnalyzer import TrendAnalyzer

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_trend():
    """
    Analyzes a trend based on the provided keyword
    """
    try:
        data = request.get_json()
        
        if not data or 'keyword' not in data:
            return jsonify({'error': 'Missing keyword parameter'}), 400
            
        keyword = data['keyword']
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_trend_with_ai(keyword)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trends', methods=['GET'])
def get_trending():
    """
    Returns a list of currently trending topics
    """
    try:
        analyzer = TrendAnalyzer()
        trends = analyzer.get_top_trends()
        
        return jsonify({
            'success': True,
            'trends': trends
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    })

# This conditional is used when running the app locally
if __name__ == '__main__':
    app.run(debug=True)

# Export the Flask app for Vercel serverless functions
# This 'app' variable is what Vercel looks for to serve the application
