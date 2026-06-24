import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api'

const copy = {
  de: {
    back: 'Zurück zum Dashboard', connected: 'Live verbunden', simulated: 'Simulierte Demodaten',
    synced: 'Zuletzt synchronisiert', justNow: 'gerade eben', today: 'Heute', steps: 'Schritte',
    sleep: 'Schlaf', resting: 'Ruhepuls', active: 'Aktivitätsminuten', calories: 'Aktive Kalorien',
    livePulse: 'Live-Herzfrequenz', lastMinute: 'Letzte 60 Sekunden', history: 'Deine letzten 14 Tage',
    dailySteps: 'Schritte pro Tag', sleepDuration: 'Schlafdauer', restingTrend: 'Ruhepuls',
    activeTime: 'Aktive Minuten', average: 'Ø 14 Tage', hours: 'Std.', minutes: 'Min.',
    insightEyebrow: 'NutriMatch Insight', insightTitle: 'Deine Gesundheitsdaten sind bereit', insight: 'Die 14-Tage-Auswertung für Schlaf, Bewegung und Erholung findest du jetzt ganz oben in deinem Dashboard.',
    update: 'Empfehlungen mit Gesundheitsdaten aktualisieren', updating: 'Wird aktualisiert…', updated: 'Empfehlungen wurden mit den Wearable-Daten aktualisiert.', dashboard: 'Zum Dashboard',
    loading: 'Gesundheitsdaten werden synchronisiert…', expired: 'Diese NFC-Synchronisierung ist abgelaufen. Bitte berühre den Tag erneut.',
    quality: 'Schlafqualität', battery: 'Akku', via: 'Verbunden über NFC', bpm: 'BPM', kcal: 'kcal',
  },
  en: {
    back: 'Back to dashboard', connected: 'Connected live', simulated: 'Simulated demo data',
    synced: 'Last synced', justNow: 'just now', today: 'Today', steps: 'Steps', sleep: 'Sleep',
    resting: 'Resting heart rate', active: 'Active minutes', calories: 'Active calories',
    livePulse: 'Live heart rate', lastMinute: 'Last 60 seconds', history: 'Your last 14 days',
    dailySteps: 'Daily steps', sleepDuration: 'Sleep duration', restingTrend: 'Resting heart rate',
    activeTime: 'Active minutes', average: '14-day avg.', hours: 'h', minutes: 'min',
    insightEyebrow: 'NutriMatch Insight', insightTitle: 'Your health data is ready', insight: 'Your 14-day sleep, movement, and recovery analysis is now available at the top of your dashboard.',
    update: 'Update recommendations with health data', updating: 'Updating…', updated: 'Recommendations were updated with wearable data.', dashboard: 'Go to dashboard',
    loading: 'Synchronizing health data…', expired: 'This NFC sync has expired. Please tap the tag again.',
    quality: 'Sleep quality', battery: 'Battery', via: 'Connected via NFC', bpm: 'BPM', kcal: 'kcal',
  },
}

function formatHours(value, locale, labels) {
  const hours = Math.floor(value)
  const minutes = Math.round((value - hours) * 60)
  return locale === 'de' ? `${hours} Std. ${minutes} Min.` : `${hours} h ${minutes} min`
}

function BarChart({ data, valueKey, color = '#52b788', max, formatValue, locale }) {
  const chartMax = max || Math.max(...data.map((item) => item[valueKey])) * 1.08
  return (
    <div className="watch-bars" aria-label={valueKey}>
      {data.map((item, index) => {
        const date = new Date(`${item.date}T12:00:00`)
        const label = date.toLocaleDateString(locale, { weekday: 'short' }).replace('.', '')
        const title = `${date.toLocaleDateString(locale)}: ${formatValue(item[valueKey])}`
        return (
          <div className="watch-bar-column" key={item.date} title={title}>
            <span className="watch-bar-value">{index === data.length - 1 ? formatValue(item[valueKey]) : ''}</span>
            <div className="watch-bar-track">
              <div className="watch-bar-fill" style={{ height: `${Math.max(5, item[valueKey] / chartMax * 100)}%`, background: color }} />
            </div>
            <span className={index === data.length - 1 ? 'is-today' : ''}>{label}</span>
          </div>
        )
      })}
    </div>
  )
}

