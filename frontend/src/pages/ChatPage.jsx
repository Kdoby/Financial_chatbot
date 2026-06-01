import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API } from '../api'
import { motion, AnimatePresence } from 'framer-motion'
import ChatMessage from '../components/ChatMessage'
import ConsultPanel from '../components/ConsultPanel'
import styles from './ChatPage.module.css'

export default function ChatPage() {
  const [messages, setMessages]     = useState([])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [consultSession, setConsult] = useState(null) // { sessionId, question, ... }
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)
  const navigate  = useNavigate()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage() {
    const q = input.trim()
    if (!q || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '서버 오류')
      setMessages(prev => [...prev, { role: 'bot', data, question: q }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', text: e.message }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleStartConsult(sessionId, question, meta) {
    setConsult({ sessionId, question, ...meta })
  }

  function handleCloseConsult() {
    setConsult(null)
  }

  return (
    <div className={styles.page}>
      {/* ── 헤더 ── */}
      <header className={styles.header}>
        <button className={styles.backBtn} onClick={() => navigate('/')}>
          ← 홈
        </button>
        <span className={styles.logo}>
          <span className={styles.logoMark}>◆</span> Finia
        </span>
        <div className={styles.headerRight}>
          <span className={styles.statusDot} />
          <span className={styles.statusText}>AI 온라인</span>
        </div>
      </header>

      <div className={styles.layout}>
        {/* ── 채팅 영역 ── */}
        <main className={styles.chatArea}>
          <div className={styles.messages}>
            {messages.length === 0 && (
              <motion.div
                className={styles.welcome}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className={styles.welcomeIcon}>◆</div>
                <h2 className={styles.welcomeTitle}>무엇이 궁금하신가요?</h2>
                <p className={styles.welcomeDesc}>
                  예금, 펀드, 대출, 외환에 관한 질문을 자유롭게 입력하세요.
                </p>
                <div className={styles.suggestions}>
                  {['적금 금리 높은 상품 알려줘', '달러 환전 수수료는?', '펀드 투자 어떻게 시작해?'].map(s => (
                    <button key={s} className={styles.suggestion} onClick={() => { setInput(s); inputRef.current?.focus() }}>
                      {s}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            <AnimatePresence>
              {messages.map((msg, i) => (
                <ChatMessage
                  key={i}
                  msg={msg}
                  onStartConsult={handleStartConsult}
                />
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div
                className={styles.typingWrap}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className={styles.typingDots}>
                  <span /><span /><span />
                </div>
              </motion.div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* ── 입력 ── */}
          <div className={styles.inputBar}>
            <input
              ref={inputRef}
              className={styles.input}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder="금융 관련 질문을 입력하세요..."
              disabled={loading}
              autoFocus
            />
            <button
              className={styles.sendBtn}
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              전송
            </button>
          </div>
        </main>

        {/* ── 상담 패널 (슬라이드인) ── */}
        <AnimatePresence>
          {consultSession && (
            <ConsultPanel
              session={consultSession}
              onClose={handleCloseConsult}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
