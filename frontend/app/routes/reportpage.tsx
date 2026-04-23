import { useNavigate } from 'react-router'
import { useState, useEffect } from 'react'
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, Scatter, ReferenceLine,
} from 'recharts'

const API = 'http://localhost:5000/api'

// ─── tipos ────────────────────────────────────────────────────────────────────
type AnaliseColuna = {
  tipo: 'numerico' | 'categorico'
  nulls: number
  outliers: number
  intervalos?: Record<string, number>
  frequencia?: Record<string, number>
}
type EstatisticaColuna = {
  min: number; max: number; media: number; mediana: number; q1: number; q3: number
}
type Relatorio = {
  arquivo: { nome: string; tipo: string; linhas: number; colunas: number; tamanho: string }
  analise_geral: Record<string, AnaliseColuna>
  estatisticas: Record<string, EstatisticaColuna>
  modelos: Record<string, Record<string, any>[]>
}

// ─── paleta ───────────────────────────────────────────────────────────────────
const GREEN  = '#05CB9D'
const RED    = '#E74C3C'
const NAVY   = '#0D1B2A'
const COLORS = [GREEN, '#3498DB', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#2ECC71', '#E91E63']

// ─── helpers ──────────────────────────────────────────────────────────────────
const short = (s: string, n = 14) => s.length > n ? s.slice(0, n) + '…' : s

const tooltipStyle = {
  borderRadius: 8, border: 'none',
  boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
  fontSize: 12, background: '#fff',
}

// ─── subcomponents ─────────────────────────────────────────────────────────────
function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 13, fontWeight: 700, color: NAVY,
      marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8,
      paddingBottom: 12, borderBottom: '2px solid var(--border)'
    }}>
      {children}
    </div>
  )
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div className="card" style={{ marginBottom: 20, ...style }}>
      {children}
    </div>
  )
}

// Chip de modelo no nav
function ModelChip({ label, active, onClick, tipo }: {
  label: string; active: boolean; onClick: () => void; tipo?: string
}) {
  return (
    <button onClick={onClick} style={{
      padding: '6px 14px',
      borderRadius: 20,
      border: active ? 'none' : '1px solid var(--border)',
      background: active ? (tipo === 'categorico' ? '#9B59B6' : GREEN) : 'var(--card-bg)',
      color: active ? '#fff' : 'var(--text-muted)',
      fontSize: 12, fontWeight: 600, cursor: 'pointer',
      transition: 'all 0.15s',
      whiteSpace: 'nowrap',
    }}>
      {label}
    </button>
  )
}

