from flask import Flask, request, Response
import requests
import logging
import os

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
def proxy(path):
    # Log the incoming request
    logging.info(f"Incoming request: {request.method} {request.url}")

    # Ensure the path starts with a valid domain
    if not path:
        logging.error("No valid path supplied.")
        return Response("Error: No valid path supplied.", status=400)

    # Construct the target URL, assuming the full URL is provided in the path
    url = f"https://{path}"
    logging.info(f"Target URL: {url}")

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        logging.info(f"Received response: {resp.status_code} {resp.reason}")

        # Filter out specific headers before returning the response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]

        # Return the response to the client
        response = Response(resp.content, resp.status_code, headers)
        return response

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to {url} failed: {e}")
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
