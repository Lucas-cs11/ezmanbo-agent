import { create } from "zustand";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_guest?: boolean;
  dual_model_enabled?: boolean;
}

export const GUEST_MESSAGE_LIMIT = 5;

interface AuthStore {
  token: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  guestMessageCount: number;
  login: (token: string, user: AuthUser, refreshToken?: string | null) => void;
  logout: () => void;
  setUser: (user: AuthUser) => void;
  isAuthenticated: () => boolean;
  getAuthHeaders: () => Record<string, string>;
  /** 进入应用时调用：访问令牌还有效就沿用，过期则用刷新令牌静默换新，实在不行才登出。 */
  ensureFresh: () => Promise<boolean>;
  incrementGuestCount: () => void;
  canSendAsGuest: () => boolean;
  remainingGuestMessages: () => number;
}

function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("ezmanbo_token");
}

function loadRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("ezmanbo_refresh_token");
}

function loadUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("ezmanbo_user");
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function loadGuestCount(): number {
  if (typeof window === "undefined") return 0;
  const raw = localStorage.getItem("ezmanbo_guest_count");
  return raw ? parseInt(raw, 10) : 0;
}

// 并发去重：挂载与窗口聚焦可能同时触发 ensureFresh，不能各换一次令牌
// （刷新令牌是滑动续期的，并发换新可能互相作废）
let _refreshing: Promise<boolean> | null = null;

export const useAuthStore = create<AuthStore>()((set, get) => ({
  token: loadToken(),
  refreshToken: loadRefreshToken(),
  user: loadUser(),
  guestMessageCount: loadGuestCount(),

  login: (token, user, refreshToken) => {
    localStorage.setItem("ezmanbo_token", token);
    localStorage.setItem("ezmanbo_user", JSON.stringify(user));
    // 游客不签发刷新令牌，此时要把上一个账号残留的刷新令牌清掉
    if (refreshToken) localStorage.setItem("ezmanbo_refresh_token", refreshToken);
    else localStorage.removeItem("ezmanbo_refresh_token");
    if (!user.is_guest) localStorage.removeItem("ezmanbo_guest_count");
    set({ token, refreshToken: refreshToken || null, user, guestMessageCount: 0 });
  },

  setUser: (user) => {
    localStorage.setItem("ezmanbo_user", JSON.stringify(user));
    set({ user });
  },

  logout: () => {
    localStorage.removeItem("ezmanbo_token");
    localStorage.removeItem("ezmanbo_refresh_token");
    localStorage.removeItem("ezmanbo_user");
    localStorage.removeItem("ezmanbo_guest_count");
    set({ token: null, refreshToken: null, user: null, guestMessageCount: 0 });
  },

  ensureFresh: async () => {
    if (_refreshing) return _refreshing;
    _refreshing = (async () => {
      const { token, refreshToken } = get();

      // 先用现有访问令牌探活。只有明确 401 才认为失效——网络不通或服务端 5xx
      // 都不该把用户踢下线，否则一次抖动就要重新登录。
      if (token) {
        try {
          const r = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
          if (r.ok) {
            const fresh = await r.json();
            get().setUser(fresh);
            return true;
          }
          if (r.status !== 401) return true;
        } catch {
          return true;
        }
      }

      // 游客无刷新令牌，过期即回到登录页一键重进
      if (!refreshToken) {
        get().logout();
        return false;
      }

      try {
        const r = await fetch("/auth/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!r.ok) {
          get().logout();
          return false;
        }
        const d = await r.json();
        localStorage.setItem("ezmanbo_token", d.token);
        localStorage.setItem("ezmanbo_refresh_token", d.refresh_token);
        set({ token: d.token, refreshToken: d.refresh_token });
        return true;
      } catch {
        // 服务端暂时不可达：保留会话，等下次聚焦再试
        return true;
      }
    })().finally(() => { _refreshing = null; });
    return _refreshing;
  },

  isAuthenticated: () => !!get().token,

  getAuthHeaders: (): Record<string, string> => {
    const token = get().token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  incrementGuestCount: () => {
    const next = get().guestMessageCount + 1;
    localStorage.setItem("ezmanbo_guest_count", String(next));
    set({ guestMessageCount: next });
  },

  canSendAsGuest: () => {
    const { user, guestMessageCount } = get();
    if (!user?.is_guest) return true;
    return guestMessageCount < GUEST_MESSAGE_LIMIT;
  },

  remainingGuestMessages: () => {
    const { user, guestMessageCount } = get();
    if (!user?.is_guest) return Infinity;
    return Math.max(0, GUEST_MESSAGE_LIMIT - guestMessageCount);
  },
}));
