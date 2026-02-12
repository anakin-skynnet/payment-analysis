import { createFileRoute, Navigate } from "@tanstack/react-router";

/** Redirect to consolidated Data Quality page. */
export const Route = createFileRoute("/_sidebar/alerts-data-quality")({
  component: () => <Navigate to="/data-quality" replace />,
});
