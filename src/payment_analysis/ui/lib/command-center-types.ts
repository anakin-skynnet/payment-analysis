/**
 * Command Center UI types.
 * Chart/data shapes used by the Command Center view; API responses are mapped to these.
 * For API response types, see api.ts (e.g. CommandCenterEntryThroughputPointOut, ThreeDSFunnelOut).
 */

export interface EntrySystemPoint {
  ts: string;
  PD: number;
  WS: number;
  SEP: number;
  Checkout: number;
}

export interface FrictionFunnelStep {
  label: string;
  value: number;
  pct: number;
}

export interface RetryRecurrenceRow {
  type: "scheduled_recurrence" | "manual_retry";
  label: string;
  volume: number;
  pct: number;
}
