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

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    fetchRecommendations()
    fetchMealPlan()
  }, [])

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
