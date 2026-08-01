import React, { useState, useEffect } from "react";
import { Card, Button, Space, Badge } from "antd";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [notificationCount, setNotificationCount] = useState(3);

  useEffect(() => {
    // 模拟未读消息数量
    const count = parseInt(localStorage.getItem("notificationCount") || "3");
    setNotificationCount(count);
  }, []);

  const handleClearNotifications = () => {
    setNotificationCount(0);
    localStorage.setItem("notificationCount", "0");
  };

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
        
        <div style={{ marginBottom: 16 }}>
          <Badge count={notificationCount} data-testid="notification-badge">
            <span style={{ fontSize: 14 }}>未读消息</span>
          </Badge>
          {notificationCount > 0 && (
            <Button 
              size="small" 
              onClick={handleClearNotifications}
              data-testid="btn-clear-notifications"
              style={{ marginLeft: 8 }}
            >
              清除
            </Button>
          )}
        </div>

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
