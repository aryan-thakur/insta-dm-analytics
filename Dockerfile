# 1. Base Image: Use an official Python image. Choose a specific version for reproducibility.
#    The 'slim' version is smaller.
FROM python:3.10-slim

# 2. Set Environment Variables (Optional but good practice)
ENV PYTHONDONTWRITEBYTECODE 1 # Prevents python from writing .pyc files
ENV PYTHONUNBUFFERED 1      # Prevents python from buffering stdout/stderr

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install dependencies
#    Copy requirements first to leverage Docker cache. If requirements.txt doesn't change,
#    this layer won't be rebuilt, speeding up subsequent builds if only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code into the container's working directory
#    Make sure you have a .dockerignore file to avoid copying unnecessary things.
COPY . .

# 6. (Optional) Expose port if you were running a web server (e.g., Flask, Jupyter)
# EXPOSE 8888

# 7. Default command (optional): What runs when the container starts *if not overridden*
#    For development, it's often better to override this in docker-compose.yml
#    or use 'docker-compose run' or 'docker-compose exec'.
# CMD ["python", "src/main.py"]