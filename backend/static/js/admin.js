document.addEventListener('DOMContentLoaded', () => {
  activateSidebarNavigation();
  bindSearchFilters();
  bindTypeOptions();
  bindActionButtons();
  bindWizardActions();
  setupPortalSwitch();
  loadUserDirectory();
});

function setupPortalSwitch() {
  const topbar = document.querySelector('.topbar');
  if (!topbar) return;

  const existing = topbar.querySelector('.portal-switch');
  if (existing) return;

  const link = document.createElement('a');
  link.href = './dashboard.html';
  link.className = 'portal-switch';
  link.textContent = 'Student side';
  link.setAttribute('aria-label', 'Open student side');

  const userBadge = topbar.querySelector('.user-badge');
  if (userBadge) {
    topbar.insertBefore(link, userBadge);
  } else {
    topbar.appendChild(link);
  }
}

function activateSidebarNavigation() {
  const currentPath = window.location.pathname.split('/').pop();

  document.querySelectorAll('.nav-item[href]').forEach((item) => {
    const href = item.getAttribute('href');
    if (!href || href.startsWith('#')) return;

    const targetFile = href.split('/').pop();
    if (targetFile === currentPath) {
      item.classList.add('active');
    }
  });
}

function bindSearchFilters() {
  const searchInputs = Array.from(document.querySelectorAll('input')).filter((input) => {
    const placeholder = (input.placeholder || '').toLowerCase();
    const ariaLabel = (input.getAttribute('aria-label') || '').toLowerCase();
    return input.hasAttribute('data-search') || placeholder.includes('search') || ariaLabel.includes('search');
  });

  searchInputs.forEach((input) => {
    input.addEventListener('input', () => {
      const filter = input.value.trim().toLowerCase();
      const scope = input.closest('.content') || document.body;
      const rows = Array.from(scope.querySelectorAll('table tbody tr'));

      rows.forEach((row) => {
        const rowText = row.textContent.toLowerCase();
        row.style.display = rowText.includes(filter) ? '' : 'none';
      });
    });
  });
}

async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('uptorps_access_token');
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (error) {
      data = text;
    }
  }

  if (!response.ok) {
    const message = data && typeof data === 'object'
      ? (data.detail || data.message || JSON.stringify(data))
      : String(data || 'Request failed');
    throw new Error(message);
  }

  return data;
}

function mapAdminTypeToBackend(value) {
  if (!value) return null;
  const normalized = String(value).trim().toUpperCase();
  if (normalized === 'MANAGER' || normalized === 'MANAGER') return 'MANAGER';
  if (normalized === 'DEVELOPER' || normalized === 'DEV') return 'DEVELOPER';
  return normalized;
}

function mapSpecializationToBackend(value) {
  const normalized = String(value || '').trim();
  if (!normalized) return null;
  if (normalized.toLowerCase().includes('frontend')) return 'FRONTEND';
  if (normalized.toLowerCase().includes('backend')) return 'BACKEND';
  if (normalized.toLowerCase().includes('security')) return 'SECURITY';
  return normalized.toUpperCase();
}

async function loadUserDirectory() {
  const tables = document.querySelectorAll('table tbody');
  if (!tables.length) return;

  const token = localStorage.getItem('uptorps_access_token');
  if (!token) return;

  try {
    const users = await apiFetch('/api/accounts/users/');
    const tableBodies = Array.from(document.querySelectorAll('table tbody'));
    tableBodies.forEach((tbody) => {
      if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="6">No users found.</td></tr>';
        return;
      }

      tbody.innerHTML = users.map((user) => {
        const role = (user.role || 'STUDENT').toUpperCase();
        const adminType = (user.admin_type || '—').toUpperCase();
        const specialization = user.dev_specialization ? String(user.dev_specialization).replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '—';
        const status = user.is_active ? 'Active' : 'Inactive';
        const displayName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email;
        return `
          <tr data-user-id="${user.uuid}">
            <td>${displayName}<br /><span class="meta">${user.email}</span></td>
            <td><span class="role-badge">${role === 'ADMIN' ? 'Admin' : role === 'TEACHER' ? 'Teacher' : role === 'PREMIUM_TEACHER' ? 'Premium Teacher' : role.replace(/_/g, ' ')}</span></td>
            <td>${role === 'ADMIN' ? (adminType === 'MANAGER' ? '<span class="role-badge">Manager</span>' : adminType === 'DEVELOPER' ? '<span class="role-badge">Developer</span>' : adminType) : '—'}</td>
            <td>${role === 'ADMIN' && adminType === 'DEVELOPER' ? specialization : '—'}</td>
            <td><span class="status-pill ${status === 'Active' ? 'active' : 'inactive'}">${status}</span></td>
            <td><button class="inline-button danger" data-action="delete-user" data-user-id="${user.uuid}">Delete</button></td>
          </tr>
        `;
      }).join('');
    });
  } catch (error) {
    console.warn('Could not load backend users:', error);
  }
}

