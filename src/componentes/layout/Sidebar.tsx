/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, Database, History, LogOut, ShieldAlert, Upload } from 'lucide-react';
import { useAuth } from '../../contextos/AuthContexto';

const Sidebar: React.FC = () => {
  const { logout } = useAuth();

  const navItems = [
    { name: 'Historico', path: '/historico', icon: History },
    { name: 'Meus Datasets', path: '/datasets', icon: Database },
    { name: 'Upload Dataset', path: '/upload', icon: Upload },
    { name: 'Nova Analise', path: '/analise/nova', icon: Activity },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white h-screen fixed left-0 top-0 flex flex-col border-r border-slate-800">
      <div className="p-6 flex items-center gap-3 border-b border-slate-800">
        <ShieldAlert className="text-emerald-400 w-8 h-8" />
        <h1 className="text-xl font-bold tracking-tight">AnomalyDetect</h1>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 p-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 p-3 w-full rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Sair</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
