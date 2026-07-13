import { DemoApi } from "./demo-api";
import { ResilientApi } from "./resilient-api";
import type { WebwovenApi } from "./types";

export function createRuntimeApi(): WebwovenApi {
  const wantsLiveDevelopmentApi = import.meta.env.VITE_API_MODE === "live";
  if (import.meta.env.DEV && !wantsLiveDevelopmentApi) return new DemoApi();
  return new ResilientApi();
}
