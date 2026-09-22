import { api } from './client'

export const aiApi = {
  analyze: (data) => api.post('/ai/analyze', data).then(res => res.data),
  hints: (data) => api.post('/ai/hints', data).then(res => res.data),
  review: (data) => api.post('/ai/review', data).then(res => res.data),
  explain: (data) => api.post('/ai/explain', data).then(res => res.data),
}