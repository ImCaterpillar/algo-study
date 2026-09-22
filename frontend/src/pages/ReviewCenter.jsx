import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reviewApi } from '../api/reviewApi'
import Loading from '../components/Loading.jsx'

const REVIEW_RESULTS = ['掌握', '部分遗忘', '完全遗忘']
const SCHEDULE_LABELS = [
  { days: 1, label: 'D+1' },
  { days: 3, label: 'D+3' },
  { days: 7, label: 'D+7' },
]

export default function ReviewCenter() {
  const [dueItems, setDueItems] = useState([])
  const [dueTotal, setDueTotal] = useState(0)
  const [scheduleItems, setScheduleItems] = useState({ 1: [], 3: [], 7: [] })
  const [activeTab, setActiveTab] = useState('due')
  const [reviewingId, setReviewingId] = useState(null)
  const [reviewResult, setReviewResult] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const due = await reviewApi.due()
      setDueItems(due.items || [])
      setDueTotal(due.total || 0)
      const schedule = { 1: [], 3: [], 7: [] }
      for (const s of SCHEDULE_LABELS) {
        schedule[s.days] = await reviewApi.schedule(s.days)
      }
      setScheduleItems(schedule)
    } catch (err) {
      console.error(err)
    }
  }

  async function handleQuickReview(problemId, result) {
    try {
      await reviewApi.quickReview(problemId, result)
      setReviewingId(null)
      setReviewResult('')
      loadData()
    } catch (err) {
      console.error(err)
    }
  }

  function startReview(id) {
    setReviewingId(id)
    setReviewResult('')
  }

  function cancelReview() {
    setReviewingId(null)
    setReviewResult('')
  }

  function renderMastery(level) {
    const labels = ['未开始', '看题解懂', '能复现', '能独立做', '能讲清楚', '熟练掌握']
    return <span className={`mastery-badge mastery-${level}`}>{labels[level] || level}</span>
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>错题复盘中心</h1>
          <p>间隔复习法：D+1 → D+3 → D+7 → D+14 → D+30，逐步巩固记忆。</p>
        </div>
      </div>

      <div className="review-tabs">
        <button className={activeTab === 'due' ? 'active' : ''} onClick={() => setActiveTab('due')}>
          待复盘 ({dueTotal})
        </button>
        <button className={activeTab === 'd1' ? 'active' : ''} onClick={() => setActiveTab('d1')}>
          D+1 ({scheduleItems[1]?.length || 0})
        </button>
        <button className={activeTab === 'd3' ? 'active' : ''} onClick={() => setActiveTab('d3')}>
          D+3 ({scheduleItems[3]?.length || 0})
        </button>
        <button className={activeTab === 'd7' ? 'active' : ''} onClick={() => setActiveTab('d7')}>
          D+7 ({scheduleItems[7]?.length || 0})
        </button>
      </div>

      {activeTab === 'due' && (
        <div className="review-section">
          {dueItems.length === 0 ? (
            <div className="card">目前没有待复盘题。继续保持刷题节奏！</div>
          ) : (
            <div className="problem-grid">
              {dueItems.map(item => (
                <div key={item.problem_id} className="problem-card card">
                  {reviewingId === item.problem_id ? (
                    <div className="quick-review">
                      <h3>{item.title_cn || item.title}</h3>
                      <p className="muted">{renderMastery(item.mastery_level)}</p>
                      <div className="review-buttons">
                        {REVIEW_RESULTS.map(r => (
                          <button key={r} className={`button review-btn ${r}`} onClick={() => handleQuickReview(item.problem_id, r)}>
                            {r}
                          </button>
                        ))}
                        <button className="button secondary" onClick={cancelReview}>取消</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="problem-card-header">
                        <div>
                          <Link to={`/problems/${item.problem_id}`}><h3>{item.title_cn || item.title}</h3></Link>
                          <p className="muted">{item.title}</p>
                        </div>
                        <span className={`difficulty ${item.difficulty.toLowerCase()}`}>{item.difficulty}</span>
                      </div>
                      <div className="problem-card-meta">
                        <span>掌握度: {renderMastery(item.mastery_level)}</span>
                        <span className="review-due-tag">{item.review_due}</span>
                      </div>
                      <div className="problem-card-footer">
                        <span>已复习 {item.total_reviews} 次</span>
                        <button className="button" onClick={() => startReview(item.problem_id)}>快速复盘</button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab !== 'due' && (
        <div className="review-section">
          {(() => {
            const days = activeTab === 'd1' ? 1 : activeTab === 'd3' ? 3 : 7
            const items = scheduleItems[days] || []
            return items.length === 0 ? (
              <div className="card">暂无即将到期的复习任务。</div>
            ) : (
              <div className="problem-grid">
                {items.map(item => (
                  <div key={item.problem_id} className="problem-card card">
                    <div className="problem-card-header">
                      <div>
                        <Link to={`/problems/${item.problem_id}`}><h3>{item.title_cn || item.title}</h3></Link>
                        <p className="muted">{item.title}</p>
                      </div>
                      <span className={`difficulty ${item.difficulty.toLowerCase()}`}>{item.difficulty}</span>
                    </div>
                    <div className="problem-card-meta">
                      <span>掌握度: {renderMastery(item.mastery_level)}</span>
                      <span className="review-due-tag">{item.review_due}</span>
                    </div>
                    <div className="problem-card-footer">
                      <span>已复习 {item.total_reviews} 次</span>
                      <Link className="button" to={`/problems/${item.problem_id}`}>去刷题</Link>
                    </div>
                  </div>
                ))}
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}