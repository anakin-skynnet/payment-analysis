import { createFileRoute, Navigate } from "@tanstack/react-router";

/** Redirect to consolidated Data Quality page. */
export const Route = createFileRoute("/_sidebar/incidents")({
  component: () => <Navigate to="/data-quality" replace />,
});
