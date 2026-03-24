import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, FileText, FolderOpen, ShieldCheck, BarChart3,
  MessageSquareText, LogOut, Menu, X, Bell, Sparkles, Building2,
  AlertTriangle, UserPlus, Settings, Calendar, Clock, Search, Scale, TrendingUp
} from 'lucide-react';

import { useAuthStore } from '../../store/authStore';
import { useQuery } from '@tanstack/react-query';
import { complianceAPI } from '../../services/api';

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/clients', icon: Users, label: 'Clients' },
  { to: '/invoices', icon: FileText, label: 'Invoices' },
  { to: '/documents', icon: FolderOpen, label: 'Documents' },
  { to: '/compliance', icon: ShieldCheck, label: 'Compliance' },
  { to: '/reports', icon: BarChart3, label: 'Reports' },
  { to: '/trial-balance', icon: TrendingUp, label: 'Fin. Statements' },
  { to: '/gstr2b', icon: FileText, label: 'GSTR-2B Recon.' },
  { to: '/matters', icon: Building2, label: 'Matters' },
  { to: '/court-calendar', icon: Calendar, label: 'Court Calendar' },
  { to: '/drafting', icon: FileText, label: 'AI Drafting' },
  { to: '/legal-billing', icon: Clock, label: 'Legal Billing' },
  { to: '/legal-research', icon: Search, label: 'Legal Research' },
  { to: '/limitation', icon: Scale, label: 'Limitation Calc.' },
  { to: '/chat', icon: MessageSquareText, label: 'AI Chat' },
  { to: '/team', icon: UserPlus, label: 'Team' },
  { to: '/settings', icon: Settings, label: 'Settings' },

  // 🔥 AI FEATURES (NEW)
  { to: '/ocr', icon: Sparkles, label: 'OCR Scanner' },
  { to: '/tds', icon: FileText, label: 'TDS Manager' },
  { to: '/itr', icon: FileText, label: 'ITR Assistant' },
  { to: '/calendar', icon: Calendar, label: 'Tax Calendar' },
  { to: '/portal', icon: Users, label: 'Client Portal' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: alerts } = useQuery({
    queryKey: ['compliance-alerts'],
    queryFn: () => complianceAPI.allAlerts({ days_ahead: 7 }),
    refetchInterval: 60000,
  });

  const overdueCount = alerts?.filter(a => a.is_overdue).length || 0;
  const urgentCount = alerts?.filter(a => !a.is_overdue && a.days_left <= 3).length || 0;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      
      {/* Sidebar */}
      <aside className="w-60 border-r flex flex-col" style={{ background: 'var(--bg-surface)' }}>
        
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-blue-500">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Maavi AI</p>
            <p className="text-xs text-gray-400">CA Copilot</p>
          </div>
        </div>

        {/* User */}
        <div className="p-4 text-sm text-gray-300">
          <p>{user?.full_name}</p>
          <p className="text-xs text-gray-500">{user?.email}</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${
                  isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-3 border-t">
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        
        {/* Topbar */}
        <header className="flex justify-end items-center p-3 border-b bg-[#0f172a]">
          <div className="flex items-center gap-3 text-white">
            <Bell size={18} />
            <div className="bg-blue-600 w-8 h-8 rounded-full flex items-center justify-center">
              {user?.full_name?.[0]}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}