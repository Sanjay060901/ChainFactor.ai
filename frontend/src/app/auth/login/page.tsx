"use client";

/**
 * Login page skeleton.
 * TODO: Wire to api.login(), handle JWT storage, redirect to /dashboard
 * See wireframes.md Screen 1 for layout reference.
 */

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-center text-2xl font-bold text-primary-700">
          ChainFactor AI
        </h1>
        <p className="mt-1 text-center text-sm text-gray-500">
          AI-powered invoice financing for SMEs
        </p>

        <div className="mt-8">
          <div className="flex border-b">
            <button className="flex-1 border-b-2 border-primary-600 pb-2 text-sm font-medium text-primary-600">
              Login
            </button>
            <a
              href="/auth/register"
              className="flex-1 pb-2 text-center text-sm font-medium text-gray-400 hover:text-gray-600"
            >
              Register
            </a>
          </div>

          <form className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Phone / Email
              </label>
              <input
                type="text"
                placeholder="+91 9876543210"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <button
              type="submit"
              className="w-full rounded-lg bg-primary-600 py-2.5 text-sm font-medium text-white hover:bg-primary-700"
            >
              Sign In
            </button>
          </form>

          <div className="mt-4 text-center">
            <span className="text-xs text-gray-400">or</span>
          </div>
          <button className="mt-2 w-full rounded-lg border border-gray-300 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
            OTP Login
          </button>
        </div>
      </div>
    </main>
  );
}
