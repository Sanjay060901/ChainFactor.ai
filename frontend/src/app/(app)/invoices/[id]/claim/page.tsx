import ClaimNFTClient from "./client";

export function generateStaticParams() { return [{ id: 'placeholder' }]; }

export default function ClaimNFTPage({ params }: { params: { id: string } }) {
  return <ClaimNFTClient params={params} />;
}
