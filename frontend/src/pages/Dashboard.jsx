import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { statsApi } from '../api/statsApi'
import Loading from '../components/Loading.jsx'
import ProblemCard from '../components/ProblemCard.jsx'

export default function Dashboard() {
  const [data, setData] = useState(null)

  useEffect(() => {
    statsApi.dashboard().then(setData).catch(console.error)
  }, [])

  if (!data) return <Loading />
  const s = data.summary

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>今日学习面板</h1>
          <p>阶段 3 新增：智能推荐、弱项分析、个性化学习路径。</p>
        </div>
        <Link className="button" to="/problems">开始刷题</Link>
      </div>

      <div className="metric-grid">
        <div className="metric-card"><span>总题数</span><strong>{s.total_problems}</strong></div>
        <div className="metric-card"><span>已尝试</span><strong>{s.attempted}</strong></div>
        <div className="metric-card"><span>已通过</span><strong>{s.accepted}</strong></div>
        <div className="metric-card"><span>待复盘</span><strong>{s.need_review}</strong></div>
      </div>

      {data.weakness_analysis && data.weakness_analysis.weakest_tags.length > 0 && (
        <section className="card weakness-card">
          <h2>⚠️ 弱项标签（需要加强）</h2>
          <div className="weak-tags">
            {data.weakness_analysis.weakest_tags.map(tag => (
              <span key={tag} className="weak-tag">{tag}</span>
            ))}
          </div>
          <p className="muted">根据您的错题记录和掌握度自动分析。建议优先练习这些标签的题目。</p>
        </section>
      )}

      {data.weakness_analysis && data.weakness_analysis.strongest_tags.length > 0 && (
        <section className="card strength-card">
          <h2>💪 强项标签（已掌握）</h2>
          <div className="strong-tags">
            {data.weakness_analysis.strongest_tags.map(tag => (
              <span key={tag} className="strong-tag">{tag}</span>
            ))}
          </div>
        </section>
      )}

      <section className="section">
        <div className="section-header">
          <h2>📋 今日推荐</h2>
          <span className="muted">基于弱项分析和学习进度智能推荐</span>
        </div>
        <div className="problem-grid">
          {data.recommendations.map(problem => <ProblemCard key={problem.id} problem={problem} />)}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>📊 薄弱标签详情</h2>
          <Link to="/stats" className="button secondary small">查看全部统计</Link>
        </div>
        <div className="weakness-detail">
          {Object.entries(data.weakness_analysis?.by_tag || {}).slice(0, 6).map(([tag, stats]) => (
            <div key={tag} className="weakness-item">
              <div className="weakness-info">
                <span className="weakness-tag-name">{tag}</span>
                <span className="muted">掌握度 {stats.avg_mastery}/5 · {stats.need_review}/{stats.total} 待复习</span>
              </div>
              <div className="weakness-bar">
                <div className="weakness-fill" style={{ width: `${(stats.avg_mastery / 5) * 100}%` }}></div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}