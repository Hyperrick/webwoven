import type { SessionSnapshot } from "./types";

export class StaleSessionError extends Error {
  readonly snapshot: SessionSnapshot;

  constructor(message: string, snapshot: SessionSnapshot) {
    super(message);
    this.name = "StaleSessionError";
    this.snapshot = snapshot;
  }
}
