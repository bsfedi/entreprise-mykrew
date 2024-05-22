#!/bin/bash
# Check if port and service name are provided as arguments
# Check if port and service name are provided as arguments
if [ $# -ne 6 ]; then
    echo "Usage: $0 <PORT> <SERVICE_NAME> <MONGO_URI> <CLIENT_NAME> <FRONT_PORT> <BACK_URL>"
    exit 1
fi

port=$1
service_name=$2
mongo_uri=$3
client_name=$4
front_port=$5
back_url=$6


cd ..

mkdir $service_name

cd $service_name

git  clone https://github.com/bsfedi/Mykrew-backend.git
git  clone -b  changes-after-test https://github.com/bsfedi/Mykrew-frontend.git


# Change directory to mykrew-backend
cd Mykrew-backend || exit



cat << EOF > docker-compose.yml
version: "3.2"
services:
  $service_name:
    build: .
    ports:
      - "$port:$port"
EOF

echo "docker-compose.yml file has been generated successfully!"

# Generate Dockerfile
cat << EOF > dockerfile
# Use the official Node.js 14 image as a base
FROM node:14

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Expose the port on which your Express.js app will run (this is just informative)
EXPOSE $port

# Modify environment variables
RUN sed -i "s|PORT=.*|PORT=$port|g" .env
RUN sed -i "s|MONGO_URI=.*|MONGO_URI=$mongo_uri|g" .env

# Rebuild bcrypt
RUN npm rebuild bcrypt --build-from-source


# Start the Express.js app when the container launches
CMD ["node", "server.js"]
EOF

echo "Dockerfile has been generated successfully!"
docker-compose up -d
docker-compose start



# Change directory to mykrew
cd ../Mykrew-frontend || exit

# Generate Dockerfile
cat << EOF > nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen $front_port;
        server_name localhost;  # Replace with your custom URL

        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files \$uri \$uri/ /index.html;
        }
    }
}

EOF


# Generate Dockerfile
cat << EOF > Dockerfile
# Use an official Node.js runtime as a parent image
FROM node:14 as builder

# Set the working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Set environment variable for client name
# Set environment variable for client name


# Copy the current directory contents into the container at /app
COPY . .

# Modify environment.ts with the dynamic URL
RUN sed -i "s|baseUrl: '.*'|baseUrl: '${back_url}'|g" src/environments/environment.ts && \
    echo "Updated base URL in environment.ts to: https://new-base-url.com/"


RUN sed -i "s|default: '.*'|default: '${client_name}'|g" src/environments/environment.ts && \
    echo "Updated CLIENT_NAME in environment.ts to: ${client_name}"

# Build the Angular app
RUN npm run build --prod

# Use Nginx as a web server for the Angular app
FROM nginx:latest

# Copy the built Angular app to the default Nginx public directory
COPY --from=builder /app/dist/mykrew /usr/share/nginx/html

# Copy the custom nginx.conf to the Nginx container
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 90 to the outside world
EXPOSE $front_port

# Start Nginx when the container launches
CMD ["nginx", "-g", "daemon off;"]

EOF

echo "Dockerfile has been generated successfully!"

# Execute the docker build command
docker build -t $client_name --build-arg PORT=$front_port  --build-arg  back_url=$back_url -f Dockerfile .

docker run -d -p ${front_port}:${front_port}  $client_name


echo "Frontend container has been started successfully in detached mode!"