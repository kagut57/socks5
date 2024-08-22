FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install Flask requests

CMD ["python3", "proxy_server.py"]
