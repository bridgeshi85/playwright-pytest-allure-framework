import React, { useState } from "react";
import { Button, Input, Card, message, Checkbox } from "antd";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const handleLogin = () => {
    if (username === "admin" && password === "123456") {
      if (rememberMe) {
        localStorage.setItem("remembered_user", username);
      }
      message.success("登录成功");
      navigate("/home");
    } else {
      message.error("用户名或密码错误");
    }
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
      <Card title="Demo 登录页面" bordered={true}>
        <label>用户名：</label>
        <Input
          data-testid="input-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <label style={{ marginTop: 10 }}>密码：</label>
        <Input.Password
          data-testid="input-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <div style={{ marginTop: 10 }}>
          <Checkbox
            data-testid="checkbox-remember"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
          >
            记住我
          </Checkbox>
        </div>

        <Button
          type="primary"
          data-testid="btn-login"
          block
          style={{ marginTop: 20 }}
          onClick={handleLogin}
        >
          登录
        </Button>
      </Card>
    </div>
  );
}
