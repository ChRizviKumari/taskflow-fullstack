import type {
  ApiErrorBody, AuthResponse, Board, Column, Page, Task, TaskPatch, TaskQuery, User,
} from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isConflict(): boolean {
    return this.status === 409;
  }
}

export interface ClientOptions {
  baseUrl?: string;
  getToken: () => string | null;
  onUnauthorized?: () => void;
  fetchImpl?: typeof fetch;
}

type Params = Record<string, string | number | undefined>;

export function buildQuery(params: Params): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export function createApiClient(opts: ClientOptions) {
  const base = opts.baseUrl ?? "";
  const doFetch = opts.fetchImpl ?? ((...a: Parameters<typeof fetch>) => fetch(...a));

  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    signal?: AbortSignal,
  ): Promise<T> {
    const headers: Record<string, string> = {};
    const token = opts.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";

    let res: Response;
    try {
      res = await doFetch(`${base}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal,
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") throw err;
      throw new ApiError(0, "network_error", "Cannot reach the server");
    }

    if (res.status === 204) return undefined as T;
    const data: unknown = await res.json().catch(() => null);
    if (!res.ok) {
      const e = (data as { error?: ApiErrorBody } | null)?.error;
      if (res.status === 401 && token) opts.onUnauthorized?.();
      throw new ApiError(res.status, e?.code ?? "http_error", e?.message ?? res.statusText, e?.details);
    }
    return data as T;
  }

  return {
    register: (email: string, name: string, password: string) =>
      request<AuthResponse>("POST", "/api/auth/register", { email, name, password }),
    login: (email: string, password: string) =>
      request<AuthResponse>("POST", "/api/auth/login", { email, password }),
    me: () => request<{ user: User }>("GET", "/api/auth/me"),

    listBoards: (params: { q?: string; page?: number; page_size?: number } = {}, signal?: AbortSignal) =>
      request<Page<Board>>("GET", `/api/boards${buildQuery(params)}`, undefined, signal),
    createBoard: (name: string) => request<{ board: Board }>("POST", "/api/boards", { name }),
    getBoard: (id: number, signal?: AbortSignal) =>
      request<{ board: Board }>("GET", `/api/boards/${id}`, undefined, signal),
    deleteBoard: (id: number) => request<void>("DELETE", `/api/boards/${id}`),
    createColumn: (boardId: number, name: string) =>
      request<{ column: Column }>("POST", `/api/boards/${boardId}/columns`, { name }),

    listTasks: (boardId: number, query: TaskQuery = {}, signal?: AbortSignal) =>
      request<Page<Task>>("GET", `/api/boards/${boardId}/tasks${buildQuery({ ...query })}`, undefined, signal),
    createTask: (columnId: number, input: { title: string; description?: string; priority?: Task["priority"] }) =>
      request<{ task: Task }>("POST", `/api/columns/${columnId}/tasks`, input),
    updateTask: (id: number, patch: TaskPatch) =>
      request<{ task: Task }>("PATCH", `/api/tasks/${id}`, patch),
    deleteTask: (id: number) => request<void>("DELETE", `/api/tasks/${id}`),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
