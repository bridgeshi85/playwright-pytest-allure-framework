import { Alert, Card, Spin } from "antd";
import { useEffect, useState } from "react";

const API_ENDPOINTS = [
  "/api/har-demo/profile",
  "/api/har-demo/permissions",
  "/api/har-demo/metrics",
];

async function fetchDemoData() {
  const responses = await Promise.all(API_ENDPOINTS.map((endpoint) => fetch(endpoint)));

  if (responses.some((response) => !response.ok)) {
    throw new Error("Unable to load HAR demo data.");
  }

  return Promise.all(responses.map((response) => response.json()));
}

export default function HarDemo() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDemoData()
      .then(([profile, permissions, metrics]) => {
        setData({ profile, permissions, metrics });
      })
      .catch((requestError) => {
        setError(requestError.message);
      });
  }, []);

  if (error) {
    return (
      <div style={pageStyle}>
        <Alert
          data-testid="har-demo-error"
          description={error}
          message="HAR demo failed to load"
          type="error"
        />
      </div>
    );
  }

  if (!data) {
    return (
      <div style={pageStyle}>
        <Spin data-testid="har-demo-loading" tip="Loading HAR demo data" />
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <Card
        data-testid="har-demo-success"
        title="HAR Record and Replay Demo"
        style={{ width: 420 }}
      >
        <p data-testid="har-demo-profile">{data.profile.displayName}</p>
        <p data-testid="har-demo-permission">{data.permissions.primaryPermission}</p>
        <p data-testid="har-demo-metrics">{data.metrics.activeProjects}</p>
      </Card>
    </div>
  );
}

const pageStyle = {
  alignItems: "center",
  backgroundColor: "#f5f5f5",
  display: "flex",
  justifyContent: "center",
  height: "100vh",
  width: "100vw",
};
