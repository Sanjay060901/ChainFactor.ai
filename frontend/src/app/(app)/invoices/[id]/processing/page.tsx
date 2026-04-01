import ProcessingClient from "./client";

export function generateStaticParams() { return [{ id: 'placeholder' }]; }

export default function ProcessingPage({ params }: { params: { id: string } }) {
  return <ProcessingClient params={params} />;
}
