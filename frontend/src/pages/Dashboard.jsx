import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Dashboard() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    try {
      const res = await api.get('/recommendations/my')
      setRecommendations(res.data)
    } catch (err) {
      console.error('Failed to fetch recommendations')
    }
  }

  const generateNew = async () => {
    setLoading(true)
    try {
      await api.post('/recommendations/generate')
      await fetchRecommendations()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate recommendations')
    } finally {
      setLoading(false)
    }
  }

  const latestRec = recommendations[0]

  return (
    <div className="dashboard">
      <h1>{t('dashboard.title')}</h1>

      <div className="dashboard-grid">
        {/* Recommendations Panel */}
        <div className="dashboard-card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>{t('dashboard.recommendations')}</h2>
            <button className="btn btn-primary" onClick={generateNew} disabled={loading}>
              {loading ? '...' : t('dashboard.generate')}
            </button>
          </div>

          {!latestRec ? (
            <p style={{ color: 'var(--text-muted)' }}>{t('dashboard.no_recommendations')}</p>
          ) : (
            <>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="rec-score">{t('dashboard.score')}: {latestRec.score}</span>
              </div>

              {/* Reasoning */}
              {latestRec.reasoning && Object.keys(latestRec.reasoning).length > 0 && (
                <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--bg)', borderRadius: 'var(--radius-sm)' }}>
                  <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--primary)' }}>{t('dashboard.reasoning')}</h3>
                  {Object.entries(latestRec.reasoning).map(([key, value]) => (
                    <p key={key} style={{ fontSize: '0.85rem', color: 'var(--text-light)', marginBottom: '0.25rem' }}>
                      • {value}
                    </p>
                  ))}
                </div>
              )}

              {/* Supplements list */}
              <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>{t('dashboard.supplement_list')}</h3>
              {latestRec.supplements.map((supp, i) => (
                <div
                  key={i}
                  className="recommendation-item"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/supplements?category=${supp.category}&search=${encodeURIComponent(supp.name)}`)}
                >
                  <div className="rec-info">
                    <h4>{supp.name}</h4>
                    <p>{supp.brand} • {supp.category} • €{supp.price?.toFixed(2)}</p>
                  </div>
                  <span className="rec-score" title="Match-Score">{Math.round(supp.score)}%</span>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Health Data Panel */}
        <div className="dashboard-card">
          <h2>{t('dashboard.health_data')}</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Smartwatch & Fitness-App Integration
          </p>
          <button className="btn btn-secondary">{t('dashboard.connect_device')}</button>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card">
          <h2>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button className="btn btn-secondary" onClick={() => navigate('/questionnaire')}>
              {t('nav.questionnaire')}
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/supplements')}>
              {t('nav.supplements')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
