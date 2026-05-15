import React from "react";
import ComplaintListPage from "./ComplaintListPage";

/**
 * Agent's own work queue — open and in-progress assignments.
 * Server-side, /complaints already filters by agent for Support Agents.
 */
export default function AgentQueuePage() {
  return (
    <ComplaintListPage
      title="My Work Queue"
      subtitle="Complaints assigned to you"
    />
  );
}
