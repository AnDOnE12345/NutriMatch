import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Dashboard() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [mealPlan, setMealPlan] = useState(null)
  const [healthAnalysis, setHealthAnalysis] = useState(null)
  const [nfcWaiting, setNfcWaiting] = useState(false)
  const [nfcDevice] = useState(() => {
    try { return JSON.parse(localStorage.getItem('nfcDevice')) } catch { return null }
  })

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    fetchRecommendations()
    fetchMealPlan()
    fetchHealthAnalysis()
  }, [])

  useEffect(() => {
    if (!localStorage.getItem('token')) return undefined
    let stopped = false

    const checkForNfcTap = async () => {
      try {
        const after = localStorage.getItem('lastNfcEvent') || undefined
        const res = await api.get('/health/nfc/events/latest', { params: { after } })
        const event = res.data?.event
        if (!stopped && event) {
          localStorage.setItem('lastNfcEvent', event.id)
          navigate(`/health/watch/${event.id}`)
        }
      } catch {
        // NFC is optional; keep the rest of the dashboard quiet if it is unavailable.
      }
    }

    checkForNfcTap()
    const interval = window.setInterval(checkForNfcTap, 1000)
    return () => {
      stopped = true
      window.clearInterval(interval)
    }
  }, [navigate])

  const fetchRecommendations = async () => {
    try {
      const res = await api.get('/recommendations/my')
      setRecommendations(res.data)
    } catch (err) {
      console.error('Failed to fetch recommendations')
    }
  }

  const fetchMealPlan = async () => {
    try {
      const res = await api.get('/meals/plan')
      setMealPlan(res.data)
    } catch (err) {
      console.error('Failed to fetch meal plan')
    }
  }

  const fetchHealthAnalysis = async () => {
    try {
      const res = await api.get('/health/data')
      const days = res.data
        .filter((entry) => entry.source === 'nfc_demo_watch' && entry.data_type === 'wearable_daily_summary')
        .map((entry) => entry.value)
        .filter(Boolean)
        .sort((a, b) => a.date.localeCompare(b.date))
        .slice(-14)

      if (days.length < 7) {
        setHealthAnalysis(null)
        return
      }

      const average = (items, key) => items.reduce((sum, item) => sum + Number(item[key] || 0), 0) / items.length
      const avgSleep = average(days, 'sleep_hours')
      const avgSteps = Math.round(average(days, 'steps'))
      const avgActive = Math.round(average(days, 'active_minutes'))
      const avgResting = Math.round(average(days, 'resting_heart_rate'))
      const recentWeek = days.slice(-7)
      const previousWeek = days.slice(-14, -7)
      const restingDelta = average(recentWeek, 'resting_heart_rate') - average(previousWeek, 'resting_heart_rate')

      setHealthAnalysis({ avgSleep, avgSteps, avgActive, avgResting, restingDelta, days: days.length })
    } catch {
      setHealthAnalysis(null)
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

  // Build unique top picks — best product per category, no duplicates
  const topPicks = (() => {
    if (!latestRec?.supplements?.length) return []
    const seen = new Map()
    for (const supp of [...latestRec.supplements].sort((a, b) => b.score - a.score)) {
      if (!seen.has(supp.category)) {
        seen.set(supp.category, supp)
      }
    }
    return [...seen.values()]
  })()

  const lang = i18n.language || 'de'

  const formatDate = (dateStr) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString(lang === 'de' ? 'de-DE' : 'en-US', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    })
  }

  const getMealPlanCalories = () => {
    if (!mealPlan) return null
    if (typeof mealPlan.total_calories === 'number') return mealPlan.total_calories

    return ['breakfast', 'lunch', 'dinner'].reduce((sum, key) => (
      sum + (mealPlan.meals?.[key]?.calories || 0)
    ), 0)
  }

  const getCalorieGapText = () => {
    if (!mealPlan?.tdee) return null
    const total = getMealPlanCalories()
    if (!total) return null

    const gap = total - mealPlan.tdee
    const percent = mealPlan.calorie_coverage_percent || Math.round(total / mealPlan.tdee * 100)

    if (Math.abs(gap) < 100) {
      return t('dashboard.calorie_gap_ok', { percent })
    }

    if (gap < 0) {
      return t('dashboard.calorie_gap_low', { percent, value: Math.abs(gap) })
    }

    return t('dashboard.calorie_gap_high', { percent, value: gap })
  }

  const formatNumber = (value) => (
    new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-US', {
      maximumFractionDigits: 1
    }).format(value)
  )

  const formatSleepDuration = (value) => {
    const hours = Math.floor(value)
    const minutes = Math.round((value - hours) * 60)
    return lang === 'de' ? `${hours} Std. ${minutes} Min.` : `${hours} h ${minutes} min`
  }

  const getHealthInsights = () => {
    if (!healthAnalysis) return []
    const { avgSleep, avgSteps, avgActive, avgResting, restingDelta } = healthAnalysis
    const weeklyActive = avgActive * 7
    const extraMinutes = Math.max(10, Math.ceil((150 - weeklyActive) / 35) * 5)

    const sleepInsight = avgSleep < 7
      ? {
          icon: '☾', tone: 'attention', title: lang === 'de' ? 'Schlaf verbessern' : 'Improve sleep',
          metric: `Ø ${formatSleepDuration(avgSleep)}`,
          text: lang === 'de'
            ? `Du schläfst im Durchschnitt weniger als 7 Stunden. Versuche, deine Schlafdauer schrittweise um ${Math.min(60, Math.max(15, Math.round((7 - avgSleep) * 60 / 15) * 15))} Minuten zu erhöhen.`
            : `Your average is below 7 hours. Try gradually adding ${Math.min(60, Math.max(15, Math.round((7 - avgSleep) * 60 / 15) * 15))} minutes of sleep.`,
        }
      : {
          icon: '☾', tone: 'positive', title: lang === 'de' ? 'Erholsamer Schlaf' : 'Restorative sleep',
          metric: `Ø ${formatSleepDuration(avgSleep)}`,
          text: lang === 'de' ? 'Deine durchschnittliche Schlafdauer liegt in einem guten Bereich. Behalte deinen regelmäßigen Rhythmus bei.' : 'Your average sleep duration is in a good range. Keep your schedule consistent.',
        }

    const activityInsight = weeklyActive < 150
      ? {
          icon: '↟', tone: 'attention', title: lang === 'de' ? 'Mehr Bewegung im Alltag' : 'Move more during the day',
          metric: `Ø ${avgSteps.toLocaleString(lang === 'de' ? 'de-DE' : 'en-US')} ${lang === 'de' ? 'Schritte' : 'steps'}`,
          text: lang === 'de' ? `Im Schnitt sammelst du ${avgActive} aktive Minuten pro Tag. Etwa ${extraMinutes} zusätzliche Minuten Bewegung täglich wären ein realistischer nächster Schritt.` : `You average ${avgActive} active minutes per day. About ${extraMinutes} extra minutes of daily movement is a realistic next step.`,
        }
      : {
          icon: '↟', tone: 'positive', title: lang === 'de' ? 'Aktivitätsziel erreicht' : 'Activity target reached',
          metric: `Ø ${avgSteps.toLocaleString(lang === 'de' ? 'de-DE' : 'en-US')} ${lang === 'de' ? 'Schritte' : 'steps'}`,
          text: lang === 'de' ? `Mit etwa ${weeklyActive} aktiven Minuten pro Woche erreichst du ein solides Aktivitätsniveau. Bleib möglichst regelmäßig in Bewegung.` : `At about ${weeklyActive} active minutes per week, you maintain a solid activity level. Keep it consistent.`,
        }

    let recoveryText
    let recoveryTone = 'stable'
    let recoveryTitle = lang === 'de' ? 'Stabile Erholung' : 'Stable recovery'
    if (restingDelta > 3) {
      recoveryTone = 'attention'
      recoveryTitle = lang === 'de' ? 'Erholung beobachten' : 'Watch your recovery'
      recoveryText = lang === 'de' ? `Dein Ruhepuls lag in den letzten 7 Tagen etwa ${Math.round(restingDelta)} BPM über der Vorwoche. Plane etwas mehr Erholung ein und beobachte den Trend.` : `Your resting heart rate was about ${Math.round(restingDelta)} BPM higher than the previous week. Allow more recovery and watch the trend.`
    } else if (restingDelta < -2) {
      recoveryTone = 'positive'
      recoveryTitle = lang === 'de' ? 'Positive Erholungstendenz' : 'Positive recovery trend'
      recoveryText = lang === 'de' ? `Dein durchschnittlicher Ruhepuls ist gegenüber der Vorwoche um ${Math.abs(Math.round(restingDelta))} BPM gesunken.` : `Your average resting heart rate decreased by ${Math.abs(Math.round(restingDelta))} BPM compared with the previous week.`
    } else {
      recoveryText = lang === 'de' ? 'Dein Ruhepuls blieb über die letzten zwei Wochen stabil. Es wurden keine auffälligen Veränderungen erkannt.' : 'Your resting heart rate remained stable over the last two weeks. No notable changes were detected.'
    }

    return [sleepInsight, activityInsight, {
      icon: '♥', tone: recoveryTone, title: recoveryTitle, metric: `Ø ${avgResting} BPM`, text: recoveryText,
    }]
  }

  const formatNutrientAmount = (info) => (
    `${formatNumber(info.actual)} ${info.unit}`
  )

  const getMealIngredients = (meal) => {
    if (meal.ingredient_details?.length) {
      return meal.ingredient_details.map((ingredient) => ({
        name: lang === 'de' ? ingredient.name_de : ingredient.name_en,
        amount: ingredient.amount,
        unit: ingredient.unit === 'Stk' && lang !== 'de' ? 'pcs' : ingredient.unit,
      }))
    }

    const names = lang === 'de'
      ? (meal.ingredients_de || meal.ingredients || [])
      : (meal.ingredients_en || meal.ingredients || [])

    return names.map((name) => ({ name }))
  }

  const getCalorieFormulaText = () => {
    const estimate = mealPlan?.calorie_estimate
    if (!estimate) return null

    const adjustment = estimate.goal_adjustment > 0
      ? `+${estimate.goal_adjustment}`
      : `${estimate.goal_adjustment}`

    return t('dashboard.calorie_formula', {
      bmr: estimate.bmr,
      multiplier: estimate.activity_multiplier,
      activity: lang === 'de' ? estimate.activity_description_de : estimate.activity_description_en,
      maintenance: estimate.maintenance_calories,
      adjustment,
    })
  }

  const MealCard = ({ meal, title, icon }) => {
    if (!meal || !meal.name) return null
    const coverage = meal.nutrient_coverage || {}
    const topNutrients = Object.entries(coverage)
      .sort((a, b) => b[1].percent - a[1].percent)
      .slice(0, 4)

    return (
      <div className="meal-card">
        <div className="meal-card-header">
          <span className="meal-icon">{icon}</span>
          <h4>{title}</h4>
          <span className="meal-cal">{meal.calories || meal.target_cal} kcal</span>
        </div>
        {meal.image_url && (
          <div className="meal-image">
            <img
              src={meal.image_url}
              alt={meal.name}
              onError={(event) => {
                event.currentTarget.closest('.meal-image')?.classList.add('is-hidden')
              }}
            />
          </div>
        )}
        <h5 className="meal-name">{lang === 'de' ? (meal.name_de || meal.name) : (meal.name_en || meal.name)}</h5>
        {getMealIngredients(meal).length > 0 && (
          <div className="meal-ingredients">
            <span className="meal-section-label">{t('dashboard.ingredients')}</span>
            <span className="meal-ingredient-note">{t('dashboard.ingredients_note')}</span>
            <div className="meal-ingredient-list">
              {getMealIngredients(meal).map((ingredient) => (
                <span className="meal-ingredient-chip" key={ingredient.name}>
                  <span>{ingredient.name}</span>
                  {ingredient.amount && (
                    <strong>{formatNumber(ingredient.amount)} {ingredient.unit}</strong>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}
        {meal.serving_factor && Math.abs(meal.serving_factor - 1) > 0.05 && (
          <p className="meal-serving">
            {t('dashboard.serving_factor', { value: formatNumber(meal.serving_factor) })}
          </p>
        )}
        <p className="meal-macros">
          {t('dashboard.macros', {
            protein: formatNumber(meal.protein || 0),
            carbs: formatNumber(meal.carbs || 0),
            fat: formatNumber(meal.fat || 0),
          })}
        </p>
        {topNutrients.length > 0 && (
          <div className="meal-nutrients">
            {topNutrients.map(([key, info]) => (
              <div key={key} className="meal-nutrient-bar">
                <span className="nutrient-label">{lang === 'de' ? info.label_de : info.label_en}</span>
                <div className="nutrient-bar-track">
                  <div className="nutrient-bar-fill" style={{ width: `${info.percent}%` }} />
                </div>
                <span
                  className="nutrient-pct"
                  title={t('dashboard.nutrient_target', { percent: info.raw_percent || info.percent })}
                >
                  {formatNutrientAmount(info)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="dashboard">
      <h1>{t('dashboard.title')}</h1>

      {healthAnalysis && (
        <section className="health-analysis">
          <div className="health-analysis-header">
            <div>
              <span className="eyebrow">NUTRIMATCH INSIGHT</span>
              <h2>{lang === 'de' ? 'Deine Gesundheitsanalyse' : 'Your health analysis'}</h2>
              <p>{lang === 'de' ? `Auswertung deiner letzten ${healthAnalysis.days} Tage mit der NutriMatch Demo Watch.` : `Analysis of your last ${healthAnalysis.days} days with the NutriMatch Demo Watch.`}</p>
            </div>
            <span className="analysis-demo-badge">{lang === 'de' ? 'Simulierte Demodaten' : 'Simulated demo data'}</span>
          </div>
          <div className="health-insight-grid">
            {getHealthInsights().map((insight) => (
              <article className={`health-insight-card ${insight.tone}`} key={insight.title}>
                <span className="health-insight-icon">{insight.icon}</span>
                <div><span className="insight-status-dot" /><h3>{insight.title}</h3></div>
                <strong>{insight.metric}</strong>
                <p>{insight.text}</p>
              </article>
            ))}
          </div>
          <p className="health-analysis-note">{lang === 'de' ? 'Hinweis: Diese Wellness-Auswertung ersetzt keine medizinische Beratung oder Diagnose.' : 'Note: This wellness analysis does not replace medical advice or diagnosis.'}</p>
        </section>
      )}

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

              {/* MEAL PLAN SECTION */}
              {mealPlan && (
                <div className="meal-plan-section">
                  <div className="meal-plan-header">
                    <div>
                      <h3>🍽️ {t('dashboard.meal_plan_title')}</h3>
                      <p className="meal-plan-date">{formatDate(mealPlan.date)}</p>
                    </div>
                    <div className="meal-plan-calories">
                      <span className="cal-number">{getMealPlanCalories()}</span>
                      <span className="cal-label">{t('dashboard.menu_calories')}</span>
                      <span className="cal-target">
                        {t('dashboard.calorie_target', { value: mealPlan.tdee })}
                      </span>
                    </div>
                  </div>
                  {getCalorieGapText() && (
                    <p className="meal-calorie-note">{getCalorieGapText()}</p>
                  )}
                  {getCalorieFormulaText() && (
                    <p className="meal-calorie-formula">{getCalorieFormulaText()}</p>
                  )}

                  <div className="meal-cards-grid">
                    <MealCard meal={mealPlan.meals?.breakfast} title={t('dashboard.breakfast')} icon="🌅" />
                    <MealCard meal={mealPlan.meals?.lunch} title={t('dashboard.lunch')} icon="☀️" />
                    <MealCard meal={mealPlan.meals?.dinner} title={t('dashboard.dinner')} icon="🌙" />
                  </div>

                  {/* Daily Summary */}
                  {mealPlan.daily_nutrient_coverage && (
                    <div className="meal-daily-summary">
                      <h4>{t('dashboard.daily_coverage')}</h4>
                      <div className="daily-nutrients-grid">
                        {Object.entries(mealPlan.daily_nutrient_coverage).map(([key, info]) => (
                          <div key={key} className={`daily-nutrient-item ${info.percent < 60 ? 'deficient' : info.percent >= 90 ? 'good' : ''}`}>
                            <span className="dn-label">{lang === 'de' ? info.label_de : info.label_en}</span>
                            <div className="dn-bar-track">
                              <div className="dn-bar-fill" style={{ width: `${Math.min(100, info.percent)}%` }} />
                            </div>
                            <span className="dn-pct">{info.percent}%</span>
                          </div>
                        ))}
                      </div>
                      {mealPlan.deficiencies?.length > 0 && (
                        <div className="meal-deficiency-note">
                          <p>⚠️ {t('dashboard.deficiency_hint')}</p>
                          <span className="deficiency-list">
                            {mealPlan.deficiencies.map(d => lang === 'de' ? d.label_de : d.label_en).join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* TOP PICKS — Shopping List */}
              {topPicks.length > 0 && (
                <div className="shopping-list">
                  <div className="shopping-list-header">
                    <span className="shopping-list-icon">🛒</span>
                    <h3>{t('dashboard.shopping_list')}</h3>
                  </div>
                  <p className="shopping-list-subtitle">{t('dashboard.shopping_list_hint')}</p>
                  <div className="shopping-list-items">
                    {topPicks.map((supp, i) => (
                      <div
                        key={i}
                        className="shopping-list-item"
                        onClick={() => navigate(`/supplements?category=${supp.category}&search=${encodeURIComponent(supp.name)}`)}
                      >
                        <div className="shopping-item-info">
                          <h4>{supp.name}</h4>
                          <p>{supp.brand} • €{supp.price?.toFixed(2)}</p>
                        </div>
                        <div className="shopping-item-right">
                          <span className="shopping-item-score">{Math.round(supp.score)}%</span>
                          <span className="shopping-item-arrow">→</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* All Supplements list */}
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
          {nfcDevice && (
            <div className="dashboard-device-status">
              <button
                className="device-status-icon"
                type="button"
                title={lang === 'de' ? 'Gesundheitsdaten öffnen' : 'Open health data'}
                aria-label={lang === 'de' ? 'Gesundheitsdaten öffnen' : 'Open health data'}
                onClick={() => navigate('/health/watch/latest')}
              >⌚</button>
              <div><strong>{nfcDevice.name}</strong><small><i /> NFC verbunden · Akku {nfcDevice.battery}%</small></div>
            </div>
          )}
          {nfcWaiting && (
            <div className="nfc-waiting-message">
              <span className="nfc-rings">)))</span>
              <div><strong>Bereit für NFC</strong><small>Halte dein Smartphone an den NutriMatch Tag.</small></div>
            </div>
          )}
          <button className="btn btn-secondary" onClick={() => setNfcWaiting((value) => !value)}>
            {nfcWaiting ? 'Warten beenden' : t('dashboard.connect_device')}
          </button>
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
