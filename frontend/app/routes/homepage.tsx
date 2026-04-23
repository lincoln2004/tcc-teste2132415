import { Link } from 'react-router'

export default function HomePage() {
  return (
    <div className="page-content">
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Meus Datasets</h1>
          <p className="page-subtitle">Gerencie e analise seus arquivos de dados.</p>
        </div>
        <div className="btn-group">
          <Link to="/upload" className="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload Dataset
          </Link>
        </div>
      </div>

      <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="none"
          stroke="var(--green)" strokeWidth="1.5" viewBox="0 0 24 24"
          style={{ margin: '0 auto 16px' }}>
          <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
          <path d="M12 8v4"/><path d="M12 16h.01"/>
        </svg>
        <p style={{ fontSize: 15, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 6 }}>
          Nenhum dataset ainda
        </p>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
          Faça upload de um arquivo CSV para começar sua análise de anomalias.
        </p>
        <Link to="/upload" className="btn btn-primary" style={{ display: 'inline-flex' }}>
          Começar nova análise
        </Link>
      </div>
    </div>
  )
}
