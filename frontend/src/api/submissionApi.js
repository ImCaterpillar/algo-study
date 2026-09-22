import { api } from './client'

export const submissionApi = {
  create: (payload) => api.post('/submissions', payload).then(res => res.data),
  byProblem: (problemId) => api.get(`/submissions/problem/${problemId}`).then(res => res.data),
}
