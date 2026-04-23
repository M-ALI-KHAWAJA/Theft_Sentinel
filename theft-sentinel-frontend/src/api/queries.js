import axiosInstance from './axios';

export const listMyQueries = () => axiosInstance.get('/api/queries/');

export const createQuery = (message) =>
  axiosInstance.post('/api/queries/', { message });

export const answerQuery = (id, response) =>
  axiosInstance.post(`/api/queries/${id}/answer/`, { response });

export const approveQuery = (id) => axiosInstance.post(`/api/queries/${id}/approve/`);

export const deleteQuery = (id) => axiosInstance.delete(`/api/queries/${id}/`);
