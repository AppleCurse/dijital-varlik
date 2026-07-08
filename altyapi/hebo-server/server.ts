/**
 * Dijital Varlık — Hebo Gateway Server
 * Hono + Hebo Gateway, LiteLLM'e proxy olarak ek routing katmanı.
 * Port: 4001
 */
import { Hono } from "hono";
import { gateway, defineModelCatalog } from "@hebo-ai/gateway";

// LiteLLM proxy model tanımları
const gw = gateway({
  basePath: "/v1/gateway",
  models: {
    "deepseek-v4-pro": {
      name: "DeepSeek V4 Pro",
      providers: ["litellm"],
      capabilities: ["tool_call", "reasoning", "temperature"],
    },
    "deepseek-v4-flash": {
      name: "DeepSeek V4 Flash",
      providers: ["litellm"],
      capabilities: ["tool_call", "temperature"],
    },
    "9router": {
      name: "9Router (OmniRoute)",
      providers: ["litellm"],
      capabilities: ["tool_call", "temperature"],
    },
  },
  logger: { level: "debug" },
});

const app = new Hono();

// Hebo Gateway handler'ı mount et
app.mount("/v1/gateway/", gw.handler);

// Health endpoint
app.get("/health", (c) => c.json({ status: "ok", gateway: "hebo" }));

// LiteLLM'e proxy geçiş (şimdilik direkt LiteLLM kullanılıyor,
// Hebo özel routing/MCP ihtiyaçlarında devreye girer)

console.log("🐒 Hebo Gateway starting on :4001");
console.log("   Models: deepseek-v4-pro, deepseek-v4-flash, 9router");

export default {
  port: 4001,
  fetch: app.fetch,
};
