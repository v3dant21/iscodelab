FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV API_INTERNAL_URL=http://backend:8000
RUN npm run build
CMD ["npx", "next", "start", "--hostname", "0.0.0.0"]
