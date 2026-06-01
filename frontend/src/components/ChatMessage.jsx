import { useState } from 'react'
import { motion } from 'framer-motion'
import styles from './ChatMessage.module.css'

const MODE_INFO = {
  rag: { label: '📚 QA 직접 반환', desc: '데이터셋 답변' },
  se:  { label: '🧠 RAG + LLM',   desc: 'RAG 컨텍스트 + LLM 생성' },
  mcp: { label: '🔧 MCP',          desc: '외부 도구 호출' },
}

const CONF_CLASS = { 높음: 'high', 보통: 'medium', 낮음: 'low' }
const CONF_EMOJI = { 높음: '✅', 보통: '⚠️', 낮음: '❌' }

export default function ChatMessage({ msg, onStartConsult }) {
  const [samplesOpen, setSamplesOpen] = useState(false)
  const [connecting, setConnecting]   = useState(false)
  const [connected, setConnected]     = useState(false)

  if (msg.role === 'user') {
    return (
      <motion.div
        className={styles.userWrap}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className={styles.userBubble}>{msg.text}</div>
      </motion.div>
    )
  }

  if (msg.role === 'error') {
    return (
      <motion.div
        className={styles.errorBubble}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        ⚠️ {msg.text}
      </motion.div>
    )
  }

  const { data, question } = msg
  const conf      = data.confidence || '높음'
  const mode      = data.mode || 'rag'
  const modeInfo  = MODE_INFO[mode] || MODE_INFO.rag
  const confClass = CONF_CLASS[conf] || 'high'
  const retrieved = data.retrieved || []
  const samples   = data.samples || []
  const tools     = data.tools_used || []
  const showConsult = (conf === '낮음' || conf === '보통') && mode !== 'rag'

  async function handleConsult() {
    setConnecting(true)
    try {
      const res = await fetch(`${API}/consult/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          semantic_entropy: data.semantic_entropy,
          normalized_se: data.normalized_se,
          confidence: conf,
        }),
      })
      const { session_id } = await res.json()
      if (!res.ok) throw new Error()
      setConnected(true)
      onStartConsult(session_id, question, { confidence: conf })
    } catch {
      setConnecting(false)
    }
  }

  return (
    <motion.div
      className={styles.botWrap}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className={styles.botBubble}>
        {/* 모드 태그 */}
        <div className={styles.modeLine}>
          <span className={styles.modeTag}>{modeInfo.label}</span>
          <span className={styles.modeSub}>· {modeInfo.desc}</span>
          <span className={styles.modeSub}>· 유사도 {(data.top_similarity * 100).toFixed(0)}%</span>
        </div>

        {/* 답변 본문 */}
        <p className={styles.answer}>{data.answer}</p>

        {/* 신뢰도 배지 */}
        {mode !== 'rag' && (
          <div className={styles.seArea}>
            <span className={`${styles.confBadge} ${styles[confClass]}`}>
              {CONF_EMOJI[conf]} 신뢰도: {conf}
            </span>
            <span className={styles.seDetail}>
              SE {(data.semantic_entropy || 0).toFixed(3)} &nbsp;·&nbsp;
              정규화 {((data.normalized_se || 0) * 100).toFixed(1)}% &nbsp;·&nbsp;
              클러스터 {data.n_clusters || 0}개
            </span>
          </div>
        )}

        {/* 도구 사용 */}
        {tools.length > 0 && (
          <p className={styles.seDetail}>🔧 사용된 도구: {tools.join(', ')}</p>
        )}

        {/* 샘플 토글 */}
        {samples.length > 0 && (
          <div>
            <button className={styles.samplesToggle} onClick={() => setSamplesOpen(o => !o)}>
              {samplesOpen ? '샘플 숨기기' : `샘플 답변 보기 (${samples.length}개)`}
            </button>
            {samplesOpen && (
              <ul className={styles.samplesList}>
                {samples.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            )}
          </div>
        )}

        {/* 출처 */}
        {retrieved.filter(r => r.topic).length > 0 && (
          <p className={styles.sources}>
            출처: {retrieved.filter(r => r.topic).map(r => `${r.topic}${r.source ? ' / ' + r.source : ''}`).join(' · ')}
          </p>
        )}

        {/* 상담사 연결 */}
        {showConsult && (
          <div className={styles.consultArea}>
            <p className={styles.consultNotice}>
              AI 신뢰도가 {conf}입니다. 전문 상담사와 연결하시겠어요?
            </p>
            <button
              className={`${styles.consultBtn} ${connected ? styles.consultDone : ''}`}
              onClick={!connected ? handleConsult : undefined}
              disabled={connecting || connected}
            >
              {connected ? '🟢 상담사 연결됨' : connecting ? '⏳ 연결 중...' : '📞 상담사 연결'}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}