function LineChart({ data, valueKey, color = '#ef6f6c', formatValue, locale }) {
  const values = data.map((item) => item[valueKey])
  const low = Math.min(...values) - 3
  const high = Math.max(...values) + 3
  const points = values.map((value, index) => {
    const x = 4 + index * (92 / Math.max(1, values.length - 1))
    const y = 88 - ((value - low) / Math.max(1, high - low)) * 72
    return `${x},${y}`
  }).join(' ')
  return (
    <div className="watch-line-wrap">
      <svg className="watch-line-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={valueKey}>
        <defs><linearGradient id={`fill-${valueKey}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={color} stopOpacity=".25"/><stop offset="1" stopColor={color} stopOpacity="0"/></linearGradient></defs>
        <polyline points={`4,92 ${points} 96,92`} fill={`url(#fill-${valueKey})`} stroke="none" />
        <polyline points={points} fill="none" stroke={color} strokeWidth="2.2" vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="watch-line-labels">
        <span>{new Date(`${data[0].date}T12:00:00`).toLocaleDateString(locale, { day: '2-digit', month: '2-digit' })}</span>
        <strong>{formatValue(values.at(-1))}</strong>
        <span>{new Date(`${data.at(-1).date}T12:00:00`).toLocaleDateString(locale, { day: '2-digit', month: '2-digit' })}</span>
      </div>
    </div>
  )
}

function LivePulse({ values, heartRate, labels }) {
  const points = values.map((value, index) => {
    const x = index * (100 / Math.max(1, values.length - 1))
    const y = 50 - (value - 72) * 3.2
    return `${x},${Math.max(7, Math.min(93, y))}`
  }).join(' ')
  return (
    <section className="live-pulse-card">
      <div className="live-pulse-copy">
        <span className="eyebrow">{labels.livePulse}</span>
        <div><span className="pulse-heart">♥</span><strong>{heartRate}</strong><span>{labels.bpm}</span></div>
        <small><i /> {labels.connected} · {labels.lastMinute}</small>
      </div>
      <svg className="live-pulse-chart" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={labels.livePulse}>
        <polyline points={points} fill="none" stroke="#ff8a80" strokeWidth="2.4" vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </section>
  )
}

export default function WearableDashboard() {
  const { eventId } = useParams()
  const navigate = useNavigate()
  const { i18n } = useTranslation()
  const language = i18n.language?.startsWith('en') ? 'en' : 'de'
  const labels = copy[language]
  const locale = language === 'de' ? 'de-DE' : 'en-US'
  const [dataset, setDataset] = useState(null)
  const [error, setError] = useState('')
  const [heartRate, setHeartRate] = useState(72)
  const [pulseValues, setPulseValues] = useState(() => Array.from({ length: 36 }, (_, i) => 71 + Math.sin(i / 3) * 1.4))
  const [updating, setUpdating] = useState(false)
  const [updated, setUpdated] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    setDataset(null)
    setUpdated(false)
    let active = true
    const request = eventId === 'latest'
      ? api.get('/health/nfc/device/latest')
      : api.post(`/health/nfc/events/${eventId}/connect`)
    request
      .then(({ data }) => {
        if (!active) return
        setDataset(data)
        setHeartRate(data.live_heart_rate)
        localStorage.setItem('nfcDevice', JSON.stringify(data.device))
      })
      .catch(() => { if (active) setError(labels.expired) })
    return () => { active = false }
  }, [eventId, navigate, labels.expired])

  useEffect(() => {
    if (!localStorage.getItem('token')) return undefined
    let stopped = false
    const checkForAnotherTap = async () => {
      try {
        const after = eventId === 'latest' ? localStorage.getItem('lastNfcEvent') : eventId
        const response = await api.get('/health/nfc/events/latest', { params: { after } })
        const nextEvent = response.data?.event
        if (!stopped && nextEvent) {
          localStorage.setItem('lastNfcEvent', nextEvent.id)
          navigate(`/health/watch/${nextEvent.id}`, { replace: true })
        }
      } catch {
        // Live resync remains optional when the network is temporarily unavailable.
      }
    }
    const interval = window.setInterval(checkForAnotherTap, 1000)
    return () => {
      stopped = true
      window.clearInterval(interval)
    }
  }, [eventId, navigate])

  useEffect(() => {
    if (!dataset) return undefined
    const timer = window.setInterval(() => {
      setHeartRate((previous) => {
        const pullToBaseline = (72 - previous) * 0.22
        const next = Math.round(Math.max(64, Math.min(82, previous + pullToBaseline + (Math.random() - 0.5) * 3)))
        setPulseValues((values) => [...values.slice(-59), next])
        return next
      })
    }, 1000)
    return () => window.clearInterval(timer)
  }, [dataset])

  const handleRecommendationUpdate = async () => {
    setUpdating(true)
    setUpdated(false)
    try {
      await api.post('/recommendations/generate')
      setUpdated(true)
    } catch {
      setUpdated(false)
    } finally {
      setUpdating(false)
    }
  }

  const averages = useMemo(() => dataset?.averages || {}, [dataset])

  if (error) return <div className="watch-state"><div className="watch-state-icon">!</div><h1>{error}</h1><button className="btn btn-primary" onClick={() => navigate('/dashboard')}>{labels.back}</button></div>
  if (!dataset) return <div className="watch-state"><div className="watch-sync-spinner"/><h1>{labels.loading}</h1><p>NM-WATCH-01 · NFC</p></div>

  const { device, today, history } = dataset
  const statCards = [
    { icon: '↟', value: today.steps.toLocaleString(locale), label: labels.steps, tone: 'green' },
    { icon: '☾', value: formatHours(today.sleep_hours, locale, labels), label: labels.sleep, tone: 'violet', extra: `${today.sleep_quality}% ${labels.quality}` },
    { icon: '♥', value: `${today.resting_heart_rate} ${labels.bpm.toLowerCase()}`, label: labels.resting, tone: 'red' },
    { icon: '⚡', value: `${today.active_minutes} ${labels.minutes}`, label: labels.active, tone: 'orange' },
  ]

  return (
    <div className="watch-page">
      <button className="watch-back" onClick={() => navigate('/dashboard')}>← {labels.back}</button>
      <header className="watch-device-header">
        <div className="watch-device-icon">⌚</div>
        <div className="watch-device-title"><div className="watch-title-row"><h1>{device.name}</h1><span className="live-chip"><i /> {labels.connected}</span></div><p>{device.id} · {labels.via} · {labels.synced} {labels.justNow}</p></div>
        <div className="watch-device-meta"><span>▰ {device.battery}% {labels.battery}</span><span className="demo-chip">{labels.simulated}</span></div>
      </header>

      <div className="watch-section-heading"><div><span className="eyebrow">{labels.today}</span><h2>{new Date(`${today.date}T12:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' })}</h2></div><span>{today.active_calories} {labels.kcal} · {labels.calories}</span></div>
      <section className="watch-stat-grid">{statCards.map((card) => <article className={`watch-stat-card ${card.tone}`} key={card.label}><span className="watch-stat-icon">{card.icon}</span><div><strong>{card.value}</strong><span>{card.label}</span>{card.extra && <small>{card.extra}</small>}</div></article>)}</section>

      <LivePulse values={pulseValues} heartRate={heartRate} labels={labels} />

      <div className="watch-section-heading history-heading"><div><span className="eyebrow">{labels.history}</span><h2>{labels.history}</h2></div></div>
      <section className="watch-chart-grid">
        <article className="watch-chart-card"><div className="chart-card-head"><div><h3>{labels.dailySteps}</h3><span>{labels.average}: {averages.steps?.toLocaleString(locale)}</span></div><span className="chart-icon green">↟</span></div><BarChart data={history} valueKey="steps" color="#40916c" formatValue={(v) => v.toLocaleString(locale)} locale={locale}/></article>
        <article className="watch-chart-card"><div className="chart-card-head"><div><h3>{labels.sleepDuration}</h3><span>{labels.average}: {formatHours(averages.sleep_hours, locale, labels)}</span></div><span className="chart-icon violet">☾</span></div><BarChart data={history} valueKey="sleep_hours" color="#7b6fc4" max={9} formatValue={(v) => `${v.toFixed(1)} h`} locale={locale}/></article>
        <article className="watch-chart-card"><div className="chart-card-head"><div><h3>{labels.restingTrend}</h3><span>{labels.average}: {averages.resting_heart_rate} {labels.bpm}</span></div><span className="chart-icon red">♥</span></div><LineChart data={history} valueKey="resting_heart_rate" formatValue={(v) => `${v} ${labels.bpm}`} locale={locale}/></article>
        <article className="watch-chart-card"><div className="chart-card-head"><div><h3>{labels.activeTime}</h3><span>{labels.average}: {averages.active_minutes} {labels.minutes}</span></div><span className="chart-icon orange">⚡</span></div><BarChart data={history} valueKey="active_minutes" color="#e79a42" formatValue={(v) => `${v} min`} locale={locale}/></article>
      </section>

      <section className="watch-insight"><div className="insight-icon">✦</div><div><span className="eyebrow">{labels.insightEyebrow}</span><h2>{labels.insightTitle}</h2><p>{labels.insight}</p>{updated && <p className="update-success">✓ {labels.updated}</p>}</div>{updated ? <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>{labels.dashboard}</button> : <button className="btn btn-primary" disabled={updating} onClick={handleRecommendationUpdate}>{updating ? labels.updating : labels.update}</button>}</section>
    </div>
  )
}
