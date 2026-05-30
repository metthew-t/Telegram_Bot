const STORAGE_KEY = 'telegram_counselling_auth';

function getStoredAuth() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch (error) {
    return null;
  }
}

export function saveAuth(auth) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
}

export function clearAuth() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getAccessToken() {
  const auth = getStoredAuth();
  return auth?.access || null;
}

export function getUser() {
  const auth = getStoredAuth();
  return auth?.user || null;
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}

export function logoutUser() {
  clearAuth();
  window.dispatchEvent(new Event('storage'));
}
