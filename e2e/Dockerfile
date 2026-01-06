# E2E Testing Dockerfile with Playwright
FROM mcr.microsoft.com/playwright:v1.42.0-jammy

WORKDIR /e2e

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy test files
COPY . .

# Create auth directory
RUN mkdir -p .auth

# Default command
CMD ["npm", "test"]
