import axiosInstance from './axios';

export const registerBranch = (payload) =>
  axiosInstance.post('/api/tenants/register/', payload);

export const getBranchProfile = () => axiosInstance.get('/api/tenants/branch-profile/');

export const patchBranchProfile = (payload) =>
  axiosInstance.patch('/api/tenants/branch-profile/', payload);

export const getSuperAdminDashboard = () =>
  axiosInstance.get('/api/super-admin/dashboard/');

export const listTenants = () =>
  axiosInstance.get('/api/super-admin/tenants/');

export const approveTenant = (tenantId) =>
  axiosInstance.post(`/api/super-admin/tenants/${tenantId}/approve/`);

export const rejectTenant = (tenantId) =>
  axiosInstance.post(`/api/super-admin/tenants/${tenantId}/reject/`);

export const listPasswordResetRequests = () =>
  axiosInstance.get('/api/super-admin/password-reset-requests/');

export const approvePasswordResetRequest = (id) =>
  axiosInstance.post(`/api/super-admin/password-reset-requests/${id}/approve/`);

export const rejectPasswordResetRequest = (id) =>
  axiosInstance.post(`/api/super-admin/password-reset-requests/${id}/reject/`);

export const deletePasswordResetRequest = (id) =>
  axiosInstance.delete(`/api/password-reset-request/${id}/`);

export const suspendTenant = (tenantId) =>
  axiosInstance.post(`/api/super-admin/tenants/${tenantId}/suspend/`);

export const reapproveTenant = (tenantId) =>
  axiosInstance.post(`/api/super-admin/tenants/${tenantId}/re-approve/`);

export const deleteTenantBranch = (tenantId) =>
  axiosInstance.delete(`/api/super-admin/tenants/${tenantId}/delete/`);

/** @param {Record<string, unknown> | undefined} payload Authenticated: omit or `{}`. Login (unauthenticated): `{ email }`. */
export const superAdminRequestPasswordEmail = (payload) =>
  axiosInstance.post('/api/super-admin/reset-password/', payload ?? {});

export const superAdminDeleteAccount = () =>
  axiosInstance.delete('/api/super-admin/delete-account/');

export const getSuperAdminProfile = () => axiosInstance.get('/api/super-admin/profile/');

export const patchSuperAdminProfile = (payload) =>
  axiosInstance.patch('/api/super-admin/profile/', payload);

export const listSuperAdminQueries = () =>
  axiosInstance.get('/api/super-admin/queries/');
