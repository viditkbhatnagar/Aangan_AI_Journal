import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, clearToken, setToken, setUnauthorizedHandler } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [members, setMembers] = useState([]);

  const refreshMembers = useCallback(async () => {
    try { setMembers(await api.get('/circles/members')); }
    catch { setMembers([]); }
  }, []);

  const finishLogin = useCallback(async (accessToken) => {
    setToken(accessToken);
    const me = await api.get('/me');
    setUser(me);
    await refreshMembers();
  }, [refreshMembers]);

  const login = useCallback(async (email, password) => {
    const { access_token } = await api.post('/auth/login', { email, password });
    await finishLogin(access_token);
  }, [finishLogin]);

  const register = useCallback(async (payload) => {
    const { access_token } = await api.post('/auth/register', payload);
    await finishLogin(access_token);
  }, [finishLogin]);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setMembers([]);
  }, []);

  useEffect(() => { setUnauthorizedHandler(() => { setUser(null); setMembers([]); }); }, []);

  const value = useMemo(
    () => ({ user, members, login, register, logout, refreshMembers }),
    [user, members, login, register, logout, refreshMembers],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
