# 1. 使用 Playwright 官方最新的 Python 镜像
FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

# 2. 设置工作目录
WORKDIR /workspace

# 3. 复制依赖文件
COPY requirements.txt .

# 4. 安装业务依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. 复制你的测试代码和配置文件到镜像中
COPY . /workspace/

CMD ["/bin/bash"]