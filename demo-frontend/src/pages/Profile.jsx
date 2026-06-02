import React from "react";
import { Card, Descriptions, Button } from "antd";
import { useNavigate } from "react-router-dom";

/**
 * Profile 页面 — 演示两种 real_bug 失败场景：
 *
 * 1. real_bug (assertion 失败)：
 *    页面 data-testid="user-email" 实际内容是 "admin@example.com"
 *    测试若断言 to_have_text("admin@demo.com") 将报 AssertionError
 *
 * 2. real_bug (element not found)：
 *    UI 重构后编辑按钮 testid 从 "btn-edit" 改为 "btn-edit-profile"
 *    测试若还用旧 testid get_by_test_id("btn-edit") 将报
 *    "locator resolved to 0 elements"
 */
export default function Profile() {
  const navigate = useNavigate();

  return (
    <div style={{ padding: 40, backgroundColor: "#f5f5f5", minHeight: "100vh" }}>
      <h1>用户资料</h1>
      <Card style={{ maxWidth: 600 }}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="用户名">
            <span data-testid="user-name">admin</span>
          </Descriptions.Item>
          <Descriptions.Item label="邮箱">
            {/* 实际值：admin@example.com；测试中会断言 admin@demo.com → 失败 */}
            <span data-testid="user-email">admin@example.com</span>
          </Descriptions.Item>
          <Descriptions.Item label="角色">
            <span data-testid="user-role">超级管理员</span>
          </Descriptions.Item>
        </Descriptions>

        {/* UI 重构：testid 已从 btn-edit 改为 btn-edit-profile；旧测试会找不到元素 */}
        <Button
          type="primary"
          data-testid="btn-edit-profile"
          style={{ marginTop: 16 }}
        >
          编辑资料
        </Button>
      </Card>

      <div style={{ marginTop: 24 }}>
        <a onClick={() => navigate("/home")} style={{ cursor: "pointer", color: "#1677ff" }}>
          ← 返回首页
        </a>
      </div>
    </div>
  );
}
