import { useNavigate } from 'react-router'
import { useState, useEffect } from 'react'

type ColumnInfo = { column: string; type: 'numerico' | 'categorico' }
type DadosUpload = { key: string; columns: ColumnInfo[] }

export default function FilterColumns() {
  const [dados, setDados]             = useState<DadosUpload | null>(null)
  const [selecionadas, setSelecionadas] = useState<Record<string, boolean>>({})
  const navigate = useNavigate()

  useEffect(() => {
    const raw = localStorage.getItem('dados_upload')
    if (!raw) { navigate('/upload'); return }
    const parsed: DadosUpload = JSON.parse(raw)
    setDados(parsed)
    setSelecionadas(Object.fromEntries(parsed.columns.map(c => [c.column, true])))
  }, [])

  function toggleAll(checked: boolean) {
    if (!dados) return
    setSelecionadas(Object.fromEntries(dados.columns.map(c => [c.column, checked])))
  }

  function handleConfirmar() {
    if (!dados) return
    const selected = Object.entries(selecionadas).filter(([_, v]) => v).map(([c]) => c)
    const colunas_numericas   = dados.columns.filter(c => selected.includes(c.column) && c.type === 'numerico').map(c => c.column)
    const colunas_categoricas = dados.columns.filter(c => selected.includes(c.column) && c.type === 'categorico').map(c => c.column)
    localStorage.setItem('dados_upload', JSON.stringify({ ...dados, colunas_numericas, colunas_categoricas }))
    navigate('/decisions/models')
  }

  const alguma = Object.values(selecionadas).some(Boolean)
  const numSelecionadas = Object.values(selecionadas).filter(Boolean).length

  return (
    <div className="page-content">
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Selecionar Colunas</h1>
          <p className="page-subtitle">
            Escolha quais colunas serão analisadas. {numSelecionadas} de {dados?.columns.length ?? 0} selecionadas.
          </p>
        </div>
        <div className="btn-group">
          <button className="btn btn-primary" onClick={handleConfirmar} disabled={!alguma}>
            Confirmar e continuar →
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Coluna</th>
                <th>Tipo detectado</th>
                <th style={{ width: 60, textAlign: 'center' }}>
                  <input type="checkbox" defaultChecked
                    onChange={e => toggleAll(e.target.checked)} />
                </th>
              </tr>
            </thead>
            <tbody>
              {dados?.columns.map(({ column, type }) => (
                <tr key={column}>
                  <td style={{ fontWeight: 500 }}>{column}</td>
                  <td>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                      background: type === 'numerico' ? '#EFF6FF' : '#F5F3FF',
                      color: type === 'numerico' ? '#1D4ED8' : '#6D28D9',
                    }}>
                      {type}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <input type="checkbox"
                      checked={selecionadas[column] ?? false}
                      onChange={e => setSelecionadas(p => ({ ...p, [column]: e.target.checked }))} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
