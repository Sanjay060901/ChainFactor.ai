import AuditTrailClient from "./client";

export function generateStaticParams() { return [{ id: 'placeholder' }]; }

export default function AuditTrailPage({ params }: { params: { id: string } }) {
  return <AuditTrailClient params={params} />;
}
