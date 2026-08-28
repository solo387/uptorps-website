const STORAGE_KEYS = {
  user: 'uptorps_user',
  role: 'uptorps_role',
  remember: 'uptorps_remember',
  pendingEmail: 'uptorps_pending_email',
  accounts: 'uptorps_accounts',
};

const getAccounts = () => {
  try {
    const rawValue = localStorage.getItem(STORAGE_KEYS.accounts);
    if (!rawValue) return {};
    const parsed = JSON.parse(rawValue);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (error) {
    return {};
  }
};

const saveAccounts = (accounts) => {
  localStorage.setItem(STORAGE_KEYS.accounts, JSON.stringify(accounts));
};

const getAccountByEmail = (email) => {
  const normalizedEmail = normalizeEmail(email);
  const accounts = getAccounts();
  return accounts[normalizedEmail] || null;
};

const saveAccount = (email, accountData) => {
  const normalizedEmail = normalizeEmail(email);
  const accounts = getAccounts();
  accounts[normalizedEmail] = {
    email: normalizedEmail,
    ...accountData
  };
  saveAccounts(accounts);
  return accounts[normalizedEmail];
};

const isAdminRole = (role) => ['admin', 'administrator', 'teacher', 'premium_teacher'].includes(String(role || '').toLowerCase());

const setMessage = (message, type = 'info') => {
  const messageBox = document.getElementById('form-message');
  if (!messageBox) return;

  messageBox.className = type === 'error'
    ? 'error-message'
    : type === 'success'
      ? 'success-message'
      : type === 'warning'
        ? 'warning-message'
        : 'info-message';

  messageBox.textContent = message;
};

const normalizeEmail = (value) => (value || '').trim().toLowerCase();

const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

const getCurrentUser = () => localStorage.getItem(STORAGE_KEYS.user) || '';
const getCurrentRole = () => localStorage.getItem(STORAGE_KEYS.role) || 'student';
const isAdminRoute = () => window.location.pathname.includes('admin-');
const getRequestedPortal = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get('portal') === 'admin' ? 'admin' : 'student';
};

const clearAuthState = () => {
  localStorage.removeItem('uptorps_logged_in');
  localStorage.removeItem(STORAGE_KEYS.user);
  localStorage.removeItem(STORAGE_KEYS.role);
  localStorage.removeItem(STORAGE_KEYS.accounts);
  localStorage.removeItem('uptorps_access_token');
  localStorage.removeItem('uptorps_refresh_token');
};

const setAuthState = (payload) => {
  const userEmail = normalizeEmail(payload.email || payload.user?.email || getCurrentUser());
  const role = String(payload.role || 'student').toLowerCase();
  localStorage.setItem(STORAGE_KEYS.user, userEmail);
  localStorage.setItem(STORAGE_KEYS.role, role);
  localStorage.setItem('uptorps_logged_in', 'true');
  if (payload.access) {
    localStorage.setItem('uptorps_access_token', payload.access);
  }
  if (payload.refresh) {
    localStorage.setItem('uptorps_refresh_token', payload.refresh);
  }
};

const fetchJson = async (url, options = {}) => {
  const isLoginRequest = String(url).includes('/api/accounts/login/');
  const token = isLoginRequest ? null : localStorage.getItem('uptorps_access_token');
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

  if (token) {
    headers.Authorization = "Bearer " + token;
  }

  const response = await fetch(url, { ...options, headers });
  const payloadText = await response.text();
  let payload = null;

  if (payloadText) {
    try {
      payload = JSON.parse(payloadText);
    } catch (error) {
      payload = payloadText;
    }
  }

  if (!response.ok) {
    const message = payload && typeof payload === 'object'
      ? (payload.detail || payload.message || JSON.stringify(payload))
      : String(payload || 'Request failed');
    throw new Error(message);
  }

  return payload;
};

const ensureAuthState = () => {
  const isLoggedIn = localStorage.getItem('uptorps_logged_in') === 'true';
  const page = document.body.dataset.page;
  const currentRole = getCurrentRole();

  if (page === 'dashboard' || page === 'referral') {
    if (!isLoggedIn || currentRole !== 'student') {
      window.location.href = './login.html?portal=student';
      return;
    }
  }

  if (isAdminRoute()) {
    if (!isLoggedIn || currentRole !== 'admin') {
      window.location.href = './login.html?portal=admin';
    }
  }
};

