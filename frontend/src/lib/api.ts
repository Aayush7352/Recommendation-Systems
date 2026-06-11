import type {
  CompareResponse,
  Domain,
  DomainInfo,
  EvalResponse,
  Item,
  RecResponse,
  ServiceInfo,
  UserSummary,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ApiResult<T> {
  data: T | null;
  error: string | null;
}

async function get<T>(
  path: string,
  init?: RequestInit & { revalidate?: number },
): Promise<ApiResult<T>> {
  const url = `${BASE_URL}${path}`;
  try {
    const res = await fetch(url, {
      ...init,
      cache: init?.cache ?? "no-store",
      next: init?.revalidate != null ? { revalidate: init.revalidate } : undefined,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      return { data: null, error: `${res.status} ${res.statusText}${text ? ` — ${text.slice(0, 200)}` : ""}` };
    }
    const data = (await res.json()) as T;
    return { data, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    return { data: null, error: message };
  }
}

export const api = {
  baseUrl: BASE_URL,

  getService: () => get<ServiceInfo>("/"),

  getDomainInfo: (domain: Domain) => get<DomainInfo>(`/domains/${domain}/info`),

  getUsers: (domain: Domain, limit = 50) =>
    get<UserSummary[]>(`/domains/${domain}/users?limit=${limit}`),

  getUserHistory: (domain: Domain, userId: string | number, limit = 50) =>
    get<Item[]>(
      `/domains/${domain}/users/${encodeURIComponent(String(userId))}/history?limit=${limit}`,
    ),

  getItems: (domain: Domain, limit = 50) =>
    get<Item[]>(`/domains/${domain}/items?limit=${limit}`),

  recommend: (
    domain: Domain,
    algo: string,
    userId: string | number,
    k = 10,
  ) =>
    get<RecResponse>(
      `/recommend/${domain}/${algo}/${encodeURIComponent(String(userId))}?k=${k}`,
    ),

  compare: (
    domain: Domain,
    userId: string | number,
    algos: string[],
    k = 10,
  ) =>
    get<CompareResponse>(
      `/recommend/${domain}/compare/${encodeURIComponent(String(userId))}?algos=${algos.join(",")}&k=${k}`,
    ),

  evaluate: (domain: Domain, k = 10, refresh = false) =>
    get<EvalResponse>(`/evaluate/${domain}?k=${k}&refresh=${refresh}`),
};