async function deleteUserAccount(userUuid) {
  if (!userUuid) return false;
  try {
    await apiFetch(`/api/accounts/users/${userUuid}/delete/`, { method: 'DELETE' });
    showToast('User deleted successfully.');
    loadUserDirectory();
    return true;
  } catch (error) {
    showToast(error.message || 'Unable to delete user.');
    return false;
  }
}

function bindTypeOptions() {
  const options = document.querySelectorAll('.type-option');
  options.forEach((option) => {
    option.addEventListener('click', () => {
      options.forEach((node) => node.classList.remove('selected'));
      option.classList.add('selected');
      if (typeof updateReviewSummary === 'function') {
        updateReviewSummary();
      }
    });
  });
}

function bindWizardActions() {
  const createPage = window.location.pathname.endsWith('admin-create-account.html');
  if (!createPage) return;

  const wizardBack = document.getElementById('wizardBack');
  const wizardCancel = document.getElementById('wizardCancel');
  const wizardPrimaryAction = document.getElementById('wizardPrimaryAction');

  if (wizardBack) {
    wizardBack.addEventListener('click', () => {
      if (window.accountWizardState && window.accountWizardState.currentStep > 1) {
        window.accountWizardState.currentStep -= 1;
        updateWizardState();
      } else {
        showToast('You are already on the first step.');
      }
    });
  }

  if (wizardCancel) {
    wizardCancel.addEventListener('click', () => {
      resetWizard();
      showToast('Account creation was cancelled.');
    });
  }

  if (wizardPrimaryAction) {
    wizardPrimaryAction.addEventListener('click', () => {
      if (!window.accountWizardState) {
        window.accountWizardState = { currentStep: 1, selectedRole: 'Administrator' };
      }

      const current = window.accountWizardState.currentStep;
      if (current === 1) {
        window.accountWizardState.currentStep = 2;
        updateWizardState();
        return;
      }

      if (current === 2) {
        if (!validateStepTwo()) return;
        updateReviewSummary();
        window.accountWizardState.currentStep = 3;
        updateWizardState();
        return;
      }

      if (current === 3) {
        if (!persistAdministrativeAccount()) {
          return;
        }
        resetWizard();
      }
    });
  }

  window.accountWizardState = { currentStep: 1, selectedRole: getSelectedRole() };
  updateWizardState();
  updateReviewSummary();
}

function getSelectedRole() {
  const selected = document.querySelector('.type-option.selected');
  return selected ? selected.dataset.role || 'Administrator' : 'Administrator';
}

function updateWizardState() {
  if (!window.accountWizardState) return;

  const current = window.accountWizardState.currentStep;
  const wizardSteps = Array.from(document.querySelectorAll('.wizard-step'));
  const panels = Array.from(document.querySelectorAll('.wizard-panel'));

  wizardSteps.forEach((step, index) => {
    step.classList.toggle('active', index + 1 === current);
  });

  panels.forEach((panel) => {
    const isActive = Number(panel.dataset.step) === current;
    panel.classList.toggle('active', isActive);
  });

  const primaryAction = document.getElementById('wizardPrimaryAction');
  if (primaryAction) {
    primaryAction.textContent = current === 3 ? 'Create account' : 'Continue';
  }

  const backButton = document.getElementById('wizardBack');
  if (backButton) {
    backButton.style.visibility = current === 1 ? 'hidden' : 'visible';
  }

  const adminTypeField = document.getElementById('adminTypeField');
  const specializationField = document.getElementById('specializationField');
  const selectedRole = getSelectedRole();
  const isAdminRole = selectedRole === 'Administrator';
  if (adminTypeField) {
    adminTypeField.style.display = isAdminRole ? 'flex' : 'none';
  }
  if (specializationField) {
    const shouldShow = isAdminRole && document.getElementById('adminTypeSelect')?.value === 'Developer';
    specializationField.style.display = shouldShow ? 'flex' : 'none';
  }
}