const setCurrentUser = (email, role = 'student') => {
  const normalized = normalizeEmail(email);
  localStorage.setItem(STORAGE_KEYS.user, normalized || '');
  localStorage.setItem(STORAGE_KEYS.role, role === 'admin' ? 'admin' : 'student');
  localStorage.setItem('uptorps_logged_in', 'true');
};

const logoutUser = () => {
  clearAuthState();
  localStorage.removeItem(STORAGE_KEYS.remember);
  localStorage.removeItem(STORAGE_KEYS.accounts);
  window.location.href = './login.html';
};

const setupPasswordToggles = () => {
  document.querySelectorAll('.toggle-password').forEach((button) => {
    button.addEventListener('click', () => {
      const target = document.getElementById(button.dataset.target);
      if (!target) return;
      const isPassword = target.type === 'password';
      target.type = isPassword ? 'text' : 'password';
      button.textContent = isPassword ? '🙈' : '👁️';
      button.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
    });
  });
};

const setupYear = () => {
  const yearNode = document.getElementById('year');
  if (yearNode) {
    yearNode.textContent = new Date().getFullYear();
  }
};

const setupDashboardUser = () => {
  const page = document.body.dataset.page;
  if (page !== 'dashboard' && page !== 'referral') return;

  const email = getCurrentUser();
  const emailNode = document.getElementById('user-email');
  if (emailNode) {
    emailNode.textContent = email || 'Guest';
  }

  const greetingNode = document.getElementById('user-greeting');
  if (greetingNode) {
    const username = email ? email.split('@')[0] : 'Guest';
    greetingNode.textContent = `${username} 👋`;
  }
};

  const handleLogin = async (event) => {
    event.preventDefault();

    const form = event.currentTarget;
    if (form.dataset.submitting === 'true') {
      return;
    }

    clearAuthState();
    form.dataset.submitting = 'true';

    const email = normalizeEmail(form.email.value);
    const password = form.password.value;
    const selectedPortalField = form.querySelector('input[name="portal"]:checked');
    const selectedPortal = selectedPortalField ? selectedPortalField.value : getRequestedPortal();

    if (!isValidEmail(email)) {
      setMessage('Please enter a valid email address.', 'error');
      form.dataset.submitting = 'false';
      return;
    }

    if (!password || password.length < 6) {
      setMessage('Password must be at least 6 characters.', 'error');
      form.dataset.submitting = 'false';
      return;
    }

    try {
      const loginResponse = await fetchJson('/api/accounts/login/', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      const userMeta = loginResponse.user || {};
      const userUuid = userMeta.uuid || (userMeta.user && userMeta.user.uuid);

      if (!userUuid) {
        throw new Error('Login did not return a valid user ID.');
      }

      localStorage.setItem('uptorps_access_token', loginResponse.access);
      localStorage.setItem('uptorps_refresh_token', loginResponse.refresh);

      const profileResponse = await fetchJson(`/api/accounts/users/info/${userUuid}/`);
      const role = String(profileResponse.role || '').toUpperCase();

      if (selectedPortal === 'admin' && role !== 'ADMIN') {
        throw new Error('This account does not have admin access.');
      }

      if (selectedPortal === 'student' && role === 'ADMIN') {
        throw new Error('This is an admin account. Please choose Admin to continue.');
      }

      setAuthState({
        email: profileResponse.email || email,
        role: role === 'ADMIN' ? 'admin' : 'student',
        access: loginResponse.access,
        refresh: loginResponse.refresh
      });

      if (form.remember && form.remember.checked) {
        localStorage.setItem(STORAGE_KEYS.remember, 'true');
      } else {
        localStorage.removeItem(STORAGE_KEYS.remember);
      }

      window.location.href = selectedPortal === 'admin' ? './admin-dashboard.html' : './dashboard.html';
    } catch (error) {
      setMessage(error.message || 'Unable to sign in. Please check your details and try again.', 'error');
    } finally {
      form.dataset.submitting = 'false';
    }
  };

const handleSignup = (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  const email = normalizeEmail(form.email.value);
  const password = form.password.value;
  const confirmPassword = form.confirm_password.value;

  if (!isValidEmail(email)) {
    setMessage('Please enter a valid email address.', 'error');
    return;
  }

  if (password.length < 8) {
    setMessage('Password must be at least 8 characters.', 'error');
    return;
  }

  if (password !== confirmPassword) {
    setMessage('Passwords do not match.', 'error');
    return;
  }

  const existingAccount = getAccountByEmail(email);
  if (existingAccount && isAdminRole(existingAccount.role)) {
    setMessage('Admin accounts can only be created by an existing admin account. Students can create student accounts only.', 'error');
    return;
  }

  saveAccount(email, {
    password,
    role: 'student',
    createdBy: 'student-self-signup'
  });

  localStorage.setItem(STORAGE_KEYS.pendingEmail, email);
  setCurrentUser(email, 'student');
  window.location.href = './verification-sent.html';
};

const handleForgotPassword = (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  const email = normalizeEmail(form.email.value);

  if (!isValidEmail(email)) {
    setMessage('Please enter a valid email address.', 'error');
    return;
  }

  localStorage.setItem(STORAGE_KEYS.pendingEmail, email);
  const message = `If an account exists with ${email}, a password reset link has been sent. Please check your inbox.`;
  setMessage(message, 'success');
};

const handleResetPassword = (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  const password = form.password.value;
  const confirmPassword = form.confirm_password.value;

  if (password.length < 8) {
    setMessage('Password must be at least 8 characters.', 'error');
    return;
  }

  if (password !== confirmPassword) {
    setMessage('Passwords do not match.', 'error');
    return;
  }

  setMessage('Password updated successfully. You can now sign in.', 'success');
  setTimeout(() => {
    window.location.href = './login.html';
  }, 1200);
};

const setupVerificationMessage = () => {
  const page = document.body.dataset.page;
  if (page !== 'verification-sent') return;

  const email = localStorage.getItem(STORAGE_KEYS.pendingEmail) || 'your email';
  const emailNode = document.getElementById('user-email');
  if (emailNode) {
    emailNode.textContent = email;
  }
};

const setupCopies = () => {
  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;

      try {
        await navigator.clipboard.writeText(target.value);
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
          button.textContent = originalText;
        }, 1200);
      } catch (error) {
        target.select();
        document.execCommand('copy');
      }
    });
  });
};

