FROM jenkins/jenkins:lts

# 以root用户运行，确保有权限访问docker.sock
USER root 

# -------- Install Docker CLI --------
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# 使用官方jenkins镜像源
ENV JENKINS_UC="https://updates.jenkins.io"
ENV JENKINS_UC_DOWNLOAD="https://updates.jenkins.io"
ENV JENKINS_PLUGIN_INFO="https://updates.jenkins.io/plugin-versions.json"

# -------- Install Jenkins plugins (as root) --------
COPY plugins.txt /usr/share/jenkins/plugins.txt
RUN jenkins-plugin-cli --verbose --plugin-file /usr/share/jenkins/plugins.txt

EXPOSE 8080
