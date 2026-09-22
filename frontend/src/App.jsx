import { NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import ProblemList from './pages/ProblemList.jsx'
import ProblemDetail from './pages/ProblemDetail.jsx'
import ReviewCenter from './pages/ReviewCenter.jsx'
import TemplateLibrary from './pages/TemplateLibrary.jsx'
import TemplatePractice from './pages/TemplatePractice.jsx'
import Stats from './pages/Stats.jsx'
import Login from './pages/Login.jsx'
import NotFound from './pages/NotFound.jsx'
import { authApi } from './api/authApi'

const navItems = [
  ['/', '首页'],
  ['/problems', '题库'],
  ['/reviews', '复盘'],
  ['/templates', '模板库'],
  ['/stats', '统计'],
]

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (!authApi.isLoggedIn()) {
      navigate('/login')
      setLoading(false)
      return
    }
    setLoading(false)
  }, [navigate])

  if (loading) {
    return <div className="loading">加载中...</div>
  }

  return children
}

function PublicRoute({ children }) {
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (authApi.isLoggedIn()) {
      navigate('/')
      setLoading(false)
      return
    }
    setLoading(false)
  }, [navigate])

  if (loading) {
    return <div className="loading">加载中...</div>
  }

  return children
}

export default function App() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (authApi.isLoggedIn()) {
      setUser(authApi.getUser())
    }
  }, [])

  function handleLogout() {
    authApi.logout()
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <div className="app-shell">
      <Routes>
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        
        <Route path="*" element={
          <ProtectedRoute>
            <>
              <aside className="sidebar">
                <div className="brand">AlgoStudy</div>
                <div className="subtitle">个人算法学习系统</div>
                <nav>
                  {navItems.map(([to, label]) => (
                    <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'} end={to === '/'}>
                      {label}
                    </NavLink>
                  ))}
                </nav>
                {user && (
                  <div className="user-info">
                    <div className="username">{user.username}</div>
                    <button className="logout-btn" onClick={handleLogout}>退出登录</button>
                  </div>
                )}
              </aside>
              <main className="main">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/problems" element={<ProblemList />} />
                  <Route path="/problems/:id" element={<ProblemDetail />} />
                  <Route path="/reviews" element={<ReviewCenter />} />
                  <Route path="/templates" element={<TemplateLibrary />} />
                  <Route path="/templates/practice" element={<TemplatePractice />} />
                  <Route path="/templates/practice/:templateId" element={<TemplatePractice />} />
                  <Route path="/stats" element={<Stats />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </main>
            </>
          </ProtectedRoute>
        } />
      </Routes>
    </div>
  )
}