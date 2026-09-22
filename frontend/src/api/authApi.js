import { api } from './client'

export const authApi = {
  login: (username, password) => api.post('/auth/login', new URLSearchParams({ username, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }).then(res => res.data),
  register: (data) => api.post('/auth/register', data).then(res => res.data),
  me: () => api.get('/auth/me').then(res => res.data),
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },
  setToken: (token) => {
    localStorage.setItem('token', token)
  },
  getToken: () => localStorage.getItem('token'),
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user))
  },
  getUser: () => {
    const user = localStorage.getItem('user')
    if (!user) return null
    try {
      return JSON.parse(user)
    } catch {
      localStorage.removeItem('user')
      return null
    }
  },
  isLoggedIn: () => !!localStorage.getItem('token'),
}
