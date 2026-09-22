import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page">
      <section className="card empty-state">
        <h1>页面不存在</h1>
        <p>当前路径没有对应页面。</p>
        <Link className="button" to="/">返回首页</Link>
      </section>
    </div>
  )
}
