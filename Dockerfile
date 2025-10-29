# Use a slim Python base image
FROM python:3.11-slim

# System deps (optional, can help with some builds)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi "uvicorn[standard]"

# Copy the rest of the app
COPY . /app

# Make sure the app points to the internal MySQL service (hostname: db)
# The code in backend/database.py currently uses 'localhost:3306'; replace it with 'db:3306'
RUN sed -i 's/localhost:3306/db:3306/g' backend/database.py || true

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
