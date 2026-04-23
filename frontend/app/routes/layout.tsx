import { Outlet, NavLink, useNavigate } from 'react-router'

export default function Layout() {
  const navigate = useNavigate()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
            <path d="M12 8v4"/><path d="M12 16h.01"/>
          </svg>
          <span>AnomalyDetect</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Histórico
          </NavLink>

          <NavLink to="/upload">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload Dataset
          </NavLink>

          <NavLink to="/decisions">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
            Selecionar Colunas
          </NavLink>

          <NavLink to="/decisions/models">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            Nova Análise
          </NavLink>
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => {
            localStorage.clear()
            navigate('/')
          }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none"
              stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sair
          </button>
        </div>
      </aside>

      <div className="main-area">
        <Outlet />
      </div>
    </div>
  )
}
