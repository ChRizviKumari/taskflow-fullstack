import {
  createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode,
} from "react";
import { createApiClient, type ApiClient } from "../api/client";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  api: ApiClient;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
}

const TOKEN_KEY = "taskflow.token";
const USER_KEY = "taskflow.user";

const AuthContext = createContext<AuthState | null>(null);

function readStored(): { token: string | null; user: User | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const raw = localStorage.getItem(USER_KEY);
    return { token, user: raw ? (JSON.parse(raw) as User) : null };
  } catch {
    return { token: null, user: null };
  }
}

export function AuthProvider({ children, apiOverride }: { children: ReactNode; apiOverride?: ApiClient }) {
  const initial = useMemo(readStored, []);
  const tokenRef = useRef<string | null>(initial.token);
  const [user, setUser] = useState<User | null>(initial.token ? initial.user : null);

  const clear = useCallback(() => {
    tokenRef.current = null;
    setUser(null);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch { /* storage unavailable */ }
  }, []);

  const api = useMemo(
    () => apiOverride ?? createApiClient({ getToken: () => tokenRef.current, onUnauthorized: clear }),
    [apiOverride, clear],
  );

  const accept = useCallback((token: string, u: User) => {
    tokenRef.current = token;
    setUser(u);
    try {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(u));
    } catch { /* storage unavailable */ }
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      api,
      login: async (email, password) => {
        const r = await api.login(email, password);
        accept(r.token, r.user);
      },
      register: async (email, name, password) => {
        const r = await api.register(email, name, password);
        accept(r.token, r.user);
      },
      logout: clear,
    }),
    [user, api, accept, clear],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
