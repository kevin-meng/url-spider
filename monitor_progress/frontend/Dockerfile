FROM node:18-alpine as build

WORKDIR /app

# 添加中国大陆镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache tzdata
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 配置 npm 镜像源
RUN npm config set registry https://registry.npmmirror.com

# 先复制 package.json 和 package-lock.json
COPY package.json package-lock.json* ./

# 清理可能存在的缓存
RUN rm -rf node_modules && rm -f package-lock.json

# 安装依赖
RUN npm install --force --no-cache

# 复制源代码文件（排除 node_modules）
COPY src/ ./src/
COPY public/ ./public/
COPY package.json ./
COPY package-lock.json* ./
COPY .npmrc ./
COPY nginx.conf ./
COPY Dockerfile ./
COPY README.md* ./
COPY README.* ./
COPY readme.md* ./
COPY readme.* ./

# 构建
RUN npm run build

FROM nginx:alpine

RUN apk add --no-cache tzdata
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY --from=build /app/build /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
