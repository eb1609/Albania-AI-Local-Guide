# --- STAGE 1: Build the Vite Frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /frontend

# Copy frontend package files from the correct folder path
COPY albania-local-guide/package.json albania-local-guide/package-lock.json* ./
RUN npm ci

# Copy the rest of the frontend files and build
COPY albania-local-guide/ ./
RUN npm run build

# --- STAGE 2: Build the Final Python Backend & Serve Both ---
FROM python:3.13-slim
WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY backend/ .

# Copy the static frontend assets from Stage 1 into the backend's static directory
COPY --from=frontend-build /frontend/dist /app/static

EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]