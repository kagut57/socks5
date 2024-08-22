from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/', methods=['GET'])
def proxy():
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Forward the request to the target URL
        response = requests.get(target_url, stream=True)
        
        # Return the response from the target URL
        return (response.raw.read(), response.status_code, response.headers.items())
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
