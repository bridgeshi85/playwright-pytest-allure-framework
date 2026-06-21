import React from "react";
import { Card, Button, Space } from "antd";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#f5f5f5",
      }}
    >
      <Card title="首页" style={{ width: 400 }}>
        <h2 data-testid="welcome-text">欢迎来到 Demo 系统</h2>
        <Space direction="vertical" style={{ width: "100%", marginTop: 16 }}>
          <Button block onClick={() => navigate("/dashboard")} data-testid="nav-dashboard">
            📊 Dashboard（延迟渲染）
          </Button>
          <Button block onClick={() => navigate("/profile")} data-testid="nav-profile">
            👤 用户资料（断言 / 元素失败）
          </Button>
          <Button block onClick={() => navigate("/shop")} data-testid="nav-shop">
            🛒 商品列表（API 404）
          </Button>
        </Space>
      </Card>
    </div>
  );
}
