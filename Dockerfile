FROM python:3.10-slim

WORKDIR /app

# Copy everything
COPY . .

# Install dependencies from src folder
RUN pip install --no-cache-dir -r src/requirements.txt

# Expose your fixed port
EXPOSE 8002

# Run your app from src
CMD ["python", "src/app.py"]
