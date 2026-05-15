import React from "react";
import ComplaintListPage from "./ComplaintListPage";

export default function EscalationsPage() {
  return (
    <ComplaintListPage
      title="Escalations"
      subtitle="Complaints flagged for supervisor attention"
      defaultFilters={{ escalated: true }}
    />
  );
}
