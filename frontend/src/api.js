// Fetch wrapper. The JWT lives only in this module's closure (never
// localStorage/sessionStorage) — a page refresh means logging in again,
// which is the private-by-default trade we want.
let token = null;
let onUnauthorized = () => {};

export function setToken(t) { token = t; }
export function clearToken() { token = null; }
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed (${status})`);
    this.status = status;
  }
}

async function request(path, { method = 'GET', body, formData } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });

  if (res.status === 401) {
    clearToken();
    onUnauthorized();
    throw new ApiError(401, 'Please log in again.');
  }
  if (!res.ok) {
    let detail = null;
    try { detail = (await res.json()).detail; } catch { /* not json */ }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  postForm: (path, formData) => request(path, { method: 'POST', formData }),
};
