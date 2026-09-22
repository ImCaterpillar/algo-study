import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Pie, PieChart, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import { statsApi } from '../api/statsApi'
import Loading from '../components/Loading.jsx'

export default function Stats() {
  const [stats, setStats] = useState(null)
  const [masteryDist, setMasteryDist] = useState([])
  const [reviewEff, setReviewEff] = useState(null)
  const [weakness, setWeakness] = useState(null)
  const [radarData, setRadarData] = useState([])
  const [weeklyReport, setWeeklyReport] = useState(null)

  useEffect(() => {
    Promise.all([
      statsApi.summary(),
      statsApi.masteryDistribution(),
      statsApi.reviewEffectiveness(),
      statsApi.weakness(),
      statsApi.tagMasteryRadar(),
      statsApi.weeklyReport(),
    ]).then(([s, m, r, w, rd, wr]) => {
      setStats(s)
      setMasteryDist(m)
      setReviewEff(r)
      setWeakness(w)
      setRadarData(rd)
      setWeeklyReport(wr)
    }).catch(console.error)
  }, [])

  const difficultyData = useMemo(() => {
    if (!stats) return []
    return Object.entries(stats.by_difficulty).map(([difficulty, value]) => ({ difficulty, ...value }))
  }, [stats])

  const tagData = useMemo(() => {
    if (!stats) return []
    return Object.entries(stats.by_tag)
      .map(([tag, value]) => ({ tag, completion: Math.round(value.completion_rate * 100), mastery: value.average_mastery }))
      .sort((a, b) => a.completion - b.completion)
      .slice(0, 12)
  }, [stats])

  const masteryData = useMemo(() => {
    const labels = ['未开始', '看题解懂', '能复现', '能独立做', '能讲清楚', '熟练掌握']
    return masteryDist.map(d => ({ name: labels[d.level] || d.level, count: d.count }))
  }, [masteryDist])

  const reviewEffectivenessData = useMemo(() => {
    if (!reviewEff) return []
    return reviewEff.breakdown.map(b => ({ name: b.result, value: b.count, percentage: b.percentage }))
  }, [reviewEff])

  const radarChartData = useMemo(() => {
    return radarData.slice(0, 10).map(d => ({
      tag: d.tag,
      mastery: d.mastery_level,
      fullMark: 100,
    }))
  }, [radarData])

  const failReasonColors = ['#ff6b6b', '#ffa500', '#ffd700', '#90ee90', '#87ceeb', '#dda0dd', '#ff9999', '#ffcc99']

  if (!stats) return <Loading />

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>学习统计</h1>
          <p>阶段 3 新增：弱项分析、标签雷达图、周报。</p>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric-card"><span>总题数</span><strong>{stats.total_problems}</strong></div>
        <div className="metric-card"><span>已尝试</span><strong>{stats.attempted}</strong></div>
        <div className="metric-card"><span>已通过</span><strong>{stats.accepted}</strong></div>
        <div className="metric-card"><span>平均掌握度</span><strong>{stats.average_mastery}</strong></div>
      </div>

      {weeklyReport && (
        <section className="card weekly-report-card">
          <h2>📅 周报（{weeklyReport.period}）</h2>
          <div className="weekly-metrics">
            <div className="weekly-metric">
              <strong>{weeklyReport.submissions_count}</strong>
              <span>本周提交</span>
            </div>
            <div className="weekly-metric">
              <strong>{weeklyReport.unique_problems_attempted}</strong>
              <span>尝试题目</span>
            </div>
            <div className="weekly-metric">
              <strong>{weeklyReport.accepted_count}</strong>
              <span>本周通过</span>
            </div>
            <div className="weekly-metric">
              <strong>{weeklyReport.reviews_count}</strong>
              <span>本周复习</span>
            </div>
          </div>
          {weeklyReport.top_fail_reasons && Object.keys(weeklyReport.top_fail_reasons).length > 0 && (
            <div className="weekly-fail-reasons">
              <h3>主要错因（近30天）</h3>
              <div className="fail-reason-list">
                {Object.entries(weeklyReport.top_fail_reasons).map(([reason, count], idx) => (
                  <div key={reason} className="fail-reason-item">
                    <span className="fail-reason-name">{reason}</span>
                    <span className="fail-reason-count">{count}次</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="card chart-card">
        <h2>难度完成情况</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={difficultyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="difficulty" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="total" name="总题数" fill="#8884d8" />
            <Bar dataKey="accepted" name="已通过" fill="#82ca9d" />
            <Bar dataKey="need_review" name="待复盘" fill="#ffc658" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <div className="two-column">
        <section className="card chart-card">
          <h2>标签掌握度雷达图</h2>
          {radarChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarChartData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="tag" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar name="掌握度%" dataKey="mastery" stroke="#2563eb" fill="#2563eb" fillOpacity={0.5} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <p className="muted">暂无雷达图数据。继续刷题后会显示。</p>
          )}
        </section>

        <section className="card chart-card">
          <h2>掌握度分布</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={masteryData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name, percent}) => `${name}: ${(percent*100).toFixed(0)}%`}>
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="card chart-card">
        <h2>薄弱标签：完成率较低的前 12 项</h2>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={tagData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="tag" width={130} />
            <Tooltip />
            <Bar dataKey="completion" name="完成率 %" fill="#ff7300" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <div className="two-column">
        <section className="card chart-card">
          <h2>复习效果</h2>
          {reviewEff && reviewEff.total_reviews > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={reviewEffectivenessData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name, percentage}) => `${name}: ${percentage}%`}>
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="muted">暂无复习数据。继续使用复盘中心后会显示复习效果统计。</p>
          )}
        </section>

        <section className="card chart-card">
          <h2>弱项分析</h2>
          {weakness && weakness.weakest_tags.length > 0 ? (
            <div className="weakness-analysis">
              <h3>需要加强的标签</h3>
              <div className="weak-tags">
                {weakness.weakest_tags.map(tag => (
                  <span key={tag} className="weak-tag">{tag}</span>
                ))}
              </div>
              <h3>已掌握的标签</h3>
              <div className="strong-tags">
                {weakness.strongest_tags.map(tag => (
                  <span key={tag} className="strong-tag">{tag}</span>
                ))}
              </div>
            </div>
          ) : (
            <p className="muted">暂无弱项数据。继续刷题和记录后会显示。</p>
          )}
        </section>
      </div>

      <section className="card chart-card">
        <h2>错因趋势（近30天）</h2>
        {stats.fail_reason_trends && stats.fail_reason_trends.length > 0 ? (
          <div className="fail-reason-list">
            {stats.fail_reason_trends.map((item, idx) => (
              <div key={item.fail_reason} className="fail-reason-item">
                <div className="fail-reason-info">
                  <span className="fail-reason-name">{item.fail_reason}</span>
                  <span className="fail-reason-count">{item.count}次</span>
                </div>
                <div className="fail-reason-bar">
                  <div className="fail-reason-fill" style={{ width: `${item.percentage}%`, backgroundColor: failReasonColors[idx % failReasonColors.length] }}></div>
                </div>
                <span className="fail-reason-pct">{item.percentage}%</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">暂无错因数据。记录提交时选择错因后会显示趋势统计。</p>
        )}
      </section>
    </div>
  )
}