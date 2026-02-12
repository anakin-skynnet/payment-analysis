/**
 * Command Center types (legacy re-exports).
 * All UI data is fetched from backend APIs; no synthetic mock generators are used.
 * Types used only by command-center are in command-center-types.ts.
 */

export type ReasonCodeCategory = "Antifraud" | "Technical" | "Issuer Decline";

export interface ReasonCodeSummary {
  category: ReasonCodeCategory;
  count: number;
  pct: number;
}

export type { EntrySystemPoint, FrictionFunnelStep, RetryRecurrenceRow } from "./command-center-types";