function validateStepTwo() {
  const requiredFields = [
    { id: 'fullName', message: 'Full name is required.' },
    { id: 'emailAddress', message: 'Email address is required.' },
    { id: 'password', message: 'A password is required.' },
    { id: 'confirmPassword', message: 'Please confirm the password.' }
  ];

  let valid = true;
  requiredFields.forEach(({ id, message }) => {
    const input = document.getElementById(id);
    const hasValue = (input?.value || '').trim();
    if (!hasValue) {
      valid = false;
      input.classList.add('invalid');
      showFieldError(input, message);
    } else {
      input.classList.remove('invalid');
      clearFieldError(input);
    }
  });

  const emailInput = document.getElementById('emailAddress');
  const emailValue = emailInput?.value.trim() || '';
  if (emailValue && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
    valid = false;
    emailInput.classList.add('invalid');
    showFieldError(emailInput, 'Email format is invalid.');
  }

  const passwordInput = document.getElementById('password');
  const passwordValue = passwordInput?.value || '';
  if (passwordValue && passwordValue.length < 8) {
    valid = false;
    passwordInput.classList.add('invalid');
    showFieldError(passwordInput, 'Password must be at least 8 characters.');
  }

  const confirm = document.getElementById('confirmPassword');
  if (passwordValue && confirm?.value && passwordValue !== confirm.value) {
    valid = false;
    confirm.classList.add('invalid');
    showFieldError(confirm, 'Passwords do not match.');
  }

  const selectedRole = getSelectedRole();
  if (selectedRole === 'Administrator') {
    const adminType = document.getElementById('adminTypeSelect');
    if (!adminType?.value) {
      valid = false;
      adminType.classList.add('invalid');
      showFieldError(adminType, 'Please select an admin type.');
    } else {
      adminType.classList.remove('invalid');
      clearFieldError(adminType);
    }

    if (adminType?.value === 'Developer') {
      const specialization = document.getElementById('specializationSelect');
      if (!specialization?.value) {
        valid = false;
        specialization.classList.add('invalid');
        showFieldError(specialization, 'Please choose a developer specialization.');
      } else {
        specialization.classList.remove('invalid');
        clearFieldError(specialization);
      }
    }
  }

  return valid;
}

