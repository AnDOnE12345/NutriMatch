import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../api'

const text = {
  de: {
    title: 'NutriGuide', subtitle: 'Dein NutriMatch Assistent', greeting: 'Hallo! Ich beantworte Fragen zu NutriMatch, Nahrungsergänzung, Einnahme und unserem Produktkatalog. Wobei kann ich dir helfen?',
    placeholder: 'Frage zu Supplements stellen…', send: 'Senden', close: 'Chat schließen', open: 'NutriGuide öffnen',
    disclaimer: 'Allgemeine Information, keine medizinische Diagnose.', cloud: 'Bei Cloud-Modellen wird deine Frage an den gewählten Anbieter gesendet.',
    unavailable: 'nicht konfiguriert', error: 'Der Assistent ist gerade nicht erreichbar. Bitte versuche es erneut.',
    suggestions: ['Was ist NutriMatch?', 'Wann sollte ich Magnesium einnehmen?', 'Welche Supplements sind für vegane Ernährung relevant?'],
  },
  en: {
    title: 'NutriGuide', subtitle: 'Your NutriMatch assistant', greeting: 'Hi! I can answer questions about NutriMatch, supplements, timing, and our product catalog. How can I help?',
    placeholder: 'Ask about supplements…', send: 'Send', close: 'Close chat', open: 'Open NutriGuide',
    disclaimer: 'General information, not a medical diagnosis.', cloud: 'With cloud models, your question is sent to the selected provider.',
    unavailable: 'not configured', error: 'The assistant is currently unavailable. Please try again.',
    suggestions: ['What is NutriMatch?', 'When should I take magnesium?', 'Which supplements are relevant for a vegan diet?'],
  },
}

const defaultProviders = [
  { id: 'local', label: 'Lokal · Ollama', configured: true },
  { id: 'gemini', label: 'Gemini', configured: false },
  { id: 'groq', label: 'LLaMA · Groq', configured: false },
]

export default function ChatAssistant() {
  const { i18n } = useTranslation()
  const language = i18n.language?.startsWith('en') ? 'en' : 'de'
  const labels = text[language]
  const [open, setOpen] = useState(false)
  const [provider, setProvider] = useState('local')
  const [providers, setProviders] = useState(defaultProviders)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem('nutriguideMessages'))
      if (Array.isArray(saved) && saved.length) return saved
    } catch { /* Start a fresh local conversation. */ }
    return [{ role: 'assistant', content: labels.greeting }]
  })
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    api.get('/chat/providers')
      .then(({ data }) => setProviders(data.providers || defaultProviders))
      .catch(() => setProviders(defaultProviders))
  }, [])

  useEffect(() => {
    sessionStorage.setItem('nutriguideMessages', JSON.stringify(messages.slice(-20)))
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (open) window.setTimeout(() => inputRef.current?.focus(), 120)
  }, [open])

  const sendMessage = async (suggestedMessage) => {
    const message = (suggestedMessage || input).trim()
    if (!message || sending) return

    const userMessage = { role: 'user', content: message }
    const history = messages.slice(-8).map(({ role, content }) => ({ role, content }))
    setMessages((current) => [...current, userMessage])
    setInput('')
    setSending(true)
    try {
      const { data } = await api.post('/chat', { message, provider, history })
      setMessages((current) => [...current, { role: 'assistant', content: data.reply, provider: data.provider }])
    } catch (error) {
      setMessages((current) => [...current, {
        role: 'assistant', error: true, content: error.response?.data?.detail || labels.error,
      }])
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={`chat-assistant ${open ? 'is-open' : ''}`}>
      {open && (
        <section className="chat-panel" aria-label={labels.title}>
          <header className="chat-header">
            <div className="chat-avatar">✦</div>
            <div><strong>{labels.title}</strong><span><i /> {labels.subtitle}</span></div>
            <button type="button" onClick={() => setOpen(false)} aria-label={labels.close}>×</button>
          </header>

          <div className="chat-provider-row">
            <label htmlFor="chat-provider">AI</label>
            <select id="chat-provider" value={provider} onChange={(event) => setProvider(event.target.value)}>
              {providers.map((item) => (
                <option key={item.id} value={item.id} disabled={!item.configured}>
                  {item.label}{item.configured ? '' : ` · ${labels.unavailable}`}
                </option>
              ))}
            </select>
            <span className={`provider-privacy ${provider === 'local' ? 'local' : 'cloud'}`}>
              {provider === 'local' ? '● Local' : '☁ Cloud'}
            </span>
          </div>

          <div className="chat-messages" ref={scrollRef} aria-live="polite">
            {messages.map((message, index) => (
              <div className={`chat-message ${message.role} ${message.error ? 'error' : ''}`} key={`${message.role}-${index}`}>
                {message.role === 'assistant' && <span className="message-avatar">✦</span>}
                <div><p>{message.content}</p>{message.provider && <small>{providers.find((item) => item.id === message.provider)?.label}</small>}</div>
              </div>
            ))}
            {sending && <div className="chat-message assistant"><span className="message-avatar">✦</span><div className="typing"><i/><i/><i/></div></div>}
          </div>

          {messages.length === 1 && (
            <div className="chat-suggestions">
              {labels.suggestions.map((suggestion) => <button type="button" key={suggestion} onClick={() => sendMessage(suggestion)}>{suggestion}</button>)}
            </div>
          )}

          <div className="chat-compose">
            <textarea ref={inputRef} rows="1" maxLength="800" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} placeholder={labels.placeholder}/>
            <button type="button" onClick={() => sendMessage()} disabled={!input.trim() || sending} aria-label={labels.send}>➤</button>
          </div>
          <footer className="chat-disclaimer"><span>ⓘ {labels.disclaimer}</span>{provider !== 'local' && <span>{labels.cloud}</span>}</footer>
        </section>
      )}

      <button className="chat-fab" type="button" onClick={() => setOpen((value) => !value)} aria-label={open ? labels.close : labels.open}>
        {open ? '×' : <><span>✦</span><i /></>}
      </button>
    </div>
  )
}
