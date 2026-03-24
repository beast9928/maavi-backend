app_js = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\App.js'

content = """import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ClientsPage from './pages/ClientsPage';
import ClientDetailPage from './pages/ClientDetailPage';
import InvoicesPage from './pages/InvoicesPage';
import DocumentsPage from './pages/DocumentsPage';
import CompliancePage from './pages/CompliancePage';
import ReportsPage from './pages/ReportsPage';
import ChatPage from './pages/ChatPage';
import GSTPage from './pages/GSTPage';
import TeamPage from './pages/TeamPage';
import SettingsPage from './pages/SettingsPage';
import MattersPage from './pages/MattersPage';
import CourtCalendarPage from './pages/CourtCalendarPage';
import LegalDraftingPage from './pages/LegalDraftingPage';
import LegalBillingPage from './pages/LegalBillingPage';
import LegalResearchPage from './pages/LegalResearchPage';
import LimitationPage from './pages/LimitationPage';
import TrialBalancePage from './pages/TrialBalancePage';
import GSTR2BPage from './pages/GSTR2BPage';

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated() ? <Navigate to="/dashboard" replace /> : children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="clients" element={<ClientsPage />} />
          <Route path="clients/:id" element={<ClientDetailPage />} />
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="compliance" element={<CompliancePage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="gst" element={<GSTPage />} />
          <Route path="team" element={<TeamPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="matters" element={<MattersPage />} />
          <Route path="court-calendar" element={<CourtCalendarPage />} />
          <Route path="drafting" element={<LegalDraftingPage />} />
          <Route path="legal-billing" element={<LegalBillingPage />} />
          <Route path="legal-research" element={<LegalResearchPage />} />
          <Route path="limitation" element={<LimitationPage />} />
          <Route path="trial-balance" element={<TrialBalancePage />} />
          <Route path="gstr2b" element={<GSTR2BPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
"""

open(app_js, 'w', encoding='utf-8').write(content)
print('App.js completely rewritten - clean with no duplicates!')