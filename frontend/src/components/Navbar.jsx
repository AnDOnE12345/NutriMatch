import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Navbar() {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const isLoggedIn = !!localStorage.getItem('token')

  const changeLanguage = (lang) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('language', lang)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/'
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="logo">
          <span className="logo-icon">🧬</span>
          NutriMatch
        </Link>

        <ul className="nav-links">
          <li>
            <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
              {t('nav.home')}
            </Link>
          </li>
          {isLoggedIn && (
            <>
              <li>
                <Link to="/questionnaire" className={location.pathname === '/questionnaire' ? 'active' : ''}>
                  {t('nav.questionnaire')}
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className={location.pathname === '/dashboard' ? 'active' : ''}>
                  {t('nav.dashboard')}
                </Link>
              </li>
            </>
          )}
          <li>
            <Link to="/supplements" className={location.pathname === '/supplements' ? 'active' : ''}>
              {t('nav.supplements')}
            </Link>
          </li>
          {!isLoggedIn ? (
            <>
              <li>
                <Link to="/login" className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
                  {t('nav.login')}
                </Link>
              </li>
              <li>
                <Link to="/register" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
                  {t('nav.register')}
                </Link>
              </li>
            </>
          ) : (
            <li>
              <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
                {t('nav.logout')}
              </button>
            </li>
          )}
          <li>
            <div className="lang-switch">
              <button
                className={`lang-btn ${i18n.language === 'de' ? 'active' : ''}`}
                onClick={() => changeLanguage('de')}
              >
                DE
              </button>
              <button
                className={`lang-btn ${i18n.language === 'en' ? 'active' : ''}`}
                onClick={() => changeLanguage('en')}
              >
                EN
              </button>
            </div>
          </li>
        </ul>
      </div>
    </nav>
  )
}
