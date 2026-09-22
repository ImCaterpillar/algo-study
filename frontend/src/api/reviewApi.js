import { api } from './client'

export const reviewApi = {
  due: () => api.get('/reviews/due').then(res => res.data),
  log: (payload) => api.post('/reviews/log', payload).then(res => res.data),
  plan: (problemId) => api.get(`/reviews/plan/${problemId}`).then(res => res.data),
  history: (problemId) => api.get('/reviews/history', { params: { problem_id: problemId } }).then(res => res.data),
  schedule: (days) => api.get(`/reviews/schedule/${days}`).then(res => res.data),
  quickReview: (problemId, result) => api.post('/reviews/quick-review', { problem_id: problemId, result }).then(res => res.data),
}