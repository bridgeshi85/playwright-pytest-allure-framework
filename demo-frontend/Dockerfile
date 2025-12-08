# ---------- 1) Build Stage ----------
FROM node:20 AS builder

WORKDIR /app

# 先复制依赖文件（便于缓存）
COPY package.json package-lock.json ./

RUN npm install

# 再复制代码
COPY . .

# 构建前端
RUN npm run build


# ---------- 2) Production Stage ----------
FROM nginx:alpine

# 将 Vite 构建后的 dist 内容复制到 Nginx 默认目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口（Nginx 默认 80）
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
