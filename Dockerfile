FROM python:3.10

WORKDIR /app

COPY . .

CMD ["python3", "proxy_server.py"]
