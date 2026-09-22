import { useEffect, useState } from 'react'
import { templateApi } from '../api/templateApi'
import Loading from '../components/Loading.jsx'
import Badge from '../components/Badge.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'

const PAGE_SIZE = 60
const blankForm = {
  name: '',
  category: '',
  language: 'python',
  code: '',
  explanation: '',
  tags: '',
  usage_scenario: '',
}

export default function TemplateLibrary() {
  const [templates, setTemplates] = useState(null)
  const [languages, setLanguages] = useState([])
  const [categories, setCategories] = useState([])
  const [language, setLanguage] = useState('')
  const [category, setCategory] = useState('')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(blankForm)
  const [showCreate, setShowCreate] = useState(false)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([templateApi.languages(), templateApi.categories()])
      .then(([langItems, categoryItems]) => {
        setLanguages(langItems)
        setCategories(categoryItems)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    loadTemplates(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, category])

  async function loadTemplates(reset = false) {
    setError('')
    const nextOffset = reset ? 0 : offset
    if (reset) setTemplates(null)
    try {
      const page = await templateApi.list({
        language: language || undefined,
        category: category || undefined,
        limit: PAGE_SIZE,
        offset: nextOffset,
      })
      const items = page.items || []
      setTemplates(prev => reset ? items : [...(prev || []), ...items])
      setTotal(page.total || items.length)
      setHasMore(Boolean(page.has_more))
      setOffset(nextOffset + items.length)
    } catch (e) {
      setError(e.response?.data?.detail || '模板加载失败，请检查登录状态和后端服务。')
      if (reset) setTemplates([])
      setHasMore(false)
    }
  }

  const handleEdit = (template) => {
    setShowCreate(false)
    setEditing(template.id)
    setForm({
      name: template.name,
      category: template.category,
      language: template.language,
      code: template.code,
      explanation: template.explanation,
      tags: (template.tags || []).join(','),
      usage_scenario: template.usage_scenario,
    })
  }

  const handleSave = async () => {
    setError('')
    const data = {
      ...form,
      name: form.name.trim(),
      category: form.category.trim(),
      tags: form.tags.split(',').map(t => t.trim()).filter(Boolean),
    }
    if (!data.name || !data.category || !data.code.trim()) {
      setError('名称、分类和代码不能为空。')
      return
    }
    try {
      if (editing) {
        await templateApi.update(editing, data)
        setEditing(null)
      } else {
        await templateApi.create(data)
        setShowCreate(false)
      }
      setForm(blankForm)
      await loadTemplates(true)
    } catch (e) {
      setError(e.response?.data?.detail || '保存模板失败。')
    }
  }

  const handleCopy = async (id) => {
    setError('')
    try {
      await templateApi.copy(id)
      await loadTemplates(true)
    } catch (e) {
      setError(e.response?.data?.detail || '复制模板失败。')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除这个模板吗？')) return
    setError('')
    try {
      await templateApi.delete(id)
      await loadTemplates(true)
    } catch (e) {
      setError(e.response?.data?.detail || '删除模板失败。')
    }
  }

  const cancelEdit = () => {
    setEditing(null)
    setShowCreate(false)
    setForm(blankForm)
  }

  async function loadMore() {
    setLoadingMore(true)
    await loadTemplates(false)
    setLoadingMore(false)
  }

  if (!templates) return <Loading />

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>算法模板库</h1>
          <p>阶段 4：当前题目自动推荐模板、自定义模板、模板练习模式。</p>
          <p className="muted">当前筛选共 {total} 个模板，已加载 {templates?.length || 0} 个。</p>
        </div>
        <button className="button" onClick={() => { setEditing(null); setForm(blankForm); setShowCreate(true) }}>+ 新建模板</button>
      </div>

      <ErrorMessage message={error} onRetry={() => loadTemplates(true)} />

      <div className="filters card">
        <label>语言
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            <option value="">全部</option>
            {languages.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </label>
        <label>分类
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option value="">全部</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>

      {(editing || showCreate) && (
        <div className="card edit-form-card">
          <h2>{editing ? '编辑模板' : '新建模板'}</h2>
          <div className="form-row">
            <label>名称</label>
            <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="form-row">
            <label>分类</label>
            <input type="text" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} />
          </div>
          <div className="form-row">
            <label>语言</label>
            <select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}>
              <option value="python">python</option>
              <option value="javascript">javascript</option>
              <option value="java">java</option>
              <option value="cpp">cpp</option>
            </select>
          </div>
          <div className="form-row">
            <label>标签（逗号分隔）</label>
            <input type="text" value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} />
          </div>
          <div className="form-row">
            <label>说明</label>
            <textarea value={form.explanation} onChange={e => setForm({ ...form, explanation: e.target.value })} rows={3} />
          </div>
          <div className="form-row">
            <label>适用场景</label>
            <input type="text" value={form.usage_scenario} onChange={e => setForm({ ...form, usage_scenario: e.target.value })} />
          </div>
          <div className="form-row">
            <label>代码</label>
            <textarea className="code-textarea" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} rows={8} />
          </div>
          <div className="form-actions">
            <button className="button" onClick={handleSave}>保存</button>
            <button className="button secondary" onClick={cancelEdit}>取消</button>
          </div>
        </div>
      )}

      {templates.length === 0 ? (
        <div className="card empty-state">没有匹配的模板。</div>
      ) : (
        <div className="template-grid">
          {templates.map(t => (
            <div className="card template-card" key={t.id}>
              <div className="template-card-header">
                <div>
                  <h2>{t.name}</h2>
                  <p>{t.category} · {t.language}</p>
                </div>
                <div className="template-actions">
                  <Badge>{t.language}</Badge>
                  {t.is_system ? <Badge>系统</Badge> : <Badge>个人</Badge>}
                  <button className="action-btn" onClick={() => handleCopy(t.id)}>复制</button>
                  {!t.is_system && (
                    <>
                      <button className="action-btn" onClick={() => handleEdit(t)}>编辑</button>
                      <button className="action-btn delete" onClick={() => handleDelete(t.id)}>删除</button>
                    </>
                  )}
                </div>
              </div>
              <p>{t.explanation}</p>
              <p className="muted">适用：{t.usage_scenario}</p>
              {t.tags && t.tags.length > 0 && (
                <div className="template-tags">
                  {t.tags.map(tag => <span key={tag} className="template-tag">{tag}</span>)}
                </div>
              )}
              <pre className="template-code">{t.code}</pre>
            </div>
          ))}
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
