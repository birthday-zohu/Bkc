# api/index.py
from flask import Flask, request, jsonify
import requests
import time
import re

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": True,
        "message": "Number Info API",
        "endpoint": "/api?num=MOBILE_NUMBER"
    })

@app.route('/api')
def get_number_info():
    # Get phone number from query parameter
    num = request.args.get('num')
    
    # Validate phone number
    if not num or not re.match(r'^\d{10}$', num):
        return jsonify({
            "status": False,
            "results": []
        }), 400
    
    MAX_RETRIES = 5
    RETRY_DELAY = 1  # 1 second
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempt {attempt + 1} for number: {num}")
            
            # Make request to the original API
            response = requests.get(
                f'https://numinfo-proxy-api.vercel.app/?num={num}',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check if we got valid results
            if data and data.get('results') and isinstance(data['results'], list) and len(data['results']) > 0:
                # Transform the data to clean format
                transformed_results = []
                for item in data['results']:
                    # Create clean result object
                    clean_result = {
                        'mobile': item.get('mobile', num),
                        'name': item.get('name', ''),
                        'fname': item.get('fname', ''),
                        'address': item.get('address', ''),
                        'alt': item.get('alt', ''),
                        'circle': item.get('circle', ''),
                        'id': item.get('id', ''),
                        'email': item.get('email', '')
                    }
                    transformed_results.append(clean_result)
                
                # Return successful response WITHOUT error field
                return jsonify({
                    "status": True,
                    "results": transformed_results
                })
            
            # If no results found, retry
            print(f"No results found, retrying... (Attempt {attempt + 1})")
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {str(e)}")
        except (KeyError, ValueError) as e:
            print(f"Data parsing error on attempt {attempt + 1}: {str(e)}")
        
        # Wait before retrying (except on last attempt)
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    # If all retries failed
    return jsonify({
        "status": False,
        "results": []
    })

# CORS support
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True)
