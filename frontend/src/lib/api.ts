/**
 * API client for ChainFactor AI backend.
 * All endpoints return stub data during skeleton phase.
 * Base URL switches between local dev and production via env var.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const isFormData = options.body instanceof FormData;

  const headers: Record<string, string> = {
    // Don't set Content-Type for FormData — browser sets it with boundary
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers as Record<string, string>),
  };

  // Don't send auth header for login/register/verify (no token needed, stale token causes 401)
  const isAuthRoute = path.startsWith("/api/v1/auth/");
  if (token && !isAuthRoute) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch (err) {
    console.error(`[API] Network error for ${path}:`, err);
    throw new Error("Network error – please check your internet connection and try again.");
  }

  if (!res.ok) {
    // Handle 401 — clear stale token and redirect to login
    if (res.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // Only redirect if not already on the auth page
        if (!window.location.pathname.startsWith("/auth")) {
          window.location.href = "/auth/login";
        }
      }
      throw new Error("Session expired — please log in again.");
    }

    const error = await res.json().catch(() => null);
    const message =
      typeof error === "string"
        ? error
        : (error?.detail && String(error.detail)) || error?.message || `API error: ${res.status}`;
    throw new Error(message);
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

  deleteInvoice: (invoiceId: string) =>
    request<{ message: string }>(`/api/v1/invoices/${invoiceId}`, { method: "DELETE" }),

  processInvoice: (invoiceId: string) =>
    request<{ invoice_id: string; status: string; ws_url: string }>(
      `/api/v1/invoices/${invoiceId}/process`,
      { method: "POST" }
    ),

  getAuditTrail: (invoiceId: string) =>
    request<Record<string, unknown>>(`/api/v1/invoices/${invoiceId}/audit-trail`),

  nftOptIn: (invoiceId: string, body: { wallet_address: string; signed_txn: string }) =>
    request(`/api/v1/invoices/${invoiceId}/nft/opt-in`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  nftClaim: (invoiceId: string, body: { wallet_address: string }) =>
    request<{
      optin_txn_id: string;
      transfer_txn_id: string;
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

  // Account
  deleteAccount: () =>
    request<{ message: string }>("/api/v1/auth/account", { method: "DELETE" }),

  // AI Settings
  getAIConfig: () =>
    request<{
      bedrock_region: string;
      demo_mode: boolean;
      pipeline_timeout: number;
      max_retries: number;
      agents: Array<{
        name: string;
        model_id: string;
        description: string;
        temperature: number;
        max_tokens: number;
        top_p: number;
        timeout: number;
        max_iterations: number;
        stream_events: boolean;
      }>;
      swarm: {
        max_handoffs: number;
        max_iterations: number;
        execution_timeout: number;
        node_timeout: number;
        agents: string[];
      };
      event_types: string[];
    }>("/api/v1/settings/ai-config"),

  getAIPreferences: () =>
    request<{
      pipeline_timeout: number;
      auto_process: boolean;
      enable_ws_streaming: boolean;
      risk_threshold_low: number;
      risk_threshold_high: number;
      enable_nft_auto_mint: boolean;
    }>("/api/v1/settings/ai-preferences"),

  updateAIPreferences: (body: {
    pipeline_timeout?: number;
    auto_process?: boolean;
    enable_ws_streaming?: boolean;
    risk_threshold_low?: number;
    risk_threshold_high?: number;
    enable_nft_auto_mint?: boolean;
  }) =>
    request<{
      pipeline_timeout: number;
      auto_process: boolean;
      enable_ws_streaming: boolean;
      risk_threshold_low: number;
      risk_threshold_high: number;
      enable_nft_auto_mint: boolean;
    }>("/api/v1/settings/ai-preferences", {
      method: "PUT",
      body: JSON.stringify(body),
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
