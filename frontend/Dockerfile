# Frontend Dockerfile for LifeGraph
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Expose port
EXPOSE 5173

# Development command (overridden in docker-compose for dev)
CMD ["npm", "run", "dev", "--", "--host"]
