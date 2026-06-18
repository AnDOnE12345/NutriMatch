import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api'

const GOALS = ['energy', 'sleep', 'immunity', 'muscle', 'weight_loss', 'skin_hair', 'digestion', 'stress', 'focus', 'joints']
const ALLERGIES = ['gluten', 'lactose', 'soy', 'nuts', 'fish', 'shellfish']

export default function Questionnaire() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    activity_level: 'moderate',
    sleep_hours: 7,
    stress_level: 'moderate',
    smoking: false,
    alcohol_frequency: 'rarely',
    diet_type: 'omnivore',
    meals_per_day: 3,
    water_intake_liters: 2,
    goals: [],
    allergies: [],
    preferred_form: 'capsule',
    budget_monthly: 50,
    food_budget_monthly: 300,
    prefer_organic: false,
    prefer_fairtrade: false,
    existing_conditions: [],
    current_medications: [],
  })

  const updateField = (field, value) => {
    setForm({ ...form, [field]: value })
  }

  const toggleArrayItem = (field, item) => {
    const arr = form[field]
    if (arr.includes(item)) {
      updateField(field, arr.filter((i) => i !== item))
    } else {
      updateField(field, [...arr, item])
    }
  }

  const handleSubmit = async () => {
    try {
      const payload = {
        ...form,
        age: form.age ? parseInt(form.age) : null,
        height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        sleep_hours: parseFloat(form.sleep_hours),
        meals_per_day: parseInt(form.meals_per_day),
        water_intake_liters: parseFloat(form.water_intake_liters),
        budget_monthly: parseFloat(form.budget_monthly),
        food_budget_monthly: parseFloat(form.food_budget_monthly),
      }
      await api.post('/questionnaire/submit', payload)
      navigate('/dashboard')
    } catch (err) {
      alert(err.response?.data?.detail || 'Error submitting questionnaire')
    }
  }

  const steps = [
    // Step 0: Basic Info
    <div className="form-section" key="basic">
      <h2>{t('questionnaire.basic_info')}</h2>
      <div className="form-group">
        <label>{t('questionnaire.age')}</label>
        <input type="number" value={form.age} onChange={(e) => updateField('age', e.target.value)} min="16" max="120" />
      </div>
      <div className="form-group">
        <label>{t('questionnaire.gender')}</label>
        <select value={form.gender} onChange={(e) => updateField('gender', e.target.value)}>
          <option value="">--</option>
          <option value="male">{t('questionnaire.male')}</option>
          <option value="female">{t('questionnaire.female')}</option>
          <option value="diverse">{t('questionnaire.diverse')}</option>
        </select>
      </div>
      <div className="form-group">
        <label>{t('questionnaire.height')}</label>
        <input type="number" value={form.height_cm} onChange={(e) => updateField('height_cm', e.target.value)} />
      </div>
      <div className="form-group">
        <label>{t('questionnaire.weight')}</label>
        <input type="number" value={form.weight_kg} onChange={(e) => updateField('weight_kg', e.target.value)} />
      </div>
    </div>,

    // Step 1: Lifestyle
    <div className="form-section" key="lifestyle">
      <h2>{t('questionnaire.lifestyle')}</h2>
      <div className="form-group">
        <label>{t('questionnaire.activity_level')}</label>
        <select value={form.activity_level} onChange={(e) => updateField('activity_level', e.target.value)}>
          <option value="sedentary">{t('questionnaire.sedentary')}</option>
          <option value="light">{t('questionnaire.light')}</option>
          <option value="moderate">{t('questionnaire.moderate')}</option>
          <option value="active">{t('questionnaire.active')}</option>
          <option value="very_active">{t('questionnaire.very_active')}</option>
        </select>
      </div>
      <div className="form-group">
        <label>{t('questionnaire.sleep_hours')}</label>
        <input type="number" value={form.sleep_hours} onChange={(e) => updateField('sleep_hours', e.target.value)} min="3" max="14" step="0.5" />
      </div>
      <div className="form-group">
        <label>{t('questionnaire.stress_level')}</label>
        <select value={form.stress_level} onChange={(e) => updateField('stress_level', e.target.value)}>
          <option value="low">{t('questionnaire.low')}</option>
          <option value="moderate">{t('questionnaire.moderate')}</option>
          <option value="high">{t('questionnaire.high')}</option>
        </select>
      </div>
    </div>,

    // Step 2: Diet
    <div className="form-section" key="diet">
      <h2>{t('questionnaire.diet')}</h2>
      <div className="form-group">
        <label>{t('questionnaire.diet_type')}</label>
        <select value={form.diet_type} onChange={(e) => updateField('diet_type', e.target.value)}>
          <option value="omnivore">{t('questionnaire.omnivore')}</option>
          <option value="vegetarian">{t('questionnaire.vegetarian')}</option>
          <option value="vegan">{t('questionnaire.vegan')}</option>
          <option value="pescatarian">{t('questionnaire.pescatarian')}</option>
          <option value="keto">{t('questionnaire.keto')}</option>
          <option value="paleo">{t('questionnaire.paleo')}</option>
        </select>
      </div>
      <div className="form-group">
        <label>{t('questionnaire.allergies')}</label>
        <div className="checkbox-group">
          {ALLERGIES.map((allergy) => (
            <label
              key={allergy}
              className={`checkbox-item ${form.allergies.includes(allergy) ? 'selected' : ''}`}
            >
              <input
                type="checkbox"
                checked={form.allergies.includes(allergy)}
                onChange={() => toggleArrayItem('allergies', allergy)}
              />
              {t(`questionnaire.allergy_${allergy}`)}
            </label>
          ))}
        </div>
      </div>
    </div>,

    // Step 3: Goals
    <div className="form-section" key="goals">
      <h2>{t('questionnaire.goals_select')}</h2>
      <div className="checkbox-group">
        {GOALS.map((goal) => (
          <label
            key={goal}
            className={`checkbox-item ${form.goals.includes(goal) ? 'selected' : ''}`}
          >
            <input
              type="checkbox"
              checked={form.goals.includes(goal)}
              onChange={() => toggleArrayItem('goals', goal)}
            />
            {t(`questionnaire.goal_${goal}`)}
          </label>
        ))}
      </div>
    </div>,

    // Step 4: Preferences
    <div className="form-section" key="prefs">
      <h2>{t('questionnaire.preferences')}</h2>
      <div className="form-group">
        <label>{t('questionnaire.preferred_form')}</label>
        <select value={form.preferred_form} onChange={(e) => updateField('preferred_form', e.target.value)}>
          <option value="capsule">{t('questionnaire.capsule')}</option>
          <option value="tablet">{t('questionnaire.tablet')}</option>
          <option value="powder">{t('questionnaire.powder')}</option>
          <option value="liquid">{t('questionnaire.liquid')}</option>
          <option value="gummy">{t('questionnaire.gummy')}</option>
        </select>
      </div>
      <div className="form-group">
        <label>{t('questionnaire.budget')}</label>
        <input type="number" value={form.budget_monthly} onChange={(e) => updateField('budget_monthly', e.target.value)} min="10" max="500" />
      </div>
      <div className="form-group">
        <label>{t('questionnaire.food_budget')}</label>
        <input type="number" value={form.food_budget_monthly} onChange={(e) => updateField('food_budget_monthly', e.target.value)} min="50" max="2000" step="50" />
      </div>
      <div className="form-group">
        <label className="checkbox-item" style={{ display: 'inline-flex' }}>
          <input type="checkbox" checked={form.prefer_organic} onChange={(e) => updateField('prefer_organic', e.target.checked)} />
          {t('questionnaire.prefer_organic')}
        </label>
      </div>
      <div className="form-group">
        <label className="checkbox-item" style={{ display: 'inline-flex' }}>
          <input type="checkbox" checked={form.prefer_fairtrade} onChange={(e) => updateField('prefer_fairtrade', e.target.checked)} />
          {t('questionnaire.prefer_fairtrade')}
        </label>
      </div>
    </div>,
  ]

  return (
    <div className="form-page">
      <h1>{t('questionnaire.title')}</h1>
      <p className="subtitle">{t('questionnaire.subtitle')}</p>

      {/* Progress indicator */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        {steps.map((_, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: '4px',
              borderRadius: '2px',
              background: i <= step ? 'var(--accent)' : 'var(--border)',
              transition: 'background 0.3s',
            }}
          />
        ))}
      </div>

      {steps[step]}

      <div className="form-nav">
        {step > 0 && (
          <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
            {t('questionnaire.back')}
          </button>
        )}
        {step < steps.length - 1 ? (
          <button className="btn btn-primary" onClick={() => setStep(step + 1)} style={{ marginLeft: 'auto' }}>
            {t('questionnaire.next')}
          </button>
        ) : (
          <button className="btn btn-accent" onClick={handleSubmit} style={{ marginLeft: 'auto' }}>
            {t('questionnaire.submit')}
          </button>
        )}
      </div>
    </div>
  )
}