async function persistAdministrativeAccount() {
  const selectedRole = getSelectedRole();
  const fullName = document.getElementById('fullName')?.value.trim() || '';
  const email = document.getElementById('emailAddress')?.value.trim() || '';
  const password = document.getElementById('password')?.value || '';
  const adminType = document.getElementById('adminTypeSelect')?.value || '';
  const specialization = document.getElementById('specializationSelect')?.value || '';

  if (!fullName || !email || !password) {
    showToast('Complete all required account details before creating an admin account.');
    return false;
  }

  const token = localStorage.getItem('uptorps_access_token');
  const normalizedEmail = String(email).trim().toLowerCase();
  const roleValue = selectedRole === 'Administrator' ? 'ADMIN' : selectedRole === 'Teacher' ? 'TEACHER' : 'PREMIUM_TEACHER';

  if (token) {
    try {
      const payload = {
        username: fullName.replace(/\s+/g, ' ').trim(),
        email: normalizedEmail,
        password,
        role: roleValue,
        admin_type: selectedRole === 'Administrator' ? mapAdminTypeToBackend(adminType) : null,
        dev_specialization: selectedRole === 'Administrator' && mapAdminTypeToBackend(adminType) === 'DEVELOPER' ? mapSpecializationToBackend(specialization) : null
      };

      if (selectedRole === 'Administrator' && !payload.admin_type) {
        throw new Error('Choose an admin type before creating the account.');
      }

      if (payload.admin_type === 'DEVELOPER' && !payload.dev_specialization) {
        throw new Error('Developer admins require a specialization.');
      }

      await apiFetch('/api/accounts/create-admin/', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      showToast(`${selectedRole} account created successfully.`);
      return true;
    } catch (error) {
      showToast(error.message || 'Backend account creation failed.');
      return false;
    }
  }

  const existingAccounts = JSON.parse(localStorage.getItem('uptorps_accounts') || '{}');
  if (existingAccounts[normalizedEmail]) {
    showToast('This account already exists. Use a different email address.');
    return false;
  }

  existingAccounts[normalizedEmail] = {
    email: normalizedEmail,
    password,
    role: roleValue.toLowerCase(),
    name: fullName,
    adminType,
    specialization,
    createdBy: 'admin'
  };

  localStorage.setItem('uptorps_accounts', JSON.stringify(existingAccounts));
  showToast(`${selectedRole} account created for ${fullName}.`);
  return true;
}

function updateReviewSummary() {
  const selectedRole = getSelectedRole();
  const nameValue = document.getElementById('fullName')?.value.trim() || '—';
  const emailValue = document.getElementById('emailAddress')?.value.trim() || '—';
  const adminTypeValue = document.getElementById('adminTypeSelect')?.value || '—';
  const specializationValue = document.getElementById('specializationSelect')?.value || '—';

  const reviewRole = document.getElementById('reviewRole');
  const reviewAdminType = document.getElementById('reviewAdminType');
  const reviewSpecialization = document.getElementById('reviewSpecialization');
  const reviewName = document.getElementById('reviewName');
  const reviewEmail = document.getElementById('reviewEmail');

  if (reviewRole) reviewRole.textContent = selectedRole;
  if (reviewAdminType) reviewAdminType.textContent = selectedRole === 'Administrator' ? adminTypeValue || '—' : '—';
  if (reviewSpecialization) reviewSpecialization.textContent = selectedRole === 'Administrator' && adminTypeValue === 'Developer' ? specializationValue : '—';
  if (reviewName) reviewName.textContent = nameValue;
  if (reviewEmail) reviewEmail.textContent = emailValue;
}

function showFieldError(input, message) {
  if (!input) return;
  let error = input.parentElement.querySelector('.field-error');
  if (!error) {
    error = document.createElement('div');
    error.className = 'field-error';
    input.parentElement.appendChild(error);
  }
  error.textContent = message;
}

function clearFieldError(input) {
  if (!input) return;
  const error = input.parentElement.querySelector('.field-error');
  if (error) error.remove();
}

function resetWizard() {
  window.accountWizardState = { currentStep: 1, selectedRole: 'Administrator' };
  const selectedOption = document.querySelector('.type-option.selected');
  if (selectedOption) selectedOption.classList.remove('selected');
  const firstOption = document.querySelector('.type-option[data-role="Administrator"]');
  if (firstOption) firstOption.classList.add('selected');

  ['fullName', 'emailAddress', 'password', 'confirmPassword', 'adminTypeSelect', 'specializationSelect'].forEach((id) => {
    const node = document.getElementById(id);
    if (node) {
      node.value = '';
      node.classList.remove('invalid');
      clearFieldError(node);
    }
  });

  updateWizardState();
  updateReviewSummary();
}

function bindActionButtons() {
  const interactiveButtons = Array.from(document.querySelectorAll('.inline-button, .btn, .page-cta.primary'));

  interactiveButtons.forEach((button) => {
    button.addEventListener('click', async (event) => {
      const action = button.dataset.action;
      const isPrimaryCreateFlow = window.location.pathname.endsWith('admin-create-account.html') && button.textContent.trim().toLowerCase().includes('continue');
      if (isPrimaryCreateFlow) return;

      if (action === 'delete-user') {
        const userUuid = button.dataset.userId;
        if (userUuid) {
          event.preventDefault();
          const confirmed = window.confirm('Delete this user account?');
          if (confirmed) {
            await deleteUserAccount(userUuid);
          }
        }
        return;
      }

      const row = button.closest('tr');
      if (row) {
        event.preventDefault();
        const values = Array.from(row.children).map((cell, index) => {
          const header = row.closest('table')?.querySelectorAll('th')[index];
          return {
            label: header ? header.textContent.trim() : `Column ${index + 1}`,
            value: cell.textContent.trim()
          };
        }).filter((entry) => entry.value && entry.label !== 'Actions');

        openModal('Record details', values);
        return;
      }

      if (button.textContent.trim().toLowerCase().includes('view')) {
        openModal('Action', [{ label: 'Status', value: 'Frontend-only preview mode' }]);
      }
    });
  });
}

function openModal(title, items) {
  const backdrop = document.createElement('div');
  backdrop.className = 'admin-modal-backdrop';
  backdrop.innerHTML = `
    <div class="admin-modal" role="dialog" aria-modal="true">
      <div class="admin-modal-header">
        <h3>${title}</h3>
        <button class="admin-modal-close" aria-label="Close">×</button>
      </div>
      <div class="admin-modal-body">
        ${items.map((item) => `
          <div class="admin-modal-row">
            <span>${item.label}</span>
            <strong>${item.value}</strong>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  backdrop.addEventListener('click', (event) => {
    if (event.target === backdrop) backdrop.remove();
  });

  backdrop.querySelector('.admin-modal-close').addEventListener('click', () => backdrop.remove());
  document.body.appendChild(backdrop);
}

function showToast(message) {
  const existing = document.querySelector('.admin-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'admin-toast';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 2200);
}
