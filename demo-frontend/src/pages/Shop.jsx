import React, { useState, useEffect } from "react";
import { Card, List, Alert, Spin } from "antd";
import { useNavigate } from "react-router-dom";

/**
 * Shop 页面 — 演示 flaky_env 失败场景：
 *
 * 页面启动时调用 /api/products，该接口在 demo 环境中不存在（404）。
 * 测试若断言商品列表可见（data-testid="product-list"），
 * 将因 API 失败导致列表不渲染而报 TimeoutError。
 * trace 中同时会有 network 4xx 记录，AI 可据此判断为环境问题。
 */
export default function Shop() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/products")
      .then((res) => {
        if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((data) => {
        setProducts(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load products:", err.message);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: 40, backgroundColor: "#f5f5f5", minHeight: "100vh" }}>
      <h1>商品列表</h1>

      {loading && (
        <div style={{ textAlign: "center", marginTop: 80 }}>
          <Spin size="large" />
        </div>
      )}

      {error && (
        <Alert
          data-testid="api-error"
          type="error"
          message="加载失败"
          description={`无法获取商品数据：${error}`}
          showIcon
          style={{ marginTop: 16 }}
        />
      )}

      {/* 仅当 API 成功时渲染；API 返回 404 时此元素不存在 */}
      {!loading && !error && (
        <List
          data-testid="product-list"
          grid={{ gutter: 16, column: 3 }}
          dataSource={products}
          renderItem={(item) => (
            <List.Item>
              <Card title={item.name}>
                <p data-testid={`product-price-${item.id}`}>¥{item.price}</p>
              </Card>
            </List.Item>
          )}
          style={{ marginTop: 16 }}
        />
      )}

      <div style={{ marginTop: 24 }}>
        <a onClick={() => navigate("/home")} style={{ cursor: "pointer", color: "#1677ff" }}>
          ← 返回首页
        </a>
      </div>
    </div>
  );
}
