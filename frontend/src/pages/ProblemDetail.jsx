import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { problemApi } from '../api/problemApi'
import { submissionApi } from '../api/submissionApi'
import { noteApi } from '../api/noteApi'
import { templateApi } from '../api/templateApi'
import { executeApi } from '../api/executeApi'
import { aiApi } from '../api/aiApi'
import Badge from '../components/Badge.jsx'
import CodeEditor from '../components/CodeEditor.jsx'
import Loading from '../components/Loading.jsx'

const statuses = ['Accepted', 'Wrong Answer', 'Runtime Error', 'Compile Error', 'Timeout', 'Need Review', 'Attempted']
const failReasons = ['', '思路错误', '题意理解错误', '边界条件遗漏', '数据结构选择错误', '复杂度过高', '实现细节错误', '语法错误']
const languages = ['python', 'javascript', 'java', 'cpp']

export default function ProblemDetail() {
  const { id } = useParams()
  const [problem, setProblem] = useState(null)
  const [note, setNote] = useState(null)
  const [submissions, setSubmissions] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState('')
  const [status, setStatus] = useState('Accepted')
  const [failReason, setFailReason] = useState('')
  const [masteryLevel, setMasteryLevel] = useState(0)
  const [confidence, setConfidence] = useState(0)
  const [message, setMessage] = useState('')
  const [runOutput, setRunOutput] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [hints, setHints] = useState(null)
  const [isGettingHints, setIsGettingHints] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [codeReview, setCodeReview] = useState(null)
  const [isReviewing, setIsReviewing] = useState(false)

  useEffect(() => {
    Promise.all([
      problemApi.detail(id),
      noteApi.get(id),
      submissionApi.byProblem(id),
      templateApi.recommend(id),
    ]).then(([p, n, submissionPage, recs]) => {
      setProblem(p)
      setNote(n)
      setSubmissions(submissionPage.items || [])
      setRecommendations(recs)
      setMasteryLevel(p.progress?.mastery_level || 0)
      setConfidence(p.progress?.confidence || 0)
      setCode(p.starter_code?.python || '')
    }).catch(console.error)
  }, [id])

  useEffect(() => {
    if (problem?.starter_code?.[language]) {
      setCode(problem.starter_code[language])
    } else if (problem && language === 'python' && problem.starter_code?.python) {
      setCode(problem.starter_code.python)
    } else if (problem && language === 'javascript' && problem.starter_code?.javascript) {
      setCode(problem.starter_code.javascript)
    } else if (problem && language === 'java' && problem.starter_code?.java) {
      setCode(problem.starter_code.java)
    } else if (problem && language === 'cpp' && problem.starter_code?.cpp) {
      setCode(problem.starter_code.cpp)
    }
  }, [language, problem])

  const matchedTemplates = recommendations.filter(r => r.language === language)

  if (!problem || !note) return <Loading />

  async function runCode() {
    setIsRunning(true)
    setRunOutput(null)
    try {
      const result = await executeApi.run({ language, code, timeout: 10 })
      setRunOutput(result)
    } catch (e) {
      setRunOutput({ success: false, output: '', error: '请求失败', runtime_ms: 0, status: 'Error' })
    }
    setIsRunning(false)
  }

  async function getHints() {
    setIsGettingHints(true)
    try {
      const result = await aiApi.hints({
        description: problem.description || '',
        examples: problem.examples || [],
        tags: problem.tags || [],
      })
      setHints(result.hints)
    } catch (e) {
      setHints(['获取提示失败'])
    }
    setIsGettingHints(false)
  }

  async function analyzeProblem() {
    try {
      const result = await aiApi.analyze({
        description: problem.description || '',
        examples: problem.examples || [],
        constraints: problem.constraints_text || '',
        tags: problem.tags || [],
      })
      setAnalysis(result)
    } catch (e) {
      console.error('分析失败', e)
    }
  }

  async function reviewCode() {
    setIsReviewing(true)
    try {
      const result = await aiApi.review({
        code,
        language,
        problem_tags: problem.tags || [],
      })
      setCodeReview(result)
    } catch (e) {
      setCodeReview({ suggestions: ['代码审查失败'], warnings: [], overall_rating: '未知' })
    }
    setIsReviewing(false)
  }

  async function submitCode() {
    const created = await submissionApi.create({
      problem_id: Number(id),
      language,
      code,
      status,
      fail_reason: failReason || null,
      mastery_level: Number(masteryLevel),
      confidence: Number(confidence),
      is_best: status === 'Accepted',
    })
    setSubmissions([created, ...submissions])
    const updated = await problemApi.detail(id)
    setProblem(updated)
    setMessage('提交已保存。')
  }

  async function saveNote() {
    const saved = await noteApi.save(id, note)
    setNote(saved)
    setMessage('笔记已保存。')
  }

  function insertTemplate(t) {
    setCode(prev => `${prev}\n\n${t.code}`)
  }

  return (
    <div className="page detail-page">
      <div className="page-header">
        <div>
          <Link to="/problems" className="back-link">← 返回题库</Link>
          <h1>{problem.title_cn || problem.title}</h1>
          <p>{problem.title}</p>
          <div className="tag-row">
            <Badge type={problem.difficulty.toLowerCase()}>{problem.difficulty}</Badge>
            {(problem.tags || []).map(tag => <Badge key={tag}>{tag}</Badge>)}
          </div>
        </div>
        {problem.source_url && <a className="button secondary" href={problem.source_url} target="_blank">打开原题</a>}
      </div>

      {message && <div className="notice">{message}</div>}

      {analysis && (
        <section className="card ai-analysis-card">
          <h2>🤖 AI 题目分析</h2>
          <div className="analysis-content">
            <div className="analysis-item">
              <span className="analysis-label">预测难度</span>
              <Badge type={analysis.predicted_difficulty.toLowerCase()}>{analysis.predicted_difficulty}</Badge>
              <span className="analysis-confidence">置信度: {Math.round(analysis.confidence * 100)}%</span>
            </div>
            <p className="analysis-suggestion">{analysis.suggestion}</p>
            {analysis.factors.length > 0 && (
              <div className="analysis-factors">
                <span className="analysis-label">判断依据:</span>
                <ul>{analysis.factors.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </div>
            )}
          </div>
          <button className="button secondary small" onClick={() => setAnalysis(null)}>关闭</button>
        </section>
      )}

      <div className="two-column">
        <section className="card prose-card">
          <h2>题目简述</h2>
          <p>{problem.description}</p>
          <h3>关键模式</h3>
          <p>{problem.key_pattern}</p>
          <h3>示例</h3>
          {(problem.examples || []).map((ex, index) => (
            <pre key={index}>输入：{ex.input}\n输出：{ex.output}</pre>
          ))}
          <p className="muted">{problem.constraints_text}</p>
          <div className="ai-actions">
            <button className="button secondary" onClick={analyzeProblem}>📊 分析题目</button>
            <button className="button secondary" onClick={getHints} disabled={isGettingHints}>💡 获取提示</button>
          </div>
          {hints && (
            <div className="hints-box">
              <h4>💡 解题提示</h4>
              <ol>{hints.map((hint, i) => <li key={i}>{hint}</li>)}</ol>
              <button className="button secondary small" onClick={() => setHints(null)}>关闭提示</button>
            </div>
          )}
        </section>

        <section className="card editor-card">
          <div className="toolbar">
            <label>语言
              <select value={language} onChange={e => setLanguage(e.target.value)}>
                {languages.map(x => <option key={x} value={x}>{x}</option>)}
              </select>
            </label>
            <label>状态
              <select value={status} onChange={e => setStatus(e.target.value)}>
                {statuses.map(x => <option key={x} value={x}>{x}</option>)}
              </select>
            </label>
            <label>错因
              <select value={failReason} onChange={e => setFailReason(e.target.value)}>
                {failReasons.map(x => <option key={x} value={x}>{x || '无'}</option>)}
              </select>
            </label>
          </div>
          <CodeEditor language={language} code={code} onChange={setCode} />
          <div className="toolbar bottom-toolbar">
            <label>掌握度 {masteryLevel}/5
              <input type="range" min="0" max="5" value={masteryLevel} onChange={e => setMasteryLevel(e.target.value)} />
            </label>
            <label>信心 {confidence}/5
              <input type="range" min="0" max="5" value={confidence} onChange={e => setConfidence(e.target.value)} />
            </label>
            <button className="button secondary" onClick={reviewCode} disabled={isReviewing}>
              {isReviewing ? '审查中...' : '🔍 代码审查'}
            </button>
            <button className="button secondary" onClick={runCode} disabled={isRunning}>
              {isRunning ? '运行中...' : '▶ 运行'}
            </button>
            <button className="button" onClick={submitCode}>保存提交</button>
          </div>
          {codeReview && (
            <div className="code-review-box">
              <div className="review-header">
                <h4>🔍 代码审查结果</h4>
                <span className={`review-rating ${codeReview.overall_rating}`}>{codeReview.overall_rating}</span>
                <button className="close-btn" onClick={() => setCodeReview(null)}>×</button>
              </div>
              {codeReview.warnings.length > 0 && (
                <div className="review-warnings">
                  <h5>⚠️ 警告</h5>
                  <ul>{codeReview.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
                </div>
              )}
              <div className="review-suggestions">
                <h5>💡 建议</h5>
                <ul>{codeReview.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            </div>
          )}
          {runOutput && (
            <div className={`run-output ${runOutput.success ? 'success' : 'error'}`}>
              <div className="run-output-header">
                <span className="run-status">{runOutput.status}</span>
                <span className="run-time">{runOutput.runtime_ms}ms</span>
              </div>
              {runOutput.output && <pre className="run-stdout">{runOutput.output}</pre>}
              {runOutput.error && <pre className="run-stderr">{runOutput.error}</pre>}
            </div>
          )}
        </section>
      </div>

      <div className="two-column lower">
        <section className="card">
          <h2>推荐模板</h2>
          {matchedTemplates.length === 0 && <p className="muted">暂无匹配模板，可去模板库查看全部。</p>}
          {matchedTemplates.map(t => (
            <div className="template-mini" key={t.template_id}>
              <div className="template-match-info">
                <div>
                  <strong>{t.name}</strong>
                  <span className="match-score">匹配度: {Math.round(t.match_score * 100)}%</span>
                </div>
                <p>{t.explanation}</p>
                {t.matched_tags && t.matched_tags.length > 0 && (
                  <div className="matched-tags">
                    {t.matched_tags.map(tag => <span key={tag} className="matched-tag">{tag}</span>)}
                  </div>
                )}
              </div>
              <button className="button secondary" onClick={() => insertTemplate(t)}>插入</button>
            </div>
          ))}
        </section>

        <section className="card">
          <h2>我的笔记</h2>
          <label>解题思路<textarea value={note.idea} onChange={e => setNote({...note, idea: e.target.value})} /></label>
          <label>关键点<textarea value={note.key_points} onChange={e => setNote({...note, key_points: e.target.value})} /></label>
          <label>复杂度<textarea value={note.complexity} onChange={e => setNote({...note, complexity: e.target.value})} /></label>
          <label>易错点<textarea value={note.pitfalls} onChange={e => setNote({...note, pitfalls: e.target.value})} /></label>
          <label>总结<textarea value={note.summary} onChange={e => setNote({...note, summary: e.target.value})} /></label>
          <button className="button" onClick={saveNote}>保存笔记</button>
        </section>
      </div>

      <section className="card">
        <h2>提交历史</h2>
        {submissions.length === 0 && <p className="muted">还没有提交记录。</p>}
        {submissions.map(s => (
          <details key={s.id} className="submission-item">
            <summary>{s.status} · {s.language} · {new Date(s.created_at).toLocaleString()} {s.fail_reason ? `· ${s.fail_reason}` : ''}</summary>
            <pre>{s.code}</pre>
          </details>
        ))}
      </section>
    </div>
  )
}