# Stage 1: Build the Vue application
FROM node:20-slim AS build-stage

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package.json and pnpm-lock.yaml (if it exists)
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy the rest of the frontend code
COPY . .

# Build the application
RUN pnpm run build-only

# Stage 2: Serve the application with Nginx
FROM nginx:stable-alpine AS production-stage

# Copy the build output from the build-stage to Nginx's html directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy a default nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
