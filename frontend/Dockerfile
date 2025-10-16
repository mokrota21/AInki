FROM node:20-alpine

WORKDIR /app

# Install dependencies (separate for caching)
COPY package*.json ./

# Copy source
COPY . .

RUN npm ci


EXPOSE 5173

# Default command to run Vite dev server, listening on all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

