import requests
import logging
import os
from flask import Flask, request, redirect, jsonify
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    # Returning 204 No Content for favicon requests or you could serve a local favicon file
    return '', 204

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # Extract the target URL from the query parameters
    target_url = request.args.get('url')
    
    if not target_url:
        return "No valid URL supplied.", 400
    
    # Parse the URL to ensure it’s correctly formatted
    parsed_url = urlparse(target_url)
    
    # If the URL does not include a scheme, add http by default
    if not parsed_url.scheme:
        target_url = 'http://' + target_url
        parsed_url = urlparse(target_url)
    
    # Reconstruct the target URL to ensure it is correctly formed
    target_url = urlunparse(parsed_url)
    
    try:
        # Forward the request to the target URL
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )
        
        # Prepare the response to forward back to the client
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = resp.content
        
        # Handle redirects if necessary
        if 300 <= resp.status_code < 400:
            location = resp.headers.get('Location')
            if location:
                location = location.replace(parsed_url.netloc, request.host)
                return redirect(location, code=resp.status_code)

        return response, resp.status_code, headers

    except requests.exceptions.RequestException as e:
        return f"Request to {target_url} failed: {str(e)}", 500

if __name__ == '__main__':
    # Running the Flask app
    app.run(host='0.0.0.0', port=10000)
