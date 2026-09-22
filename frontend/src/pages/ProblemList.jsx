import { useEffect, useState } from 'react'
import { problemApi } from '../api/problemApi'
import Loading from '../components/Loading.jsx'
import ProblemCard from '../components/ProblemCard.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'

const difficulties = ['', 'Easy', 'Medium', 'Hard']
const stages = ['', 'beginner', 'core', 'advanced']
const statuses = ['', 'Not Started', 'Attempted', 'Accepted', 'Need Review']
const PAGE_SIZE = 60

export default function ProblemList() {
  const [problems, setProblems] = useState(null)
  const [allTags, setAllTags] = useState([])
  const [difficulty, setDifficulty] = useState('')
  const [stage, setStage] = useState('')
  const [tag, setTag] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

  const params = {
    difficulty: difficulty || undefined,
    stage: stage || undefined,
    tag: tag || undefined,
    status: status || undefined,
  }

  useEffect(() => {
    problemApi.list({ limit: 500 })
      .then(page => setAllTags(Array.from(new Set((page.items || []).flatMap(p => p.tags || []))).sort()))
      .catch(() => setAllTags([]))
  }, [])

  useEffect(() => {
    loadFirstPage()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [difficulty, stage, tag, status])

  async function loadFirstPage() {
    setError('')
    setProblems(null)
    setOffset(0)
    try {
      const page = await problemApi.list({ ...params, limit: PAGE_SIZE, offset: 0 })
      const items = page.items || []
      setProblems(items)
      setTotal(page.total || items.length)
      setHasMore(Boolean(page.has_more))
      setOffset(items.length)
    } catch (e) {
      setError(e.response?.data?.detail || '题库加载失败，请检查后端服务是否运行。')
      setProblems([])
      setHasMore(false)
    }
  }

  async function loadMore() {
    setLoadingMore(true)
    setError('')
    try {
      const page = await problemApi.list({ ...params, limit: PAGE_SIZE, offset })
      const items = page.items || []
      setProblems(prev => [...(prev || []), ...items])
      setTotal(page.total || total)
      setHasMore(Boolean(page.has_more))
      setOffset(prev => prev + items.length)
    } catch (e) {
      setError(e.response?.data?.detail || '加载更多失败。')
    }
    setLoadingMore(false)
  }

  if (!problems) return <Loading />

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>精选题库</h1>
          <p>题库来自高频面试题路线，先按推荐顺序刷，后面再根据统计补弱项。</p>
          <p className="muted">当前筛选共 {total} 题，已加载 {problems?.length || 0} 题。</p>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={loadFirstPage} />

      <div className="filters card">
        <label>难度
          <select value={difficulty} onChange={e => setDifficulty(e.target.value)}>
            {difficulties.map(x => <option key={x} value={x}>{x || '全部'}</option>)}
          </select>
        </label>
        <label>阶段
          <select value={stage} onChange={e => setStage(e.target.value)}>
            {stages.map(x => <option key={x} value={x}>{x || '全部'}</option>)}
          </select>
        </label>
        <label>状态
          <select value={status} onChange={e => setStatus(e.target.value)}>
            {statuses.map(x => <option key={x} value={x}>{x || '全部'}</option>)}
          </select>
        </label>
        <label>标签
          <select value={tag} onChange={e => setTag(e.target.value)}>
            <option value="">全部</option>
            {allTags.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </label>
      </div>

      {problems.length === 0 ? (
        <div className="card empty-state">没有匹配的题目，试试放宽筛选条件。</div>
      ) : (
        <div className="problem-grid">
          {problems.map(problem => <ProblemCard key={problem.id} problem={problem} />)}
        </div>
      )}

      {hasMore && (
        <div className="pagination-actions">
          <button className="button secondary" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? '加载中...' : '加载更多'}
          </button>
        </div>
      )}
    </div>
  )
}
