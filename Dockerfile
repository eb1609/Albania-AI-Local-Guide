# --- STAGE 1: Build the React/Vite Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package definitions first to utilize caching
COPY albania-local-guide/package*.json ./
RUN npm install

# Copy the frontend code and build it
COPY albania-local-guide/ ./
RUN npm run build

# --- STAGE 2: Build the FastAPI Backend & Serve Everything ---
FROM python:3.11-slim
WORKDIR /app

# Install Python production dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ .

# CRITICAL FIX: Pull the build artifacts from Stage 1 into the "static" folder FastAPI expects
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose port and start Uvicorn
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]