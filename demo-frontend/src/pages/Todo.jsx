import React, { useState } from "react";
import { Card, Input, Button, List, Tag, Space } from "antd";
import { useNavigate } from "react-router-dom";

const PRIORITY_MAP = {
  high: "red",
  medium: "orange",
  low: "green",
};

export default function Todo() {
  const navigate = useNavigate();
  const [items, setItems] = useState([
    { id: 1, text: "完成测试报告", priority: "high", done: false },
    { id: 2, text: "Review PR", priority: "medium", done: true },
    { id: 3, text: "更新文档", priority: "low", done: false },
  ]);
  const [newText, setNewText] = useState("");
  const [filter, setFilter] = useState("all"); // all | active | completed

  const addItem = () => {
    if (!newText.trim()) return;
    setItems([
      ...items,
      { id: Date.now(), text: newText.trim(), priority: "medium", done: false },
    ]);
    setNewText("");
  };

  const toggleItem = (id) => {
    setItems(items.map((item) =>
      item.id === id ? { ...item, done: !item.done } : item
    ));
  };

  const deleteItem = (id) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const filteredItems = items.filter((item) => {
    if (filter === "active") return !item.done;
    if (filter === "completed") return item.done;
    return true;
  });

  const stats = {
    total: items.length,
    active: items.filter((i) => !i.done).length,
    completed: items.filter((i) => i.done).length,
  };

  return (
    <div style={{ padding: 40, backgroundColor: "#f5f5f5", minHeight: "100vh" }}>
      <Card title="待办事项" style={{ maxWidth: 600, margin: "0 auto" }}>
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Input
              data-testid="input-todo"
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              onPressEnter={addItem}
              placeholder="添加新任务..."
              style={{ width: 300 }}
            />
            <Button type="primary" onClick={addItem} data-testid="btn-add-todo">
              添加
            </Button>
          </Space>
        </div>

        <div style={{ marginBottom: 16 }} data-testid="todo-stats">
          <Space>
            <Button
              type={filter === "all" ? "primary" : "default"}
              onClick={() => setFilter("all")}
              data-testid="filter-all"
            >
              全部 ({stats.total})
            </Button>
            <Button
              type={filter === "active" ? "primary" : "default"}
              onClick={() => setFilter("active")}
              data-testid="filter-active"
            >
              待完成 ({stats.active})
            </Button>
            <Button
              type={filter === "completed" ? "primary" : "default"}
              onClick={() => setFilter("completed")}
              data-testid="filter-completed"
            >
              已完成 ({stats.completed})
            </Button>
          </Space>
        </div>

        <List
          data-testid="todo-list"
          dataSource={filteredItems}
          renderItem={(item) => (
            <List.Item
              data-testid={`todo-item-${item.id}`}
              actions={[
                <Button
                  size="small"
                  danger
                  onClick={() => deleteItem(item.id)}
                  data-testid={`btn-delete-${item.id}`}
                >
                  删除
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <input
                      type="checkbox"
                      checked={item.done}
                      onChange={() => toggleItem(item.id)}
                      data-testid={`checkbox-todo-${item.id}`}
                    />
                    <span
                      style={{
                        textDecoration: item.done ? "line-through" : "none",
                        color: item.done ? "#999" : "#333",
                      }}
                    >
                      {item.text}
                    </span>
                  </Space>
                }
                description={
                  <Tag color={PRIORITY_MAP[item.priority]} data-testid={`tag-priority-${item.id}`}>
                    {item.priority}
                  </Tag>
                }
              />
            </List.Item>
          )}
        />

        <div style={{ marginTop: 24 }}>
          <a onClick={() => navigate("/home")} style={{ cursor: "pointer", color: "#1677ff" }}>
            ← 返回首页
          </a>
        </div>
      </Card>
    </div>
  );
}
