import { useTranslation } from 'react-i18next'

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="footer">
      <p className="footer-disclaimer">{t('footer.disclaimer')}</p>
      <div className="footer-links">
        <a href="#">{t('footer.privacy')}</a>
        <a href="#">{t('footer.terms')}</a>
        <a href="#">{t('footer.contact')}</a>
      </div>
      <p style={{ marginTop: '1rem', fontSize: '0.8rem', opacity: 0.6 }}>
        © 2026 NutriMatch. All rights reserved.
      </p>
    </footer>
  )
}
