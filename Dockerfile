# Library Management System - Group 06
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Ho_Chi_Minh \
    LMS_HOST=0.0.0.0 \
    LMS_PORT=5000 \
    LMS_DB_PATH=/app/instance/library.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pytest.ini .
COPY src ./src
COPY tests ./tests

RUN mkdir -p /app/instance

EXPOSE 5000

CMD ["python", "src/app.py"]
