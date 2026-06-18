import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api'

export default function Register() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/auth/register', { ...form, language: i18n.language })
      // Auto-login after registration
      const res = await api.post('/auth/login', { email: form.email, password: form.password })
      localStorage.setItem('token', res.data.access_token)
      navigate('/questionnaire')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>{t('auth.register_title')}</h1>
        {error && <p style={{ color: 'red', textAlign: 'center', marginBottom: '1rem' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('auth.full_name')}</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>{t('auth.email')}</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>{t('auth.password')}</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={6}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            {t('auth.register_btn')}
          </button>
        </form>
        <div className="auth-footer">
          {t('auth.has_account')} <Link to="/login">{t('auth.login_link')}</Link>
        </div>
      </div>
    </div>
  )
}
