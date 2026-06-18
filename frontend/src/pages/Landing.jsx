import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Landing() {
  const { t } = useTranslation()

  return (
    <>
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-inner">
          <h1>{t('hero.title')}</h1>
          <p className="subtitle">{t('hero.subtitle')}</p>
          <p className="description">{t('hero.description')}</p>
          <div className="hero-buttons">
            <Link to="/register" className="btn btn-primary">
              {t('hero.cta')}
            </Link>
            <a href="#features" className="btn btn-secondary">
              {t('hero.cta_secondary')}
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features" id="features">
        <h2>{t('features.title')}</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>{t('features.personalized.title')}</h3>
            <p>{t('features.personalized.description')}</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔄</div>
            <h3>{t('features.cross_brand.title')}</h3>
            <p>{t('features.cross_brand.description')}</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔬</div>
            <h3>{t('features.transparent.title')}</h3>
            <p>{t('features.transparent.description')}</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>{t('features.adaptive.title')}</h3>
            <p>{t('features.adaptive.description')}</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="how-it-works">
        <div className="how-it-works-inner">
          <h2>{t('how_it_works.title')}</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>{t('how_it_works.step1.title')}</h3>
                <p>{t('how_it_works.step1.description')}</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>{t('how_it_works.step2.title')}</h3>
                <p>{t('how_it_works.step2.description')}</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>{t('how_it_works.step3.title')}</h3>
                <p>{t('how_it_works.step3.description')}</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>{t('how_it_works.step4.title')}</h3>
                <p>{t('how_it_works.step4.description')}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