// ─── componente principal ─────────────────────────────────────────────────────
export default function ReportPage() {
  const navigate = useNavigate()
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null)
  const [modeloAtivo, setModeloAtivo] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  // seção ativa da análise de colunas
  const [colunaAtiva, setColunaAtiva] = useState('')

  // tab global
  const [secao, setSecao] = useState<'por_coluna' | 'modelos'>('por_coluna')

  useEffect(() => {
    fetch(`${API}/report`)
      .then(r => { if (!r.ok) throw new Error(); return r.json() })
      .then((data: Relatorio) => {
        setRelatorio(data)
        const primeiro = Object.keys(data.modelos)[0]
        if (primeiro) setModeloAtivo(primeiro)
        if (Object.keys(data.analise_geral)[0]) setColunaAtiva(Object.keys(data.analise_geral)[0])
      })
      .catch(() => setErro('Erro ao carregar relatório. Gere um novo.'))
      .finally(() => setCarregando(false))
  }, [])

  async function baixar(rota: string, nome: string) {
    try {
      const res = await fetch(rota)
      if (!res.ok) throw new Error(`Erro ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = nome; a.click()
      URL.revokeObjectURL(url)
    } catch (e: unknown) {
      alert(`Falha ao baixar: ${e instanceof Error ? e.message : 'Erro'}`)
    }
  }

  if (carregando) return <div className="page-content" style={{ paddingTop: 60, textAlign: 'center', color: 'var(--text-muted)' }}>Carregando relatório…</div>
  if (erro) return (
    <div className="page-content">
      <div className="alert-error" style={{ marginBottom: 16 }}>{erro}</div>
      <button className="btn btn-ghost" onClick={() => navigate('/decisions/models')}>← Voltar</button>
    </div>
  )
  if (!relatorio) return null

  const modelos = Object.keys(relatorio.modelos)
  const modeloData = modeloAtivo ? relatorio.modelos[modeloAtivo] ?? [] : []
  const totalLinhas = relatorio.arquivo.linhas

  const colunasNumericas = Object.keys(relatorio.analise_geral).filter(c => relatorio.analise_geral[c].tipo === 'numerico')
  const colunasCategoricas = Object.keys(relatorio.analise_geral).filter(c => relatorio.analise_geral[c].tipo === 'categorico')
  const todasColunas = Object.keys(relatorio.analise_geral)

  // ── dados por modelo ativo ────────────────────────────────────────────────
  const anomaliasAtivo = modeloData.filter(r => r.anomalia === 1).length
  const taxaAtivo = totalLinhas ? (anomaliasAtivo / totalLinhas * 100).toFixed(1) : '0'

  // ── comparação entre modelos ──────────────────────────────────────────────
  const comparacaoModelos = modelos.map(m => {
    const d = relatorio.modelos[m] ?? []
    const an = d.filter(r => r.anomalia === 1).length
    return { modelo: short(m, 18), anomalias: an, normais: d.length - an, taxa: +((an / d.length) * 100).toFixed(2) }
  })

  // ── dados por coluna ativa ────────────────────────────────────────────────
  const colunaInfo = relatorio.analise_geral[colunaAtiva]
  const colunaStats = relatorio.estatisticas[colunaAtiva]

  const dadosDistrib = colunaInfo?.tipo === 'numerico' && colunaInfo.intervalos
    ? Object.entries(colunaInfo.intervalos).map(([iv, ct]) => ({
        intervalo: iv.replace(/[\[\]()]/g, '').replace(',', ' – ').trim(),
        count: ct,
        pct: +((ct / totalLinhas) * 100).toFixed(1),
      }))
    : []

  const dadosFreq = colunaInfo?.tipo === 'categorico' && colunaInfo.frequencia
    ? Object.entries(colunaInfo.frequencia).map(([cat, fr]) => ({
        categoria: cat.length > 18 ? cat.slice(0, 18) + '…' : cat,
        pct: +(+fr * 100).toFixed(1),
        count: Math.round(+fr * totalLinhas),
      }))
    : []

  // ── scores com classificação para pontos (smoke) ──────────────────────────
  const dadosScores = modeloData.slice(0, 150).map((row, i) => ({
    linha: i + 1,
    score: row.score ?? 0,
    anomalia: row.anomalia,
  }))

  // ─── seções de navegação ──────────────────────────────────────────────────
  const tabs: { id: typeof secao; label: string }[] = [
    { id: 'por_coluna', label: '🔍 Por Coluna' },
    { id: 'modelos', label: '🤖 Modelos' },
  ]

  return (
    <div className="page-content">

      {/* ── header ──────────────────────────────────────────────────────────── */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div className="page-header-left">
          <button className="page-back" onClick={() => navigate('/decisions/models')}>← Nova análise</button>
          <h1 className="page-title">
            {relatorio.arquivo.nome}
            <span className="badge-format">CSV</span>
          </h1>
          <p className="page-subtitle">Análise exploratória · Detecção de anomalias</p>
        </div>
        <div className="btn-group">
          <button className="btn btn-outline" onClick={() => baixar(`${API}/report/pdf`, 'relatorio.pdf')}>
            <DownloadIcon /> Baixar PDF
          </button>
          <button className="btn btn-primary" onClick={() => baixar(`${API}/report/cleaned`, 'dados_tratados.csv')}>
            <DownloadIcon /> CSV Tratado
          </button>
        </div>
      </div>

      {/* ── stat cards ──────────────────────────────────────────────────────── */}
      <div className="stat-grid" style={{ marginBottom: 20 }}>
        {[
          { label: 'Linhas', value: totalLinhas.toLocaleString('pt-BR'), color: 'var(--text-primary)' },
          { label: 'Colunas', value: relatorio.arquivo.colunas },
          { label: 'Col. Numéricas', value: colunasNumericas.length },
          { label: 'Col. Categóricas', value: colunasCategoricas.length },
          { label: 'Modelos Aplicados', value: modelos.length },
          { label: `Anomalias (${short(modeloAtivo ?? '', 10)})`, value: anomaliasAtivo, color: anomaliasAtivo > 0 ? RED : GREEN },
          { label: 'Taxa de Anomalia', value: `${taxaAtivo}%`, color: +taxaAtivo > 5 ? RED : GREEN },
          { label: 'Tamanho', value: relatorio.arquivo.tamanho },
        ].map((s, i) => (
          <div key={i} className="stat-card">
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── nav de modelos ─────────────────────────────────────────────────── */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            MODELO ATIVO:
          </span>
          {modelos.map(m => (
            <ModelChip
              key={m}
              label={m.replace(/_/g, ' ')}
              active={modeloAtivo === m}
              onClick={() => setModeloAtivo(m)}
              tipo={m.includes('freq') || m.includes('chi') || m.includes('entrop') || m.includes('binom') || m.includes('assoc') || m.includes('lof_cat') ? 'categorico' : 'numerico'}
            />
          ))}
        </div>
        {modeloAtivo && (
          <div style={{ display: 'flex', gap: 32, marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)', flexWrap: 'wrap' }}>
            <MiniStat label="Total" value={modeloData.length} />
            <MiniStat label="Normais" value={modeloData.length - anomaliasAtivo} color={GREEN} />
            <MiniStat label="Anomalias" value={anomaliasAtivo} color={RED} />
            <MiniStat label="Taxa" value={`${taxaAtivo}%`} color={+taxaAtivo > 5 ? RED : GREEN} />
          </div>
        )}
      </Card>

      {/* ── tabs de seção ───────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setSecao(t.id)} style={{
            padding: '9px 18px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            border: secao === t.id ? 'none' : '1px solid var(--border)',
            background: secao === t.id ? NAVY : 'var(--card-bg)',
            color: secao === t.id ? '#fff' : 'var(--text-muted)',
            cursor: 'pointer', transition: 'all 0.15s',
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SEÇÃO: POR COLUNA
      ════════════════════════════════════════════════════════════════════ */}
      {secao === 'por_coluna' && (
        <>
          {/* seletor de coluna */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>COLUNA:</span>
              {todasColunas.map(col => {
                const isNum = relatorio.analise_geral[col].tipo === 'numerico'
                return (
                  <button key={col} onClick={() => setColunaAtiva(col)} style={{
                    padding: '5px 12px', borderRadius: 16, fontSize: 11, fontWeight: 600,
                    border: colunaAtiva === col ? 'none' : '1px solid var(--border)',
                    background: colunaAtiva === col ? (isNum ? GREEN : '#9B59B6') : 'var(--card-bg)',
                    color: colunaAtiva === col ? '#fff' : 'var(--text-muted)',
                    cursor: 'pointer',
                  }}>
                    {col} <span style={{ opacity: 0.7, fontSize: 9 }}>{isNum ? 'NUM' : 'CAT'}</span>
                  </button>
                )
              })}
            </div>
          </Card>

          {colunaInfo && (
            <>
              {/* info rápida da coluna */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
                {[
                  { label: 'Tipo', value: colunaInfo.tipo === 'numerico' ? 'Numérico' : 'Categórico' },
                  { label: 'Nulos', value: colunaInfo.nulls, color: colunaInfo.nulls > 0 ? '#F39C12' : GREEN },
                  { label: 'Outliers (IQR)', value: colunaInfo.outliers, color: colunaInfo.outliers > 0 ? RED : GREEN },
                  ...(colunaStats ? [
                    { label: 'Média', value: colunaStats.media.toFixed(4) },
                    { label: 'Mediana', value: colunaStats.mediana.toFixed(4) },
                    { label: 'Mínimo', value: colunaStats.min.toFixed(4) },
                    { label: 'Máximo', value: colunaStats.max.toFixed(4) },
                    { label: 'Q1', value: colunaStats.q1.toFixed(4) },
                    { label: 'Q3', value: colunaStats.q3.toFixed(4) },
                  ] : []),
                ].map((s, i) => (
                  <div key={i} className="stat-card">
                    <div className="stat-label">{s.label}</div>
                    <div className="stat-value" style={{ color: (s as any).color ?? 'var(--text-primary)', fontSize: 16 }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* gráfico de distribuição / frequência */}
              <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 20, marginBottom: 20 }}>
                <Card style={{ margin: 0 }}>
                  <SectionTitle>
                    {colunaInfo.tipo === 'numerico' ? 'Distribuição de Frequência (Histograma)' : 'Frequência das Categorias'}
                  </SectionTitle>
                  {colunaInfo.tipo === 'numerico' && dadosDistrib.length > 0 && (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={dadosDistrib}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="intervalo" angle={-30} textAnchor="end" height={70} fontSize={9} />
                        <YAxis fontSize={10} />
                        <Tooltip formatter={(v: any, n: any) => [n === 'count' ? `${v} registros` : `${v}%`, n === 'count' ? 'Frequência' : '% do total']} contentStyle={tooltipStyle} />
                        <Legend />
                        <Bar dataKey="count" fill={GREEN} name="Frequência" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                  {colunaInfo.tipo === 'categorico' && dadosFreq.length > 0 && (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={dadosFreq} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis type="number" fontSize={10} unit="%" />
                        <YAxis type="category" dataKey="categoria" width={140} fontSize={10} />
                        <Tooltip formatter={(v: any, n: any, p: any) => [`${p.payload.count} (${v}%)`, 'Frequência']} contentStyle={tooltipStyle} />
                        <Bar dataKey="pct" name="% do total" radius={[0, 5, 5, 0]}>
                          {dadosFreq.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </Card>

                <Card style={{ margin: 0 }}>
                  <SectionTitle>Proporção</SectionTitle>
                  {colunaInfo.tipo === 'categorico' && dadosFreq.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={dadosFreq} dataKey="pct" nameKey="categoria"
                          cx="50%" cy="50%" outerRadius={90} innerRadius={40}
                          label={(e: any) => e.pct > 5 ? `${e.pct}%` : ''}
                        >
                          {dadosFreq.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(v: any) => [`${v}%`, '']} contentStyle={tooltipStyle} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={[
                          { name: 'Normal', value: totalLinhas - colunaInfo.outliers, color: GREEN },
                          { name: 'Outlier', value: colunaInfo.outliers, color: RED },
                        ]} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={40}
                          label={(e: any) => e.value > 0 ? `${((e.value / totalLinhas) * 100).toFixed(1)}%` : ''}
                        >
                          <Cell fill={GREEN} />
                          <Cell fill={RED} />
                        </Pie>
                        <Tooltip formatter={(v: any) => [v, 'registros']} contentStyle={tooltipStyle} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </Card>
              </div>

              {/* Para numérico: area chart com anomalias por modelo ativo */}
              {colunaInfo.tipo === 'numerico' && modeloAtivo && modeloData.length > 0 && (
                <Card>
                  <SectionTitle>Valores de "{colunaAtiva}" ao longo do dataset — modelo: {modeloAtivo}</SectionTitle>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={modeloData.slice(0, 200).map((r, i) => ({
                      linha: i + 1,
                      valor: r[colunaAtiva] ?? null,
                      anomalia: r.anomalia,
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="linha" fontSize={10} />
                      <YAxis fontSize={10} />
                      <Tooltip formatter={(v: any) => [+v.toFixed(4), colunaAtiva]} contentStyle={tooltipStyle} />
                      <defs>
                        <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={GREEN} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={GREEN} stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="valor" stroke={GREEN} fill="url(#grad)" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                    Exibindo até 200 primeiros registros.
                  </p>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          SEÇÃO: MODELOS
      ════════════════════════════════════════════════════════════════════ */}
      {secao === 'modelos' && (
        <>
          {/* grid de pie charts — um por modelo */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16, marginBottom: 20 }}>
            {modelos.map(m => {
              const d = relatorio.modelos[m] ?? []
              const an = d.filter(r => r.anomalia === 1).length
              const nm = d.length - an
              const taxa = d.length ? +(an / d.length * 100).toFixed(1) : 0
              return (
                <div key={m} onClick={() => setModeloAtivo(m)} style={{
                  background: 'var(--card-bg)', border: `2px solid ${modeloAtivo === m ? GREEN : 'var(--border)'}`,
                  borderRadius: 12, padding: 16, cursor: 'pointer',
                  boxShadow: modeloAtivo === m ? `0 0 0 3px ${GREEN}22` : 'var(--shadow)',
                  transition: 'all 0.15s',
                }}>
                  <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, textAlign: 'center' }}>
                    {m.replace(/_/g, ' ')}
                  </div>
                  <ResponsiveContainer width="100%" height={150}>
                    <PieChart>
                      <Pie data={[
                        { name: 'Normais', value: nm },
                        { name: 'Anomalias', value: an },
                      ]} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={35} outerRadius={60}
                        label={(e: any) => e.value > 0 ? `${((e.value / d.length) * 100).toFixed(0)}%` : ''}
                        labelLine={false}
                      >
                        <Cell fill={GREEN} />
                        <Cell fill={RED} />
                      </Pie>
                      <Tooltip formatter={(v: any) => [v, 'registros']} contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 8 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}><span style={{ color: GREEN }}>●</span> {nm}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}><span style={{ color: RED }}>●</span> {an}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: taxa > 10 ? RED : GREEN }}>{taxa}%</span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* evolução de score do modelo ativo COM PONTOS (SMOKE) */}
          {modeloAtivo && dadosScores.length > 0 && (
            <Card>
              <SectionTitle>Score de Anomalia por Registro — {modeloAtivo}</SectionTitle>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={dadosScores}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="linha" fontSize={10} label={{ value: 'Registro', position: 'insideBottomRight', offset: -5, fontSize: 10 }} />
                  <YAxis fontSize={10} domain={[0, 'auto']} />
                  <Tooltip 
                    formatter={(v: any, name: string | any, props: any) => {
                      if (name === 'score') return [v.toFixed(6), 'Score']
                      if (name === 'normais') return [v, 'Normal']
                      if (name === 'anomalias') return [v, 'Anomalia']
                      return [v, name]
                    }}
                    contentStyle={tooltipStyle}
                  />
                  <Legend />
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={GREEN} stopOpacity={0.4} />
                      <stop offset="95%" stopColor={GREEN} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <Area 
                    type="monotone" 
                    dataKey="score" 
                    stroke={GREEN} 
                    fill="url(#scoreGrad)" 
                    dot={false} 
                    name="Score" 
                  />
                  {/* Pontos para normais (score) */}
                  <Scatter 
                    name="✅ Normais"
                    data={dadosScores.filter(d => d.anomalia === 0).map(d => ({ linha: d.linha, score: d.score }))}
                    dataKey="score"
                    fill={GREEN}
                    fillOpacity={0.8}
                    shape="circle"
                    legendType="circle"
                  />
                  {/* Pontos para anomalias */}
                  <Scatter 
                    name="⚠️ Anomalias"
                    data={dadosScores.filter(d => d.anomalia === 1).map(d => ({ linha: d.linha, score: d.score }))}
                    dataKey="score"
                    fill={RED}
                    fillOpacity={0.9}
                    shape="circle"
                    legendType="circle"
                  />
                </AreaChart>
              </ResponsiveContainer>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                Score dos primeiros 150 registros. <span style={{ color: GREEN }}>● Pontos verdes</span> = normais | 
                <span style={{ color: RED, marginLeft: 8 }}>● Pontos vermelhos</span> = anomalias detectadas
              </p>
            </Card>
          )}

          {/* taxa de anomalia por modelo — barras */}
          <Card>
            <SectionTitle>Taxa de Anomalia Comparativa (%)</SectionTitle>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={comparacaoModelos}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="modelo" angle={-20} textAnchor="end" height={70} fontSize={10} />
                <YAxis fontSize={10} unit="%" domain={[0, 'auto']} />
                <Tooltip formatter={(v: any) => [`${v}%`, 'Taxa']} contentStyle={tooltipStyle} />
                <ReferenceLine y={5} stroke="#F39C12" strokeDasharray="4 4" label={{ value: '5%', fontSize: 10, fill: '#F39C12' }} />
                <Bar dataKey="taxa" name="Taxa de Anomalia" radius={[6, 6, 0, 0]}>
                  {comparacaoModelos.map((e, i) => (
                    <Cell key={i} fill={e.taxa > 10 ? RED : e.taxa > 5 ? '#F39C12' : GREEN} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}
    </div>
  )
}

// ─── micro-componentes ────────────────────────────────────────────────────────
function MiniStat({ label, value, color }: { label: string; value: any; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color ?? 'var(--text-primary)' }}>{value}</div>
    </div>
  )
}

function DownloadIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none"
      stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}