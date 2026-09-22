import { Link } from 'react-router-dom'
import Badge from './Badge.jsx'

export default function ProblemCard({ problem }) {
  const progress = problem.progress || {}
  return (
    <Link to={`/problems/${problem.id}`} className="problem-card">
      <div className="problem-card-header">
        <div>
          <div className="problem-title">{problem.recommended_order}. {problem.title_cn || problem.title}</div>
          <div className="problem-subtitle">{problem.title}</div>
        </div>
        <Badge type={problem.difficulty.toLowerCase()}>{problem.difficulty}</Badge>
      </div>
      <div className="tag-row">
        {(problem.tags || []).slice(0, 4).map(tag => <Badge key={tag}>{tag}</Badge>)}
      </div>
      <div className="progress-line">
        <span>状态：{progress.status || 'Not Started'}</span>
        <span>掌握度：{progress.mastery_level ?? 0}/5</span>
        <span>尝试：{progress.attempts ?? 0}</span>
      </div>
    </Link>
  )
}
