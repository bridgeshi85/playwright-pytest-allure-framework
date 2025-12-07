import yaml
import os


def load_config(env="default"):
    """加载指定环境的配置文件，若不存在则加载默认配置文件"""
    file_path = f"./configs/env.{env}.yaml"
    if not os.path.exists(file_path):
        file_path = "./configs/env.default.yaml"

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
