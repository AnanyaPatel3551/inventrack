FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Runtime: nginx-unprivileged runs as the non-root "nginx" user (uid 101) and listens on 8080
FROM nginxinc/nginx-unprivileged:1.27-alpine
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app/dist /usr/share/nginx/html
COPY default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
