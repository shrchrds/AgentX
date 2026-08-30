import React from 'react';
import { Link } from 'react-router-dom';

const NavBar = () => {
  return (
    <nav className="bg-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-xl font-bold tracking-tight hover:text-slate-300 transition-colors">
              AgentX Legal Framework
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Dashboard</Link>
            <Link to="/tasks" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Tasks</Link>
            <Link to="/agents" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Agents</Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavBar;