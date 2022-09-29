import "./app.css";
import App from "./App.svelte";

const app = new App({
  target: document.getElementById("app"),
  props: {
    server: "https://fg-ai-backend-jk2rolxlbq-ew.a.run.app",
  },
});

export default app;
