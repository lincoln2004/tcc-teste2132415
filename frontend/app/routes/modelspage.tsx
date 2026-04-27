import { useNavigate } from 'react-router'
import { useState, useEffect } from 'react'

const API = 'http://localhost:5000/api'

type Modelo = { id: string; nome: string; tipo: 'numerico' | 'categorico' }

// 🔥 CORREÇÃO: o tipo deve corresponder ao que vem do localStorage
type DadosUpload = { 
  key: string; 
  columns: Array<{ column: string; type: string }>;  // ← array de objetos
  colunas_numericas?: string[];
  colunas_categoricas?: string[];
}

const THRESHOLD_PRESETS = [
  { label: 'Conservador (1%)',  value: 0.01 },
  { label: 'Padrão (5%)',       value: 0.05 },
  { label: 'Moderado (10%)',    value: 0.10 },
  { label: 'Agressivo (20%)',   value: 0.20 },
]

function ModelTable({ 
  lista, 
  tipo, 
  selecionados, 
  onToggle, 
  onToggleGrupo 
}: { 
  lista: Modelo[]; 
  tipo: 'numerico' | 'categorico';
  selecionados: Record<string, boolean>;
  onToggle: (id: string, v: boolean) => void;
  onToggleGrupo: (tipo: 'numerico' | 'categorico', v: boolean) => void;
}) {
  const allChecked = lista.length > 0 && lista.every(m => selecionados[m.id])
  
  if (lista.length === 0) return null
  
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div className="section-title">
        {tipo === 'numerico' ? 'Modelos Numéricos' : 'Modelos Categóricos'}
      </div>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Modelo</th>
              <th style={{ width: 60, textAlign: 'center' }}>
                <input 
                  type="checkbox" 
                  checked={allChecked}
                  onChange={e => onToggleGrupo(tipo, e.target.checked)} 
                />
              </th>
            </tr>
          </thead>
          <tbody>
            {lista.map(m => (
              <tr key={m.id}>
                <td style={{ fontWeight: 500 }}>{m.nome}</td>
                <td style={{ textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selecionados[m.id] ?? false}
                    onChange={e => onToggle(m.id, e.target.checked)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function ModelsPage() {
  const navigate = useNavigate()
  const [dados, setDados]             = useState<DadosUpload | null>(null)
  const [modelos, setModelos]         = useState<Modelo[]>([])
  const [selecionados, setSelecionados] = useState<Record<string, boolean>>({})
  const [threshold, setThreshold]     = useState<number>(0.05)
  const [thresholdInput, setThresholdInput] = useState<string>('5')
  const [carregando, setCarregando]   = useState(true)
  const [enviando, setEnviando]       = useState(false)
  const [erro, setErro]               = useState<string | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem('dados_upload')
    if (!raw) { 
      navigate('/upload'); 
      return 
    }
    
    try {
      const parsed: DadosUpload = JSON.parse(raw)
      
      // 🔥 VALIDAÇÃO: verifica se tem as propriedades necessárias
      if (!parsed.key || !parsed.columns || !Array.isArray(parsed.columns)) {
        throw new Error('Dados inválidos: key ou columns ausentes')
      }
      
      // Se já tiver colunas selecionadas (veio do filtercolumns), mantém
      // Se não, inicializa com arrays vazios
      setDados({
        ...parsed,
        colunas_numericas: parsed.colunas_numericas || [],
        colunas_categoricas: parsed.colunas_categoricas || []
      })
    } catch (e) {
      console.error('Erro ao parsear dados do localStorage:', e)
      localStorage.removeItem('dados_upload')
      navigate('/upload')
      return
    }

    fetch(`${API}/report/models`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((lista: Modelo[]) => {
        setModelos(lista)
        setSelecionados(Object.fromEntries(lista.map(m => [m.id, false])))
      })
      .catch((err) => {
        console.error('Erro ao carregar modelos:', err)
        setErro('Erro ao carregar modelos. Tente novamente.')
      })
      .finally(() => setCarregando(false))
  }, [navigate])

  // 🔥 OBTÉM AS COLUNAS SELECIONADAS do localStorage (vindas do filtercolumns)
  const colunasNumericas = dados?.colunas_numericas ?? []
  const colunasCategoricas = dados?.colunas_categoricas ?? []
  const temCat = colunasCategoricas.length > 0
  const numericos    = modelos.filter(m => m.tipo === 'numerico')
  const categoricos  = modelos.filter(m => m.tipo === 'categorico')
  const selecionadosList = Object.entries(selecionados).filter(([_, v]) => v).map(([id]) => id)
  const algum = selecionadosList.length > 0

  function toggle(id: string, v: boolean) { 
    setSelecionados(p => ({ ...p, [id]: v })) 
  }

  function toggleGrupo(tipo: 'numerico' | 'categorico', v: boolean) {
    setSelecionados(p => {
      const n = { ...p }
      modelos.filter(m => m.tipo === tipo).forEach(m => { n[m.id] = v })
      return n
    })
  }

  function handleThresholdInput(raw: string) {
    setThresholdInput(raw)
    const val = parseFloat(raw)
    if (!isNaN(val) && val >= 0.5 && val <= 50) setThreshold(val / 100)
  }

  function handlePreset(val: number) {
    setThreshold(val)
    setThresholdInput(String(val * 100))
  }

  function handleInvalidFile() {
    localStorage.removeItem('dados_upload')
    setErro('O arquivo enviado é inválido ou está corrompido. Por favor, envie um novo arquivo CSV válido.')
    setTimeout(() => {
      navigate('/upload')
    }, 2000)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!dados) return
    
    // 🔥 VALIDA: verifica se há colunas selecionadas
    if (colunasNumericas.length === 0 && colunasCategoricas.length === 0) {
      setErro('Nenhuma coluna selecionada. Volte e selecione pelo menos uma coluna.')
      return
    }
    
    setEnviando(true); setErro(null)
    try {
      const res = await fetch(`${API}/report/generate/${dados.key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selecionados: selecionadosList,
          colunas_numericas: colunasNumericas,
          colunas_categoricas: colunasCategoricas,
          threshold,
        }),
      })
      
      if (res.status === 422) {
        const err = await res.json().catch(() => ({}))
        console.error('Erro 422 - Arquivo inválido:', err.detail)
        handleInvalidFile()
        return
      }
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erro ${res.status}`)
      }
      
      navigate('/report')
    } catch (e: any) { 
      setErro(e.message) 
    } finally { 
      setEnviando(false) 
    }
  }

  if (carregando) return (
    <div className="page-content">
      <p style={{ color: 'var(--text-muted)' }}>Carregando modelos...</p>
    </div>
  )

  const thresholdColor = threshold <= 0.05 ? '#05CB9D' : threshold <= 0.10 ? '#F39C12' : '#E74C3C'

  return (
    <div className="page-content">
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Selecionar Modelos</h1>
          <p className="page-subtitle">
            Escolha os detectores de anomalia para rodar. {selecionadosList.length} selecionados.
          </p>
        </div>
        <div className="btn-group">
          <button className="btn btn-primary" onClick={handleSubmit as any}
            disabled={!algum || enviando}>
            {enviando ? 'Gerando relatório...' : 'Gerar Relatório →'}
          </button>
        </div>
      </div>

      {erro && (
        <div className="alert-error" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>{erro}</span>
          {erro.includes('arquivo inválido') && (
            <button 
              onClick={() => navigate('/upload')} 
              style={{ background: 'none', border: 'none', color: 'var(--red)', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Fazer novo upload →
            </button>
          )}
        </div>
      )}

      {/* ── THRESHOLD ──────────────────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-title">Threshold de Corte (Contamination)</div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16, lineHeight: 1.6 }}>
          Fração esperada de anomalias no dataset. A maioria dos modelos usa esse valor como
          percentil de corte — registros acima desse limite são marcados como anomalia.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
          <input
            type="range" min={0.5} max={50} step={0.5}
            value={Math.round(threshold * 100 * 2) / 2}
            onChange={e => handlePreset(Number(e.target.value) / 100)}
            style={{ flex: 1, accentColor: thresholdColor, cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <input
              type="number" min={0.5} max={50} step={0.5}
              value={thresholdInput}
              onChange={e => handleThresholdInput(e.target.value)}
              style={{
                width: 65, padding: '4px 8px',
                border: `1.5px solid ${thresholdColor}`, borderRadius: 6,
                fontSize: 14, fontWeight: 700, color: thresholdColor,
                textAlign: 'center', background: 'var(--card-bg)', outline: 'none',
              }}
            />
            <span style={{ fontSize: 14, fontWeight: 700, color: thresholdColor }}>%</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)' }}>ATALHOS:</span>
          {THRESHOLD_PRESETS.map(p => {
            const ativo = Math.abs(threshold - p.value) < 0.001
            return (
              <button key={p.value} onClick={() => handlePreset(p.value)} style={{
                padding: '5px 12px', borderRadius: 20,
                border: ativo ? 'none' : '1px solid var(--border)',
                background: ativo ? thresholdColor : 'var(--card-bg)',
                color: ativo ? '#fff' : 'var(--text-muted)',
                fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
              }}>
                {p.label}
              </button>
            )
          })}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <ModelTable 
          lista={numericos} 
          tipo="numerico"
          selecionados={selecionados}
          onToggle={toggle}
          onToggleGrupo={toggleGrupo}
        />
        {temCat && categoricos.length > 0 && (
          <ModelTable 
            lista={categoricos} 
            tipo="categorico"
            selecionados={selecionados}
            onToggle={toggle}
            onToggleGrupo={toggleGrupo}
          />
        )}
      </form>
    </div>
  )
}