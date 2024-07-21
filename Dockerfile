# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed system dependencies here
# Example: RUN apt-get update && apt-get install -y some-package

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project's files into the container
COPY . /app

# Make port 80 available to the world outside this container
#EXPOSE 80

# Define environment variable for dynamic configuration
ENV BUY_PRICE 67000
ENV SELL_PRICE 70000
ENV AMOUNT_CURRENCY 100

# Command to run the application
CMD ["python", "SwingTrading.py"]