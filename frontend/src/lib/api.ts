/**
 * API client for ChainFactor AI backend.
 * All endpoints return stub data during skeleton phase.
 * Base URL switches between local dev and production via env var.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth
  register: (body: {
    phone: string;
    email: string;
    password: string;
    name: string;
    company_name: string;
    gstin: string;
  }) => request("/api/v1/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { phone_or_email: string; password: string }) =>
    request<{
      access_token: string;
      refresh_token: string;
      user: { id: string; name: string; email: string; phone: string };
    }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(body) }),

  verifyOtp: (body: { phone: string; otp_code: string }) =>
    request("/api/v1/auth/verify-otp", { method: "POST", body: JSON.stringify(body) }),

  // Wallet
  linkWallet: (body: { wallet_address: string; signed_message: string }) =>
    request("/api/v1/wallet/link", { method: "POST", body: JSON.stringify(body) }),

  walletStatus: () =>
    request<{ linked: boolean; wallet_address: string | null; algo_balance: number | null }>(
      "/api/v1/wallet/status"
    ),

  unlinkWallet: () =>
    request("/api/v1/wallet/link", { method: "DELETE" }),

  // Invoices
  uploadInvoice: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{
      invoice_id: string;
      status: string;
      ws_url: string;
      created_at: string;
    }>("/api/v1/invoices/upload", {
      method: "POST",
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  },

  listInvoices: (params?: {
    page?: number;
    limit?: number;
    status?: string;
    sort?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.status) query.set("status", params.status);
    if (params?.sort) query.set("sort", params.sort);
    if (params?.search) query.set("search", params.search);
    return request<{
      invoices: Array<{
        id: string;
        invoice_number: string;
        seller_name: string;
        amount: number;
        risk_score: number | null;
        status: string;
        created_at: string;
      }>;
      total: number;
      page: number;
      limit: number;
      pages: number;
    }>(`/api/v1/invoices?${query}`);
  },

  getInvoice: (invoiceId: string) =>
    request<Record<string, unknown>>(`/api/v1/invoices/${invoiceId}`),

  getAuditTrail: (invoiceId: string) =>
    request<Record<string, unknown>>(`/api/v1/invoices/${invoiceId}/audit-trail`),

  nftOptIn: (invoiceId: string, body: { wallet_address: string; signed_txn: string }) =>
    request(`/api/v1/invoices/${invoiceId}/nft/opt-in`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  nftClaim: (invoiceId: string, body: { wallet_address: string }) =>
    request<{
      txn_id: string;
      asset_id: number;
      status: string;
      explorer_url: string;
    }>(`/api/v1/invoices/${invoiceId}/nft/claim`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Dashboard
  dashboardSummary: () =>
    request<{
      total_value: number;
      active_invoices: number;
      pending_invoices: number;
      avg_risk_score: number;
      approval_rate: number;
      risk_distribution: { low: number; medium: number; high: number };
      monthly_volume: Array<{ month: string; count: number; value: number }>;
    }>("/api/v1/dashboard/summary"),

  nlQuery: (query: string) =>
    request<{ answer: string; data: unknown[] | null }>("/api/v1/dashboard/nl-query", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  // Rules
  listRules: () =>
    request<{
      rules: Array<{
        id: string;
        conditions: Array<{ field: string; operator: string; value: number | string }>;
        action: string;
        is_active: boolean;
        created_at: string;
      }>;
      default_action: string;
    }>("/api/v1/rules"),

  createRule: (body: {
    conditions: Array<{ field: string; operator: string; value: number | string }>;
    action: string;
  }) => request("/api/v1/rules", { method: "POST", body: JSON.stringify(body) }),

  updateRule: (
    ruleId: string,
    body: {
      conditions?: Array<{ field: string; operator: string; value: number | string }>;
      action?: string;
      is_active?: boolean;
    }
  ) =>
    request(`/api/v1/rules/${ruleId}`, { method: "PUT", body: JSON.stringify(body) }),

  deleteRule: (ruleId: string) =>
    request(`/api/v1/rules/${ruleId}`, { method: "DELETE" }),

  setDefaultAction: (defaultAction: string) =>
    request("/api/v1/rules/default-action", {
      method: "PUT",
      body: JSON.stringify({ default_action: defaultAction }),
    }),
};

/**
 * SSE client for real-time invoice processing events.
 * Usage:
 *   const close = subscribeToProcessing("inv_001", (event) => { ... });
 *   // later: close();
 */
export function subscribeToProcessing(
  invoiceId: string,
  onEvent: (event: Record<string, unknown>) => void,
  onError?: (error: Event) => void
): () => void {
  const source = new EventSource(
    `${API_BASE}/api/v1/invoices/${invoiceId}/stream`
  );

  source.onmessage = (e) => {
    const data = JSON.parse(e.data);
    onEvent(data);
  };

  source.onerror = (e) => {
    if (onError) onError(e);
    source.close();
  };

  return () => source.close();
}
