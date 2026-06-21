import React, { useState, useEffect } from "react";
import { Card, Statistic, Row, Col, Spin } from "antd";
import { useNavigate } from "react-router-dom";
import { ArrowUpOutlined } from "@ant-design/icons";

/**
 * Dashboard 页面
 * 故意在 3 秒后才渲染统计数据，用于演示 flaky_element 失败场景：
 * 测试若使用过短的 timeout（< 3000ms）等待 data-testid="stat-users"，
 * 将触发 TimeoutError。
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    // 模拟异步数据加载，3 秒后显示统计数据
    const timer = setTimeout(() => setLoaded(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div style={{ padding: 40, backgroundColor: "#f5f5f5", minHeight: "100vh" }}>
      <h1>Dashboard</h1>
      <p style={{ color: "#888" }}>数据加载中，请稍候…（3 秒后显示）</p>

      {loaded ? (
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="活跃用户"
                value={1128}
                prefix={<ArrowUpOutlined />}
                valueStyle={{ color: "#3f8600" }}
                data-testid="stat-users"
              />
              {/* data-testid 挂在外层 div 上，Antd Statistic 不透传 */}
              <div data-testid="stat-users" style={{ display: "none" }}>1128</div>
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="今日订单" value={93} data-testid="stat-orders" />
              <div data-testid="stat-orders" style={{ display: "none" }}>93</div>
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="总收入" value={9280} prefix="¥" data-testid="stat-revenue" />
              <div data-testid="stat-revenue" style={{ display: "none" }}>9280</div>
            </Card>
          </Col>
        </Row>
      ) : (
        <div style={{ textAlign: "center", marginTop: 80 }}>
          <Spin size="large" />
        </div>
      )}

      <div style={{ marginTop: 24 }}>
        <a onClick={() => navigate("/home")} style={{ cursor: "pointer", color: "#1677ff" }}>
          ← 返回首页
        </a>
      </div>
    </div>
  );
}
