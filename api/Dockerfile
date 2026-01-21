from python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN playwright install --with-deps chromium
EXPOSE 5000
CMD ["python3", "main.py"]
