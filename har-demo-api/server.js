import express from "express";

const app = express();
const PORT = 3001;

app.get("/health", (_request, response) => {
  response.json({ status: "ok" });
});

app.get("/api/har-demo/profile", (_request, response) => {
  response.json({ displayName: "Ada Lovelace" });
});

app.get("/api/har-demo/permissions", (_request, response) => {
  response.json({ primaryPermission: "reports:read" });
});

app.get("/api/har-demo/metrics", (_request, response) => {
  response.json({ activeProjects: 12 });
});

app.listen(PORT, () => {
  console.log(`HAR demo API listening on port ${PORT}`);
});
