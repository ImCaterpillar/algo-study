import { api } from './client'

export const noteApi = {
  get: (problemId) => api.get(`/notes/${problemId}`).then(res => res.data),
  save: (problemId, payload) => api.put(`/notes/${problemId}`, payload).then(res => res.data),
}
