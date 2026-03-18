"use client";

/**
 * Register page skeleton.
 * TODO: Wire to api.register(), handle OTP verification, redirect to /auth/login
 * See wireframes.md Screen 1 for layout reference.
 */

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-center text-2xl font-bold text-primary-700">
          ChainFactor AI
        </h1>
        <p className="mt-1 text-center text-sm text-gray-500">
          Create your account
        </p>

        <div className="mt-8">
          <div className="flex border-b">
            <a
              href="/auth/login"
              className="flex-1 pb-2 text-center text-sm font-medium text-gray-400 hover:text-gray-600"
            >
              Login
            </a>
            <button className="flex-1 border-b-2 border-primary-600 pb-2 text-sm font-medium text-primary-600">
              Register
            </button>
          </div>

          <form className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input type="text" placeholder="Manoj RS" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Company Name</label>
              <input type="text" placeholder="Acme Technologies Pvt Ltd" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">GSTIN</label>
              <input type="text" placeholder="27AABCU9603R1ZM" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Phone</label>
              <input type="tel" placeholder="+91 9876543210" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input type="email" placeholder="manoj@acmetech.in" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input type="password" placeholder="••••••••" className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
            </div>
            <button type="submit" className="w-full rounded-lg bg-primary-600 py-2.5 text-sm font-medium text-white hover:bg-primary-700">
              Create Account
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
