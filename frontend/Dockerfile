# Frontend image: Streamlit user interface
FROM python:3.11-slim

# All following commands run inside /app in the container
WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app code
COPY . .

# Streamlit's default port
EXPOSE 8501

# 0.0.0.0 lets the browser on the host reach Streamlit through the port mapping
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
