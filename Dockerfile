FROM python:3.10

WORKDIR /app

COPY . .

EXPOSE 10000

CMD ["python3", "proxy_server.py"]