const setupLogout = () => {
  document.querySelectorAll('[data-action="logout"]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      logoutUser();
    });
  });
};

const bindForms = () => {
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  const signupForm = document.getElementById('signup-form');
  if (signupForm) signupForm.addEventListener('submit', handleSignup);

  const forgotPasswordForm = document.getElementById('forgot-password-form');
  if (forgotPasswordForm) forgotPasswordForm.addEventListener('submit', handleForgotPassword);

  const resetPasswordForm = document.getElementById('reset-password-form');
  if (resetPasswordForm) resetPasswordForm.addEventListener('submit', handleResetPassword);
};

const setupPortalSelection = () => {
  const selectedPortal = getRequestedPortal();
  const choiceInputs = document.querySelectorAll('input[name="portal"]');
  choiceInputs.forEach((input) => {
    input.checked = input.value === selectedPortal;
  });

  const form = document.getElementById('login-form');
  if (!form) return;

  choiceInputs.forEach((input) => {
    input.addEventListener('change', () => {
      const checkedPortal = form.querySelector('input[name="portal"]:checked');
      if (checkedPortal) {
        form.dataset.portal = checkedPortal.value;
      }
    });
  });
};

document.addEventListener('DOMContentLoaded', () => {
  setupYear();
  setupPasswordToggles();
  bindForms();
  setupPortalSelection();
  ensureAuthState();
  setupDashboardUser();
  setupVerificationMessage();
  setupCopies();
  setupLogout();

  if (document.body.dataset.page === 'login' || document.body.dataset.page === 'signup' || document.body.dataset.page === 'forgot-password' || document.body.dataset.page === 'reset-password') {
    const messageBox = document.getElementById('form-message');
    if (messageBox && messageBox.textContent.trim() === '') {
      messageBox.style.display = 'none';
    }
  }
});
