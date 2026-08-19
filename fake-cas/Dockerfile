FROM python:3.12-slim

WORKDIR /app

COPY app.py ./app.py
COPY users.json ./users.json

EXPOSE 8380

CMD ["python", "app.py"]
