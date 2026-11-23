/**
 * Shared type primitives used across feature modules.
 */

/** Processing run status shared across pipeline features. */
export type ProcessingStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

/** Stage identifier in the evidence pipeline. */
export type PhaseId = "acquisition" | "parsing" | "fact_chain" | "standardization" | "review";
