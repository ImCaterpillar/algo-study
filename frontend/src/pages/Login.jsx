import { useState } from 'react'
import { authApi } from '../api/authApi'

export default function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    
    if (!isLogin) {
      if (password !== confirmPassword) {
        setError('密码不一致')
        return
      }
    }

    setLoading(true)
    try {
      if (isLogin) {
        const result = await authApi.login(username, password)
        authApi.setToken(result.access_token)
        const user = await authApi.me()
        authApi.setUser(user)
        window.location.href = '/'
      } else {
        await authApi.register({ username, email, password })
        setIsLogin(true)
        setError('注册成功，请登录')
      }
    } catch (e) {
      setError(e.response?.data?.detail || '登录失败')
    }
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>AlgoStudy</h1>
        <p className="subtitle">算法学习与刷题复盘系统</p>
        
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label>邮箱</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
              />
            </div>
          )}
          
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="username"
              required
            />
          </div>
          
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="password"
              required
            />
          </div>
          
          {!isLogin && (
            <div className="form-group">
              <label>确认密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="confirm password"
                required
              />
            </div>
          )}
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="button primary" disabled={loading}>
            {loading ? '加载中...' : (isLogin ? '登录' : '注册')}
          </button>
        </form>
        
        <p className="toggle-link">
          {isLogin ? '还没有账号？' : '已有账号？'}
          <button onClick={() => { setIsLogin(!isLogin); setError('') }}>
            {isLogin ? '立即注册' : '立即登录'}
          </button>
        </p>
      </div>
    </div>
  )
}