FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

<<<<<<< HEAD:backend/Dockerfile
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
=======
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
>>>>>>> db6c30c (fix port binding):backend/dockerfile
