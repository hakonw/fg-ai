import App from "./App.svelte";

const app = new App({
  target: document.body,
  props: {
    server: "http://127.0.0.1:8080",
  },
});

export default app;
