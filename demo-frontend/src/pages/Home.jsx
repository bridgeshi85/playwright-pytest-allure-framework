import React from "react";
import { Card } from "antd";

export default function Home() {
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
      <Card title="首页">
        <h2 data-testid="welcome-text">欢迎来到 Demo 系统</h2>
      </Card>
    </div>
  );
}
