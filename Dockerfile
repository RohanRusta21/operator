FROM python:3.9-slim

# Install dependencies
RUN pip install kopf kubernetes

# Create app directory
WORKDIR /app

# Copy operator code (with new name)
COPY mypod_operator.py .

# Run the operator
CMD ["python", "mypod_operator.py"]