/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { User, Bell, Search } from 'lucide-react';
import { useAuth } from '../../contextos/AuthContexto';

const Navbar: React.FC = () => {
  const { usuario } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 fixed top-0 right-0 left-64 z-10 px-8 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-4 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 w-96">
        <Search className="w-4 h-4 text-slate-400" />
        <input 
          type="text" 
          placeholder="Pesquisar datasets ou análises..." 
          className="bg-transparent border-none outline-none text-sm text-slate-600 w-full"
        />
      </div>

      <div className="flex items-center gap-6">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-emerald-500 rounded-full border-2 border-white"></span>
        </button>

        <div className="flex items-center gap-3 pl-6 border-l border-slate-200">
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">{usuario?.nome}</p>
            <p className="text-xs text-slate-500">{usuario?.email}</p>
          </div>
          <div className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center border border-emerald-200">
            <User className="w-5 h-5" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
