import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { templateApi } from '../api/templateApi'
import { problemApi } from '../api/problemApi'
import Loading from '../components/Loading.jsx'
import Badge from '../components/Badge.jsx'

export default function TemplatePractice() {
  const { templateId } = useParams()
  const [template, setTemplate] = useState(null)
  const [problems, setProblems] = useState([])
  const [selectedProblem, setSelectedProblem] = useState(null)
  const [selectedProblemDetail, setSelectedProblemDetail] = useState(null)
  const [showHint, setShowHint] = useState(false)

  useEffect(() => {
    setTemplate(null)
    if (templateId) {
      templateApi.get(templateId).then(setTemplate).catch(console.error)
    } else {
      templateApi.list().then(page => {
        const templates = page.items || []
        if (templates.length > 0) {
          setTemplate(templates[0])
        }
      }).catch(console.error)
    }
  }, [templateId])

  useEffect(() => {
    if (!template) return
    problemApi.list({ limit: 500 }).then(page => {
      const allProblems = page.items || []
      const templateTags = new Set(template.tags || [])
      const matched = allProblems.filter(p => {
        const problemTags = new Set(p.tags || [])
        return [...problemTags].some(tag => templateTags.has(tag))
      })
      setProblems(matched)
      setSelectedProblem(matched[0] || null)
    }).catch(console.error)
  }, [template])

  useEffect(() => {
    if (!selectedProblem?.id) {
      setSelectedProblemDetail(null)
      return
    }
    setSelectedProblemDetail(null)
    problemApi.detail(selectedProblem.id)
      .then(setSelectedProblemDetail)
      .catch(() => setSelectedProblemDetail(selectedProblem))
  }, [selectedProblem?.id])

  if (!template) return <Loading />

  const detail = selectedProblemDetail || selectedProblem

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/templates" className="back-link">← 返回模板库</Link>
          <h1>模板练习模式</h1>
          <p>使用模板解决相关题目，巩固模板应用能力。</p>
        </div>
      </div>

      <div className="template-practice-container">
        <section className="card template-section">
          <h2>当前模板</h2>
          <div className="template-info">
            <h3>{template.name}</h3>
            <div className="template-meta">
              <Badge>{template.category}</Badge>
              <Badge>{template.language}</Badge>
            </div>
            <p>{template.explanation}</p>
            <p className="muted">适用：{template.usage_scenario}</p>
          </div>
          <div className="template-code-box">
            <pre>{template.code}</pre>
          </div>
          <button className="button" onClick={() => setShowHint(!showHint)}>
            {showHint ? '隐藏提示' : '显示提示'}
          </button>
          {showHint && (
            <div className="hint-box">
              <h4>💡 使用提示</h4>
              <ul>
                <li>理解模板的核心逻辑和适用场景</li>
                <li>分析题目，找出与模板的关联点</li>
                <li>尝试修改模板来解决具体问题</li>
                <li>注意边界条件和特殊情况</li>
              </ul>
            </div>
          )}
        </section>

        <section className="card problems-section">
          <h2>练习题 ({problems.length} 题)</h2>
          {problems.length === 0 ? (
            <p className="muted">暂无和该模板标签直接匹配的题目。</p>
          ) : (
            <div className="practice-problems-list">
              {problems.map(p => (
                <div
                  key={p.id}
                  className={`practice-problem-item ${selectedProblem?.id === p.id ? 'selected' : ''}`}
                  onClick={() => setSelectedProblem(p)}
                >
                  <div className="problem-header">
                    <Badge type={p.difficulty.toLowerCase()}>{p.difficulty}</Badge>
                    <span className="problem-title">{p.title_cn || p.title}</span>
                  </div>
                  <div className="problem-tags">
                    {(p.tags || []).map(tag => (
                      <span key={tag} className="small-tag">{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {detail && (
          <section className="card problem-detail-section">
            <h2>题目详情</h2>
            <div className="problem-detail-header">
              <h3>{detail.title_cn || detail.title}</h3>
              <Badge type={detail.difficulty.toLowerCase()}>{detail.difficulty}</Badge>
            </div>
            <p>{detail.description || '题目详情加载中...'}</p>
            <h3>示例</h3>
            {(detail.examples || []).length > 0 ? (
              (detail.examples || []).map((ex, index) => (
                <pre key={index}>输入：{ex.input}\n输出：{ex.output}</pre>
              ))
            ) : (
              <p className="muted">暂无示例。</p>
            )}
            <Link to={`/problems/${detail.id}`} className="button">
              开始做题
            </Link>
          </section>
        )}
      </div>
    </div>
  )
}
