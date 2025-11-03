/**
 * API client for backend integration
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail?: string,
  ) {
    super(detail || statusText);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = typeof globalThis.window !== "undefined" ? globalThis.window.localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    // Handle unauthorized/invalid token (401)
    if (response.status === 401) {
      // Clear invalid token
      if (typeof globalThis.window !== "undefined") {
        globalThis.window.localStorage.removeItem("token");
        // Redirect to login page
        globalThis.window.location.href = "/login";
      }
      throw new ApiError(
        response.status,
        response.statusText,
        "Your session has expired. Please log in again."
      );
    }

    let errorData: any;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && errorData.detail) {
      // Format validation errors
      if (Array.isArray(errorData.detail)) {
        const errors = errorData.detail.map((err: any) => {
          const field = err.loc ? err.loc.slice(-1)[0] : 'field';
          return `${field}: ${err.msg}`;
        }).join(', ');
        throw new ApiError(response.status, response.statusText, errors);
      }
    }
    
    throw new ApiError(
      response.status,
      response.statusText,
      errorData.detail || errorData.message || response.statusText
    );
  }

  return response.json();
}

// Auth API
export const authApi = {
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, response.statusText, error.detail);
    }

    const data = await response.json();
    if (typeof globalThis.window !== "undefined") {
      globalThis.window.localStorage.setItem("token", data.access_token);
    }
    return data;
  },

  async signup(username: string, email: string, password: string) {
    return request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
  },

  async getMe() {
    return request("/auth/me");
  },

  logout() {
    if (typeof globalThis.window !== "undefined") {
      globalThis.window.localStorage.removeItem("token");
    }
  },
};

// Upload API
export const uploadApi = {
  async uploadClaimsFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const token = typeof globalThis.window !== "undefined" ? globalThis.window.localStorage.getItem("token") : null;

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/upload/claims`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      // Handle unauthorized/invalid token (401)
      if (response.status === 401) {
        // Clear invalid token
        if (typeof globalThis.window !== "undefined") {
          globalThis.window.localStorage.removeItem("token");
          // Redirect to login page
          globalThis.window.location.href = "/login";
        }
        throw new ApiError(
          response.status,
          response.statusText,
          "Your session has expired. Please log in again."
        );
      }

      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, response.statusText, error.detail);
    }

    return response.json();
  },
};

// Analytics API
export const analyticsApi = {
  async getMetrics(batchId?: string, startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (batchId) params.append("batch_id", batchId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    return request(`/analytics/metrics?${params.toString()}`);
  },

  async getErrorBreakdown(batchId?: string) {
    const params = new URLSearchParams();
    if (batchId) params.append("batch_id", batchId);
    const queryString = params.toString();
    return request(`/analytics/charts/error-breakdown${queryString ? `?${queryString}` : ""}`);
  },

  async getAmountBreakdown(batchId?: string) {
    const params = new URLSearchParams();
    if (batchId) params.append("batch_id", batchId);
    const queryString = params.toString();
    return request(`/analytics/charts/amount-breakdown${queryString ? `?${queryString}` : ""}`);
  },

  async getBatches() {
    return request("/analytics/batches");
  },
};

// Claims API
export const claimsApi = {
  async listClaims(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    error_type?: string;
    batch_id?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append("skip", params.skip.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.status) searchParams.append("status", params.status);
    if (params?.error_type) searchParams.append("error_type", params.error_type);
    if (params?.batch_id) searchParams.append("batch_id", params.batch_id);
    if (params?.search) searchParams.append("search", params.search);

    return request(`/claims?${searchParams.toString()}`);
  },

  async getClaim(claimId: string) {
    return request(`/claims/${claimId}`);
  },
};

// Rules API
export const rulesApi = {
  async getRules(ruleType?: "technical" | "medical") {
    const params = new URLSearchParams();
    if (ruleType) params.append("rule_type", ruleType);
    const queryString = params.toString();
    return request(`/rules${queryString ? `?${queryString}` : ""}`);
  },

  async updateRules(ruleType: "technical" | "medical", rules: any) {
    return request(`/rules/${ruleType}`, {
      method: "PUT",
      body: JSON.stringify(rules),
    });
  },

  async uploadRulesFile(ruleType: "technical" | "medical", file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const token = typeof globalThis.window !== "undefined" ? globalThis.window.localStorage.getItem("token") : null;

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/rules/${ruleType}/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof globalThis.window !== "undefined") {
          globalThis.window.localStorage.removeItem("token");
          globalThis.window.location.href = "/login";
        }
        throw new ApiError(
          response.status,
          response.statusText,
          "Your session has expired. Please log in again."
        );
      }

      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, response.statusText, error.detail);
    }

    return response.json();
  },

  async reloadRules(ruleType: "technical" | "medical") {
    return request(`/rules/${ruleType}/reload`, {
      method: "POST",
    });
  },

  async validateRules(ruleType: "technical" | "medical") {
    return request(`/rules/${ruleType}/validate`);
  },
};

// Tenants API
export const tenantsApi = {
  async createTenant(tenantId: string, copyFromDefault: boolean = true) {
    return request("/tenants/create", {
      method: "POST",
      body: JSON.stringify({ tenant_id: tenantId, copy_from_default: copyFromDefault }),
    });
  },

  async switchTenant(tenantId: string) {
    return request(`/tenants/switch?tenant_id=${tenantId}`, {
      method: "POST",
    });
  },

  async getCurrentTenant() {
    return request("/tenants/current");
  },

  async listTenants() {
    return request("/tenants/list");
  },
};

export { ApiError };

