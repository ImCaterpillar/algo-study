import { api } from './client'

export const statsApi = {
  summary: () => api.get('/stats/summary').then(res => res.data),
  dashboard: () => api.get('/stats/dashboard').then(res => res.data),
  masteryDistribution: () => api.get('/stats/mastery-distribution').then(res => res.data),
  reviewEffectiveness: () => api.get('/stats/review-effectiveness').then(res => res.data),
  weakness: () => api.get('/stats/weakness').then(res => res.data),
  weeklyReport: () => api.get('/stats/weekly-report').then(res => res.data),
  tagMasteryRadar: () => api.get('/stats/tag-mastery-radar').then(res => res.data),
  personalizedRecommendations: (limit = 5) => api.get('/stats/personalized-recommendations', { params: { limit } }).then(res => res.data),
}