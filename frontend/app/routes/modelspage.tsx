import { useNavigate } from 'react-router'
import { useState, useEffect } from 'react'

const API = 'http://localhost:5000/api'

type Modelo = { id: string; nome: string; tipo: 'numerico' | 'categorico' }
type DadosUpload = { key: string; colunas_numericas: string[]; colunas_categoricas: string[] }

export default function ModelsPage() {
  const navigate = useNavigate()
  const [dados, setDados]             = useState<DadosUpload | null>(null)
  const [modelos, setModelos]         = useState<Modelo[]>([])
  const [selecionados, setSelecionados] = useState<Record<string, boolean>>({})
  const [carregando, setCarregando]   = useState(true)
  const [enviando, setEnviando]       = useState(false)
  const [erro, setErro]               = useState<string | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem('dados_upload')
    if (!raw) { navigate('/upload'); return }
    const parsed: DadosUpload = JSON.parse(raw)
    setDados(parsed)

    fetch(`${API}/report/models`)
      .then(r => r.json())
      .then((lista: Modelo[]) => {
        setModelos(lista)
        setSelecionados(Object.fromEntries(lista.map(m => [m.id, false])))
      })
      .catch(() => setErro('Erro ao carregar modelos.'))
      .finally(() => setCarregando(false))
  }, [])

  const temCat = (dados?.colunas_categoricas?.length ?? 0) > 0
  const numericos    = modelos.filter(m => m.tipo === 'numerico')
  const categoricos  = modelos.filter(m => m.tipo === 'categorico')
  const selecionadosList = Object.entries(selecionados).filter(([_, v]) => v).map(([id]) => id)
  const algum = selecionadosList.length > 0

  function toggle(id: string, v: boolean) { setSelecionados(p => ({ ...p, [id]: v })) }

  function toggleGrupo(tipo: 'numerico' | 'categorico', v: boolean) {
    setSelecionados(p => {
      const n = { ...p }
      modelos.filter(m => m.tipo === tipo).forEach(m => { n[m.id] = v })
      return n
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!dados) return
    setEnviando(true); setErro(null)
    try {
      const res = await fetch(`${API}/report/generate/${dados.key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selecionados: selecionadosList,
          colunas_numericas: dados.colunas_numericas,
          colunas_categoricas: dados.colunas_categoricas,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erro ${res.status}`)
      }
      navigate('/report')
    } catch (e: any) { setErro(e.message) }
    finally { setEnviando(false) }
  }

  if (carregando) return (
    <div className="page-content">
      <p style={{ color: 'var(--text-muted)' }}>Carregando modelos...</p>
    </div>
  )

  function ModelTable({ lista, tipo }: { lista: Modelo[], tipo: 'numerico' | 'categorico' }) {
    const allChecked = lista.every(m => selecionados[m.id])
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
                  <input type="checkbox" checked={allChecked}
                    onChange={e => toggleGrupo(tipo, e.target.checked)} />
                </th>
              </tr>
            </thead>
            <tbody>
              {lista.map(m => (
                <tr key={m.id}>
                  <td style={{ fontWeight: 500 }}>{m.nome}</td>
                  <td style={{ textAlign: 'center' }}>
                    <input type="checkbox"
                      checked={selecionados[m.id] ?? false}
                      onChange={e => toggle(m.id, e.target.checked)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

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

      {erro && <div className="alert-error" style={{ marginBottom: 16 }}>{erro}</div>}

      <form onSubmit={handleSubmit}>
        <ModelTable lista={numericos} tipo="numerico" />
        {temCat && categoricos.length > 0 && (
          <ModelTable lista={categoricos} tipo="categorico" />
        )}
      </form>
    </div>
  )
}
