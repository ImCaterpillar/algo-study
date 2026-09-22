import { api } from './client'

export const templateApi = {
  list: (params = {}) => api.get('/templates', { params }).then(res => res.data),
  get: (id) => api.get(`/templates/${id}`).then(res => res.data),
  recommend: (problemId) => api.get(`/templates/recommend/${problemId}`).then(res => res.data),
  create: (data) => api.post('/templates', data).then(res => res.data),
  update: (id, data) => api.put(`/templates/${id}`, data).then(res => res.data),
  copy: (id) => api.post(`/templates/${id}/copy`).then(res => res.data),
  delete: (id) => api.delete(`/templates/${id}`).then(res => res.data),
  categories: () => api.get('/templates/categories').then(res => res.data),
  languages: () => api.get('/templates/languages').then(res => res.data),
}