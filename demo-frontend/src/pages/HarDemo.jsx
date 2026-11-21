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
      <Alert
        data-testid="har-demo-error"
        description={error}
        message="HAR demo failed to load"
        type="error"
      />
    );
  }

  if (!data) {
    return <Spin data-testid="har-demo-loading" tip="Loading HAR demo data" />;
  }

  return (
    <Card data-testid="har-demo-success" title="HAR Record and Replay Demo">
      <p data-testid="har-demo-profile">{data.profile.displayName}</p>
      <p data-testid="har-demo-permission">{data.permissions.primaryPermission}</p>
      <p data-testid="har-demo-metrics">{data.metrics.activeProjects}</p>
    </Card>
  );
}
