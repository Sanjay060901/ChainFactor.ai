import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-5xl font-bold text-primary-700">ChainFactor AI</h1>
      <p className="mt-4 text-lg text-gray-600">
        AI-powered invoice financing for Indian SMEs on Algorand
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          href="/auth/login"
          className="rounded-lg bg-primary-600 px-6 py-3 text-sm font-medium text-white hover:bg-primary-700"
        >
          Sign In
        </Link>
        <Link
          href="/auth/register"
          className="rounded-lg border border-primary-600 px-6 py-3 text-sm font-medium text-primary-600 hover:bg-primary-50"
        >
          Register
        </Link>
      </div>
    </main>
  );
}
