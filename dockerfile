FROM python:3.7-slim

# Set working directory
WORKDIR /usr/src/app

# Copy the source code
COPY . .

# Install the app dependencies and create database directory
RUN pip install --no-cache-dir -r requirements.txt \
    # Absolute path: /usr/src/app/db
    && mkdir db

ENTRYPOINT [ "python", "/usr/src/app/twitter-stream-bot-data-gatherer/main.py" ]
