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

/** 拍下登录会改动的四个键，供写失败时回滚。 */
function snapshotAuthKeys(): Record<string, string | null> {
  return {
    ezmanbo_token: localStorage.getItem("ezmanbo_token"),
    ezmanbo_user: localStorage.getItem("ezmanbo_user"),
    ezmanbo_refresh_token: localStorage.getItem("ezmanbo_refresh_token"),
    ezmanbo_guest_count: localStorage.getItem("ezmanbo_guest_count"),
  };
}

/** 把存储恢复到快照；值为 null 表示该键原本就不存在。 */
function restoreAuthKeys(snap: Record<string, string | null>): void {
  for (const [k, v] of Object.entries(snap)) {
    if (v === null) localStorage.removeItem(k);
    else localStorage.setItem(k, v);
  }
}

// 并发去重：挂载、路由变化与窗口聚焦可能同时触发 ensureFresh，去重后只发一次请求，
// 避免多个响应各自写一次令牌、互相覆盖。
let _refreshing: Promise<boolean> | null = null;

// 会话代次：login() / logout() 都会让它 +1。ensureFresh 在每个 await 之后都比对这个值，
// 防止「用户已经登出或已换账号，但迟到的刷新响应又把旧令牌写回去」——
// 那会让退出登录失效，甚至把上一个账号的令牌塞给刚登录的新账号。
let _sessionGen = 0;

export const useAuthStore = create<AuthStore>()((set, get) => ({
  token: loadToken(),
  refreshToken: loadRefreshToken(),
  user: loadUser(),
  guestMessageCount: loadGuestCount(),

  login: (token, user, refreshToken) => {
    // 先落盘、全部成功后再改内存，让登录成为一个原子操作：要么全部生效，要么原样不动。
    // 半截状态会让 localStorage 里出现「新令牌 + 旧身份」这种自相矛盾的组合，
    // 刷新页面后就变成拿着一个账号的令牌、显示另一个账号的身份。
    const snap = snapshotAuthKeys();
    // 配额耗尽时是所有 setItem 抛错、removeItem 却正常，所以「到底写入过没有」必须单独记：
    // 否则连第一次写入就被拒这种最常见的故障都会走进回滚，把一个完好的会话清掉。
    let touched = false;
    try {
      localStorage.setItem("ezmanbo_token", token);
      touched = true;
      localStorage.setItem("ezmanbo_user", JSON.stringify(user));
      // 游客不签发刷新令牌，此时要把上一个账号残留的刷新令牌清掉
      if (refreshToken) localStorage.setItem("ezmanbo_refresh_token", refreshToken);
      else localStorage.removeItem("ezmanbo_refresh_token");
      // 计数归零必须同时落到 localStorage：只改内存的话，刷新页面会把上一个访客的
      // 用量读回来，于是「刚进来能用」和「刷新后被拒」自相矛盾。
      localStorage.removeItem("ezmanbo_guest_count");
    } catch (e) {
      // 首次写入就被拒 = 存储分毫未动，没有可撤销的东西；此时清空反而会销毁一个完好的会话。
      if (!touched) throw e;
      try {
        // 还原到调用前，而不是一律删干净：一次失败的登录不该降级已有会话。
        restoreAuthKeys(snap);
      } catch {
        // 还原中途失败会留下「新令牌 + 旧身份」，所以 fail-closed 全清——终态只留
        // 「完整还原」或「完整清空」两种。先删 token：兜底自身若也被拒，token 已删则
        // 重载只会干净登出，不会身份错配。
        try {
          localStorage.removeItem("ezmanbo_token");
          for (const k of Object.keys(snap)) localStorage.removeItem(k);
        } catch { /* 存储彻底不可用，没有可回滚的东西 */ }
      }
      throw e;
    }
    _sessionGen += 1;
    set({ token, refreshToken: refreshToken || null, user, guestMessageCount: 0 });
  },

  setUser: (user) => {
    localStorage.setItem("ezmanbo_user", JSON.stringify(user));
    set({ user });
  },

  logout: () => {
    _sessionGen += 1;
    localStorage.removeItem("ezmanbo_token");
    localStorage.removeItem("ezmanbo_refresh_token");
    localStorage.removeItem("ezmanbo_user");
    localStorage.removeItem("ezmanbo_guest_count");
    set({ token: null, refreshToken: null, user: null, guestMessageCount: 0 });
  },

  ensureFresh: async () => {
    if (_refreshing) return _refreshing;
    _refreshing = (async () => {
      const gen = _sessionGen;
      const { token, refreshToken } = get();

      // 本次结果是否已过期：期间用户登出或换了账号，就不能再拿旧结果写回存储。
      // 返回「当前真实登录态」而不是 true——登出后应让调用方跳登录页。
      const stale = () => _sessionGen !== gen;
      const current = () => !!get().token;

      // 先用现有访问令牌探活。只有明确 401 才认为失效——网络不通或服务端 5xx
      // 都不该把用户踢下线，否则一次抖动就要重新登录。
      if (token) {
        try {
          const r = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
          if (stale()) return current();
          if (r.ok) {
            const fresh = await r.json();
            if (stale()) return current();
            get().setUser(fresh);
            return true;
          }
          if (r.status !== 401) return true;
        } catch {
          return stale() ? current() : true;
        }
      }

      if (stale()) return current();

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
        if (stale()) return current();
        if (!r.ok) {
          // 只有服务端明确拒绝这个刷新令牌（400/401/403）才判定掉线；
          // 5xx 是服务端自己的问题，不能因此把用户踢下线——那正是静默续期要避免的事。
          if (r.status === 400 || r.status === 401 || r.status === 403) {
            get().logout();
            return false;
          }
          return true;
        }
        const d = await r.json();
        if (stale()) return current();
        // 200 但响应体不完整（异常代理、半截响应）：既不要写入 undefined，
        // 也不要据此销毁会话——保留现状，交给下一次 401 去判定。
        if (!d?.token || !d?.refresh_token) return true;
        localStorage.setItem("ezmanbo_token", d.token);
        localStorage.setItem("ezmanbo_refresh_token", d.refresh_token);
        set({ token: d.token, refreshToken: d.refresh_token });
        return true;
      } catch {
        // 服务端暂时不可达：保留会话，等下次聚焦再试
        return stale() ? current() : true;
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
