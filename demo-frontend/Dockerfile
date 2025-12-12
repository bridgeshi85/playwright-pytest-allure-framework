# ---------- 1) Build Stage ----------
FROM node:20 AS builder

WORKDIR /app

# 先复制依赖文件（便于缓存）
COPY package.json package-lock.json ./

RUN npm install

# 复制代码
COPY . .

RUN npm run build


# ---------- 2) Production Stage ----------
FROM nginx:alpine

# 将 Vite 构建后的 dist 内容复制到 Nginx 默认目录
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
