import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchMe, login as apiLogin, register as apiRegister, type User } from "../api/client";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("ssg_token");
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("ssg_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthCtx>(
    () => ({
      user,
      loading,
      async login(email, password) {
        const res = await apiLogin(email, password);
        localStorage.setItem("ssg_token", res.access_token);
        setUser(res.user);
      },
      async register(email, password, fullName) {
        const res = await apiRegister(email, password, fullName);
        localStorage.setItem("ssg_token", res.access_token);
        setUser(res.user);
      },
      logout() {
        localStorage.removeItem("ssg_token");
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}
