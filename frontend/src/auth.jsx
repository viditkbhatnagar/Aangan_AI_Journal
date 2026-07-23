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

  // MFA: login can return a challenge instead of a session. The pending
  // challenge token lives only in this closure — never storage.
  const [mfaToken, setMfaToken] = useState(null);

  const login = useCallback(async (email, password) => {
    const result = await api.post('/auth/login', { email, password });
    if (result.mfa_required) {
      setMfaToken(result.mfa_token);
      return { mfaRequired: true };
    }
    await finishLogin(result.access_token);
    return { mfaRequired: false };
  }, [finishLogin]);

  const verifyMfa = useCallback(async (code) => {
    const { access_token } = await api.post('/auth/mfa/verify', { mfa_token: mfaToken, code });
    setMfaToken(null);
    await finishLogin(access_token);
  }, [mfaToken, finishLogin]);

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
    () => ({ user, members, login, verifyMfa, register, logout, refreshMembers }),
    [user, members, login, verifyMfa, register, logout, refreshMembers],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
