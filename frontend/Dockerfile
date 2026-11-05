# Use Node.js base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY . .

# Build React application
RUN npm run build

# Install lightweight static web server
RUN npm install -g serve

# Expose frontend port
EXPOSE 5173

# Start frontend
CMD ["serve", "-s", "dist", "-l", "5173"]