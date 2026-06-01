import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import styles from './HomePage.module.css'

const features = [
  {
    icon: '📚',
    title: 'RAG 지식베이스',
    desc: '4,917개 금융 Q&A 데이터셋에서 가장 정확한 답변을 즉시 검색합니다.',
    tag: '예금 · 펀드 · 대출 · 외환',
  },
  {
    icon: '🧠',
    title: 'Semantic Entropy',
    desc: 'AI 답변의 신뢰도를 실시간으로 측정해 불확실한 정보를 사전에 차단합니다.',
    tag: 'Farquhar et al. 2024',
  },
  {
    icon: '📞',
    title: '전문가 연결',
    desc: 'AI 신뢰도가 낮을 때 즉시 전문 상담사와 실시간으로 연결됩니다.',
    tag: 'Discord 브릿지',
  },
]

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.12, duration: 0.6, ease: [0.22, 1, 0.36, 1] } }),
}

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <div className={styles.page}>
      {/* ── 배경 오브 ── */}
      <div className={styles.orb1} />
      <div className={styles.orb2} />

      {/* ── 헤더 ── */}
      <header className={styles.header}>
        <span className={styles.logo}>
          <span className={styles.logoMark}>◆</span> Finia
        </span>
        <nav className={styles.nav}>
          <a href="#features">서비스</a>
          <a href="#about">소개</a>
          <button className={styles.navCta} onClick={() => navigate('/chat')}>
            챗봇 시작
          </button>
        </nav>
      </header>

      {/* ── 히어로 ── */}
      <section className={styles.hero}>
        <motion.div
          className={styles.heroInner}
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.1 } } }}
        >
          <motion.p className={styles.eyebrow} variants={fadeUp} custom={0}>
            AI × 금융 상담
          </motion.p>
          <motion.h1 className={styles.headline} variants={fadeUp} custom={1}>
            금융의 복잡함을<br />
            <em>단 하나의 질문</em>으로
          </motion.h1>
          <motion.p className={styles.subhead} variants={fadeUp} custom={2}>
            RAG 검색과 Semantic Entropy 기반 신뢰도 분석으로<br />
            정확하고 안전한 금융 답변을 제공합니다.
          </motion.p>
          <motion.div className={styles.heroActions} variants={fadeUp} custom={3}>
            <button className={styles.ctaPrimary} onClick={() => navigate('/chat')}>
              무료로 시작하기 →
            </button>
            <a href="#features" className={styles.ctaSecondary}>
              서비스 소개 ↓
            </a>
          </motion.div>
        </motion.div>

        {/* 미니 챗 프리뷰 */}
        <motion.div
          className={styles.previewCard}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className={styles.previewHeader}>
            <span className={styles.previewDot} style={{ background: '#c0392b' }} />
            <span className={styles.previewDot} style={{ background: '#e67e22' }} />
            <span className={styles.previewDot} style={{ background: '#27ae60' }} />
            <span className={styles.previewTitle}>금융 상담 AI</span>
          </div>
          <div className={styles.previewBody}>
            <div className={styles.previewMsg + ' ' + styles.previewUser}>
              적금 금리 높은 상품 추천해줘
            </div>
            <div className={styles.previewMsg + ' ' + styles.previewBot}>
              <span className={styles.previewBadge}>📚 RAG</span>
              현재 최고 금리 적금 상품은 연 4.5%의 하나은행 정기적금으로, 12개월 이상 가입 시...
            </div>
            <div className={styles.previewMsg + ' ' + styles.previewUser}>
              ELS 투자 위험성은?
            </div>
            <div className={styles.previewMsg + ' ' + styles.previewBot}>
              <span className={styles.previewBadge} style={{ background: 'rgba(230,126,34,0.15)', color: '#e67e22' }}>⚠️ SE 분석 중</span>
              신뢰도를 측정하고 있습니다...
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── 피처 ── */}
      <section id="features" className={styles.features}>
        <motion.div
          className={styles.sectionLabel}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          핵심 기능
        </motion.div>
        <motion.h2
          className={styles.sectionTitle}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          세 겹의 안전망
        </motion.h2>
        <div className={styles.featureGrid}>
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              className={styles.featureCard}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
            >
              <span className={styles.featureIcon}>{f.icon}</span>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureDesc}>{f.desc}</p>
              <span className={styles.featureTag}>{f.tag}</span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── 통계 ── */}
      <section className={styles.stats}>
        {[['4,917', '금융 Q&A'], ['99ms', '평균 응답'], ['3단계', '신뢰도 검증']].map(([n, l]) => (
          <motion.div
            key={l}
            className={styles.statItem}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <span className={styles.statNum}>{n}</span>
            <span className={styles.statLabel}>{l}</span>
          </motion.div>
        ))}
      </section>

      {/* ── CTA 배너 ── */}
      <section id="about" className={styles.ctaBanner}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className={styles.ctaBannerTitle}>지금 바로 물어보세요</h2>
          <p className={styles.ctaBannerSub}>예금, 펀드, 대출, 외환 — 어떤 금융 질문이든 답합니다</p>
          <button className={styles.ctaPrimary} onClick={() => navigate('/chat')}>
            챗봇 시작하기 →
          </button>
        </motion.div>
      </section>

      {/* ── 푸터 ── */}
      <footer className={styles.footer}>
        <span className={styles.logo} style={{ fontSize: '1rem' }}>
          <span className={styles.logoMark}>◆</span> Finia
        </span>
        <span className={styles.footerMeta}>AI 금융 상담 서비스 · 투자 권유가 아닌 정보 제공 목적</span>
      </footer>
    </div>
  )
}
