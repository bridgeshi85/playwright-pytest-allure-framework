# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /workspace

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# 安装 Playwright 浏览器及依赖
RUN playwright install --with-deps chromium

# 创建 Allure 报告目录
RUN mkdir -p /workspace/allure-results /workspace/allure-report

# 安装 Allure 命令行工具（可选，如果需要在容器内生成报告）
RUN wget https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz && \
    tar -zxvf allure-2.24.1.tgz -C /opt/ && \
    ln -s /opt/allure-2.24.1/bin/allure /usr/bin/allure && \
    rm allure-2.24.1.tgz

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV ALLURE_RESULTS_DIR=/workspace/allure-results

# 默认命令（Jenkins 会覆盖）
CMD ["/bin/bash"]