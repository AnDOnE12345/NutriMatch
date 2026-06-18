import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import api from '../api'

export default function Supplements() {
  const { t, i18n } = useTranslation()
  const [searchParams] = useSearchParams()
  const [supplements, setSupplements] = useState([])
  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    is_vegan: searchParams.get('is_vegan') === 'true',
    is_organic: searchParams.get('is_organic') === 'true',
    max_price: searchParams.get('max_price') || '',
    search: searchParams.get('search') || '',
  })

  useEffect(() => {
    fetchSupplements()
  }, [filters])

  const fetchSupplements = async () => {
    try {
      const params = {}
      if (filters.category) params.category = filters.category
      if (filters.is_vegan) params.is_vegan = true
      if (filters.is_organic) params.is_organic = true
      if (filters.max_price) params.max_price = parseFloat(filters.max_price)
      if (filters.search) params.search = filters.search

      const res = await api.get('/supplements', { params })
      setSupplements(res.data)
    } catch (err) {
      console.error('Failed to fetch supplements')
    }
  }

  const getDescription = (supp) => {
    return i18n.language === 'de' ? supp.description_de : supp.description_en
  }

  return (
    <div className="supplements-page">
      <h1>{t('supplements.title')}</h1>

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-item">
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          >
            <option value="">{t('supplements.all')}</option>
            <option value="vitamin">{t('supplements.vitamins')}</option>
            <option value="mineral">{t('supplements.minerals')}</option>
            <option value="herbal">{t('supplements.herbal')}</option>
            <option value="omega">{t('supplements.omega')}</option>
            <option value="amino_acid">{t('supplements.amino_acids')}</option>
            <option value="probiotic">{t('supplements.probiotics')}</option>
          </select>
        </div>

        <label className="filter-toggle">
          <input
            type="checkbox"
            checked={filters.is_vegan}
            onChange={(e) => setFilters({ ...filters, is_vegan: e.target.checked })}
          />
          {t('supplements.vegan_only')}
        </label>

        <label className="filter-toggle">
          <input
            type="checkbox"
            checked={filters.is_organic}
            onChange={(e) => setFilters({ ...filters, is_organic: e.target.checked })}
          />
          {t('supplements.organic_only')}
        </label>

        <div className="filter-item">
          <input
            type="text"
            placeholder="Search..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            style={{ padding: '0.5rem 1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}
          />
        </div>
      </div>

      {/* Supplements Grid */}
      <div className="supplement-grid">
        {supplements.map((supp) => (
          <div key={supp.id} className="supplement-card">
            <div className="supplement-card-header">
              <h3>{supp.name}</h3>
              <span className="supplement-brand">{supp.brand}</span>
            </div>
            <div className="supplement-card-body">
              <div className="supplement-badges">
                {supp.is_vegan && <span className="badge badge-vegan">🌱 Vegan</span>}
                {supp.is_organic && <span className="badge badge-organic">🌿 Bio</span>}
                {supp.evidence_level && (
                  <span className="badge badge-evidence">📊 {supp.evidence_level}</span>
                )}
              </div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-light)', marginBottom: '1rem' }}>
                {getDescription(supp)}
              </p>
              <div className="supplement-price">
                €{supp.price?.toFixed(2)}
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {supp.shop_name}
              </p>
            </div>
            <div className="supplement-card-actions">
              <a
                href={supp.shop_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                style={{ flex: 1, justifyContent: 'center', fontSize: '0.85rem', textDecoration: 'none' }}
              >
                {t('supplements.buy_now')} → {supp.shop_name}
              </a>
            </div>
          </div>
        ))}

        {supplements.length === 0 && (
          <p style={{ color: 'var(--text-muted)', gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
            No supplements found matching your filters.
          </p>
        )}
      </div>
    </div>
  )
}
