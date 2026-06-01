import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import styles from './ConsultPanel.module.css'
import { API } from '../api'

export default function ConsultPanel({ session, onClose }) {
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [online, setOnline]     = useState(true)
  const esRef     = useRef(null)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    const es = new EventSource(`${API}/consult/stream/${session.sessionId}`)
    esRef.current = es

    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'message') {
        setMessages(prev => [...prev, { from: 'consultant', author: data.author, text: data.content }])
      }
    }
    es.onerror = () => { setOnline(false); es.close() }

    return () => es.close()
  }, [session.sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMsg() {
    const text = input.trim()
    if (!text || !online) return
    setInput('')
    setMessages(prev => [...prev, { from: 'client', text }])

    await fetch(`${API}/consult/message/${session.sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    }).catch(() => {})
  }

  async function handleClose() {
    await fetch(`${API}/consult/close/${session.sessionId}`, { method: 'POST' }).catch(() => {})
    esRef.current?.close()
    onClose()
  }

  return (
    <motion.aside
      className={styles.panel}
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', stiffness: 280, damping: 28 }}
    >
      {/* 헤더 */}
      <div className={styles.panelHeader}>
        <div className={styles.panelTitle}>
          <span className={`${styles.onlineDot} ${!online ? styles.offline : ''}`} />
          전문 상담사
        </div>
        <button className={styles.closeBtn} onClick={handleClose}>✕ 종료</button>
      </div>

      {/* 질문 컨텍스트 */}
      <div className={styles.context}>
        <span className={styles.contextLabel}>상담 질문</span>
        <p className={styles.contextText}>{session.question}</p>
      </div>

      {/* 메시지 */}
      <div className={styles.messages}>
        {messages.length === 0 && (
          <p className={styles.waiting}>상담사 응답을 기다리는 중...</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`${styles.msg} ${m.from === 'client' ? styles.msgClient : styles.msgConsult}`}>
            {m.from === 'consultant' && (
              <span className={styles.author}>{m.author || '상담사'}</span>
            )}
            <div className={styles.msgBubble}>{m.text}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 입력 */}
      <div className={styles.inputRow}>
        <input
          ref={inputRef}
          className={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); sendMsg() } }}
          placeholder={online ? '메시지 입력...' : '연결이 끊겼습니다'}
          disabled={!online}
        />
        <button className={styles.sendBtn} onClick={sendMsg} disabled={!input.trim() || !online}>
          →
        </button>
      </div>
    </motion.aside>
  )
}
