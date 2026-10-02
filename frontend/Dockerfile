# Stage 1: Build Angular Application
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency specifications
COPY package*.json ./

# Install npm dependencies
RUN npm ci

# Copy full frontend source code
COPY . .

# Build production bundle with environment replacements
RUN npm run build -- --configuration production

# Stage 2: Serve using Nginx
FROM nginx:alpine

# Remove default static files
RUN rm -rf /usr/share/nginx/html/*

# Copy built browser bundle from builder stage
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
