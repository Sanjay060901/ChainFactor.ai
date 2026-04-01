import InvoiceDetailClient from "./client";

export function generateStaticParams() { return [{ id: 'placeholder' }]; }

export default function InvoiceDetailPage({ params }: { params: { id: string } }) {
  return <InvoiceDetailClient params={params} />;
}
