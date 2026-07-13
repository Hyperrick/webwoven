import { DemoApi } from "./demo-api";
import { HttpApi } from "./http-api";
import type { WebwovenApi } from "./types";

export function createRuntimeApi(): WebwovenApi {
  if (import.meta.env.VITE_API_MODE === "demo") return new DemoApi();
  return new HttpApi();
}
