import { Link, useNavigate } from 'react-router'
import { useState, useRef, useEffect } from 'react'

const API = 'http://localhost:5000/api'


export default function UploadPage() {
  const [uploadOk, setUploadOk] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)
  const arquivoRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const dados = localStorage.getItem('dados_upload')
    if (dados) {
      navigate('/decisions')
    }
  }, [navigate])

  async function handleSubmit() {

    const file = arquivoRef.current?.files?.[0]
    if (!file) return

    if (file.size / (1024 * 1024) > 30) {
      setErro('Arquivo muito grande. Limite: 30 MB.')
      return
    }

    setEnviando(true)
    setErro(null)

    try {
      const body = new FormData()
      body.append('documento', file)
      const res = await fetch(`${API}/files/upload`, { method: 'POST', body })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erro ${res.status}`)
      }
      const resultado = await res.json()
      localStorage.setItem('dados_upload', JSON.stringify(resultado))
      setUploadOk(true)
    } catch (e: any) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Upload Dataset</h1>
          <p className="page-subtitle">Envie um arquivo CSV para iniciar a análise.</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <div className="section-title">Selecionar arquivo</div>

        <div className="input-file-zone" onClick={() => arquivoRef.current?.click()}>
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none"
            stroke="var(--green)" strokeWidth="1.5" viewBox="0 0 24 24"
            style={{ margin: '0 auto 10px', display: 'block' }}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          {fileName
            ? <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{fileName}</span>
            : <span>Clique para selecionar ou arraste um arquivo <strong>.csv</strong></span>
          }
          <input
            type="file"
            ref={arquivoRef}
            accept=".csv,.xlsx,.xls"
            style={{ display: 'none' }}
            onChange={e => setFileName(e.target.files?.[0]?.name ?? null)}
          />
        </div>

        {erro && <div className="alert-error" style={{ marginTop: 14 }}>{erro}</div>}

        <div style={{ display: 'flex', gap: 12, marginTop: 20, justifyContent: 'flex-end' }}>
          {uploadOk && (
            <Link to="/decisions" className="btn btn-outline">Configurar colunas →</Link>
          )}
          <button className="btn btn-primary" onClick={handleSubmit}
            disabled={enviando || !fileName}>
            {enviando ? 'Enviando...' : 'Enviar arquivo'}
          </button>
        </div>
      </div>
    </div>
  )
}
