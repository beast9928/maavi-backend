# -*- coding: utf-8 -*-
import os

PAGES = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\pages'

# ── Trial Balance + P&L Page ──────────────────────────────────────────────
trial_balance_page = r"""import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, clientsAPI } from '../services/api';
import { Download, TrendingUp, TrendingDown } from 'lucide-react';

export default function TrialBalancePage() {
  const [client, setClient] = useState('');
  const [view, setView] = useState('pnl');
  const { data: clients = [] } = useQuery({ queryKey: ['clients'], queryFn: () => clientsAPI.list({ limit: 100 }) });
  const { data: tb } = useQuery({ queryKey: ['trial-balance', client], queryFn: () => api.get(`/extra/client/${client}/trial-balance`).then(r => r.data), enabled: !!client });
  const { data: pnl } = useQuery({ queryKey: ['pnl', client], queryFn: () => api.get(`/extra/client/${client}/pnl`).then(r => r.data), enabled: !!client });
  const fmt = n => '₹' + (n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  return (
    <div className="p-6 fade-in-up">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div><h1 className="page-title">Financial Statements</h1><p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Trial Balance · P&L · Balance Sheet</p></div>
        <div className="flex gap-3 flex-wrap">
          <select className="input-field w-56" value={client} onChange={e => setClient(e.target.value)}>
            <option value="">Select Client...</option>
            {clients.map(c => <option key={c.id} value={c.id}>{c.company_name}</option>)}
          </select>
          {client && <button className="btn-ghost text-sm" onClick={() => window.open(`/api/v1/extra/client/${client}/report-pdf`)}>
            <Download size={14} /> Export PDF
          </button>}
        </div>
      </div>

      {client && (
        <div className="flex gap-2 mb-5">
          {['pnl', 'trial-balance'].map(v => (
            <button key={v} onClick={() => setView(v)} className={view === v ? 'btn-primary text-sm' : 'btn-ghost text-sm'}>
              {v === 'pnl' ? 'P&L Statement' : 'Trial Balance'}
            </button>
          ))}
        </div>
      )}

      {!client ? (
        <div className="card p-12 text-center" style={{ color: 'var(--text-muted)' }}>Select a client to view financial statements</div>
      ) : view === 'pnl' && pnl ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card overflow-hidden">
            <div className="p-4 border-b" style={{ borderColor: 'var(--border)' }}><p className="section-title">Profit & Loss Statement</p></div>
            <div className="p-4 space-y-2">
              <div className="p-3 rounded-lg" style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <p className="text-xs font-semibold mb-2" style={{ color: '#4ade80' }}>INCOME</p>
                {pnl.income.map((i, idx) => (
                  <div key={idx} className="flex justify-between text-sm py-1"><span style={{ color: 'var(--text-secondary)' }}>{i.head}</span><span className="font-medium">{fmt(i.amount)}</span></div>
                ))}
                <div className="flex justify-between text-sm font-bold pt-2 border-t mt-2" style={{ borderColor: 'rgba(34,197,94,0.3)' }}>
                  <span>Total Income</span><span style={{ color: '#4ade80' }}>{fmt(pnl.total_income)}</span>
                </div>
              </div>
              <div className="p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <p className="text-xs font-semibold mb-2" style={{ color: '#f87171' }}>EXPENSES</p>
                {pnl.expenses.map((e, idx) => (
                  <div key={idx} className="flex justify-between text-sm py-1"><span style={{ color: 'var(--text-secondary)' }}>{e.head}</span><span className="font-medium">{fmt(e.amount)}</span></div>
                ))}
                <div className="flex justify-between text-sm font-bold pt-2 border-t mt-2" style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
                  <span>Total Expenses</span><span style={{ color: '#f87171' }}>{fmt(pnl.total_expenses)}</span>
                </div>
              </div>
              <div className="p-3 rounded-lg" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                <div className="flex justify-between text-sm py-1"><span style={{ color: 'var(--text-secondary)' }}>Gross Profit</span><span className="font-medium">{fmt(pnl.gross_profit)}</span></div>
                <div className="flex justify-between text-sm py-1"><span style={{ color: 'var(--text-secondary)' }}>Estimated Tax (25%)</span><span className="font-medium">({fmt(pnl.tax_estimate)})</span></div>
                <div className="flex justify-between text-sm font-bold pt-2 border-t mt-2" style={{ borderColor: 'var(--border)' }}>
                  <span>Net Profit</span>
                  <span style={{ color: pnl.net_profit >= 0 ? '#4ade80' : '#f87171' }}>{fmt(pnl.net_profit)}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            {[{ label: 'Total Revenue', value: fmt(pnl.total_income), color: '#4ade80', icon: TrendingUp },
              { label: 'Total Expenses', value: fmt(pnl.total_expenses), color: '#f87171', icon: TrendingDown },
              { label: 'Net Profit', value: fmt(pnl.net_profit), color: '#5c78f5' },
              { label: 'Profit Margin', value: `${pnl.profit_margin}%`, color: '#f59e0b' }].map((s, i) => (
              <div key={i} className="card p-4 flex items-center gap-4">
                <div><p className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.label}</p><p className="text-xl font-bold mt-1" style={{ color: s.color }}>{s.value}</p></div>
              </div>
            ))}
          </div>
        </div>
      ) : view === 'trial-balance' && tb ? (
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--border)' }}>
            <p className="section-title">Trial Balance — {tb.client}</p>
            <span className={tb.balanced ? 'badge-success' : 'badge-danger'}>{tb.balanced ? 'Balanced' : 'Unbalanced'}</span>
          </div>
          <table className="w-full">
            <thead style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border)' }}>
              <tr><th className="table-th">Account</th><th className="table-th">Type</th><th className="table-th text-right">Debit (Dr)</th><th className="table-th text-right">Credit (Cr)</th></tr>
            </thead>
            <tbody>
              {tb.accounts.map((a, i) => (
                <tr key={i} className="table-row">
                  <td className="table-td font-medium">{a.account}</td>
                  <td className="table-td"><span className={a.type === 'Income' ? 'badge-success' : a.type === 'Expense' ? 'badge-danger' : a.type === 'Asset' ? 'badge-info' : 'badge-warning'}>{a.type}</span></td>
                  <td className="table-td text-right" style={{ color: a.debit > 0 ? '#60a5fa' : 'var(--text-muted)' }}>{a.debit > 0 ? fmt(a.debit) : '—'}</td>
                  <td className="table-td text-right" style={{ color: a.credit > 0 ? '#4ade80' : 'var(--text-muted)' }}>{a.credit > 0 ? fmt(a.credit) : '—'}</td>
                </tr>
              ))}
              <tr style={{ background: 'var(--bg-elevated)', borderTop: '2px solid var(--border)' }}>
                <td className="table-td font-bold" colSpan={2}>TOTAL</td>
                <td className="table-td text-right font-bold" style={{ color: '#60a5fa' }}>{fmt(tb.total_debit)}</td>
                <td className="table-td text-right font-bold" style={{ color: '#4ade80' }}>{fmt(tb.total_credit)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
"""

# ── GSTR2B Reconciliation Page ────────────────────────────────────────────
gstr2b_page = r"""import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, clientsAPI } from '../services/api';
import { Upload, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export default function GSTR2BPage() {
  const [client, setClient] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { data: clients = [] } = useQuery({ queryKey: ['clients'], queryFn: () => clientsAPI.list({ limit: 100 }) });

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !client) { setError('Select a client first'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      const r = await fetch(`/api/v1/extra/client/${client}/gstr2b-reconcile`, {
        method: 'POST', body: formData,
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Reconciliation failed');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  const fmt = n => '₹' + (n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  return (
    <div className="p-6 fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">GSTR-2B Reconciliation</h1><p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Match portal data against your purchase invoices</p></div>
      </div>

      <div className="card p-5 mb-5">
        <p className="section-title mb-4">Upload GSTR-2B JSON</p>
        <div className="flex gap-4 flex-wrap items-end">
          <div><label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Client</label>
            <select className="input-field w-56" value={client} onChange={e => setClient(e.target.value)}>
              <option value="">Select Client...</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.company_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>GSTR-2B JSON File</label>
            <label className="btn-primary flex items-center gap-2 text-sm cursor-pointer">
              <Upload size={14} /> {loading ? 'Reconciling...' : 'Upload GSTR-2B JSON'}
              <input type="file" accept=".json" className="hidden" onChange={handleUpload} disabled={!client || loading} />
            </label>
          </div>
        </div>
        {error && <p className="text-sm mt-3" style={{ color: 'var(--danger)' }}>{error}</p>}
        <div className="mt-3 p-3 rounded-lg text-xs" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
          Download GSTR-2B JSON from GST Portal → Return Filing → GSTR-2B → Download JSON
        </div>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            {[
              { label: 'Portal Invoices', value: result.total_portal_invoices, color: '#5c78f5' },
              { label: 'Matched', value: result.matched, color: '#22c55e' },
              { label: 'Amount Mismatch', value: result.amount_mismatch, color: '#f59e0b' },
              { label: 'Missing in Books', value: result.missing_in_books, color: '#ef4444' },
            ].map((s, i) => (
              <div key={i} className="card p-4 text-center">
                <p className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
              </div>
            ))}
          </div>

          <div className="card p-4 mb-4 flex items-center gap-3" style={{ background: 'rgba(34,197,94,0.06)', borderColor: 'rgba(34,197,94,0.3)' }}>
            <CheckCircle size={18} style={{ color: '#4ade80' }} />
            <p className="text-sm font-medium" style={{ color: '#4ade80' }}>ITC Available: {fmt(result.total_itc_available)}</p>
          </div>

          {result.unmatched_portal.length > 0 && (
            <div className="card overflow-hidden mb-4">
              <div className="p-4 border-b" style={{ borderColor: 'var(--border)' }}>
                <p className="section-title flex items-center gap-2"><AlertTriangle size={14} style={{ color: '#f59e0b' }} /> Missing in Books ({result.unmatched_portal.length})</p>
              </div>
              <table className="w-full">
                <thead style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border)' }}>
                  <tr><th className="table-th">Invoice #</th><th className="table-th">Vendor GSTIN</th><th className="table-th">Portal Amount</th><th className="table-th">Action</th></tr>
                </thead>
                <tbody>
                  {result.unmatched_portal.slice(0, 10).map((r, i) => (
                    <tr key={i} className="table-row">
                      <td className="table-td font-mono text-xs">{r.invoice_number}</td>
                      <td className="table-td font-mono text-xs">{r.vendor_gstin}</td>
                      <td className="table-td" style={{ color: '#f87171' }}>{fmt(r.portal_amount)}</td>
                      <td className="table-td"><span className="badge-warning">Add to Books</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.matched_records.length > 0 && (
            <div className="card overflow-hidden">
              <div className="p-4 border-b" style={{ borderColor: 'var(--border)' }}>
                <p className="section-title flex items-center gap-2"><CheckCircle size={14} style={{ color: '#4ade80' }} /> Matched Records ({result.matched_records.length})</p>
              </div>
              <table className="w-full">
                <thead style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border)' }}>
                  <tr><th className="table-th">Invoice #</th><th className="table-th">Books Amount</th><th className="table-th">Portal Amount</th><th className="table-th">Status</th></tr>
                </thead>
                <tbody>
                  {result.matched_records.slice(0, 10).map((r, i) => (
                    <tr key={i} className="table-row">
                      <td className="table-td font-mono text-xs">{r.invoice_number}</td>
                      <td className="table-td">{fmt(r.books_amount)}</td>
                      <td className="table-td">{fmt(r.portal_amount)}</td>
                      <td className="table-td"><span className={r.status === 'matched' ? 'badge-success' : 'badge-warning'}>{r.status === 'matched' ? 'Matched' : 'Amount Diff'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
"""

# ── Legal Research Page ───────────────────────────────────────────────────
legal_research_page = r"""import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { Search, BookOpen, Scale } from 'lucide-react';

const MATTER_TYPES = ['Civil','Criminal','Corporate','IP Trademark','Labour Employment','Family','Real Estate','Consumer','NCLT','Cheque Bounce','Property'];
const COURTS = ['All Courts','Supreme Court','High Court Delhi','High Court Bombay','High Court Madras','NCLT','Labour Court'];

export default function LegalResearchPage() {
  const [query, setQuery] = useState('');
  const [matterType, setMatterType] = useState('Civil');
  const [court, setCourt] = useState('All Courts');
  const [facts, setFacts] = useState('');
  const [tab, setTab] = useState('research');

  const researchMut = useMutation({ mutationFn: () => api.post('/law/research', { query, court_filter: court }).then(r => r.data) });
  const precedentMut = useMutation({ mutationFn: () => api.post('/law/precedent-search', { matter_type: matterType, facts, court }).then(r => r.data) });

  return (
    <div className="p-6 fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">Legal Research</h1><p className="text-sm" style={{ color: 'var(--text-secondary)' }}>AI-powered Indian case law research and precedent finder</p></div>
      </div>

      <div className="flex gap-2 mb-5">
        {['research', 'precedents'].map(t => (
          <button key={t} onClick={() => setTab(t)} className={tab === t ? 'btn-primary text-sm' : 'btn-ghost text-sm'}>
            {t === 'research' ? 'Case Law Research' : 'Precedent Finder'}
          </button>
        ))}
      </div>

      {tab === 'research' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-5">
            <p className="section-title mb-4 flex items-center gap-2"><Search size={15} />Research Query</p>
            <div className="space-y-3">
              <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Search Query</label>
                <textarea className="input-field" rows={3} value={query} onChange={e => setQuery(e.target.value)} placeholder="e.g. Section 138 NI Act cheque bounce liability..."/>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Court Filter</label>
                <select className="input-field" value={court} onChange={e => setCourt(e.target.value)}>{COURTS.map(c => <option key={c}>{c}</option>)}</select>
              </div>
              <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={() => researchMut.mutate()} disabled={!query || researchMut.isPending}>
                <Search size={14} />{researchMut.isPending ? 'Searching...' : 'Search Case Law'}
              </button>
            </div>
          </div>
          <div className="card p-5" style={{ minHeight: 400 }}>
            <p className="section-title mb-4 flex items-center gap-2"><BookOpen size={15} />Results</p>
            {researchMut.isPending ? (
              <div className="flex flex-col items-center justify-center h-48 gap-3">
                <div className="w-7 h-7 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--brand)' }} />
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Searching Indian case law...</p>
              </div>
            ) : researchMut.data ? (
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'Inter',sans-serif", fontSize: 13, lineHeight: 1.8, color: 'var(--text-secondary)', overflowY: 'auto', maxHeight: 500 }}>{researchMut.data.result}</pre>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 gap-2" style={{ color: 'var(--text-muted)' }}>
                <Scale size={28} style={{ opacity: 0.3 }} />
                <p className="text-sm">Enter a query to search Indian case law</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-5">
            <p className="section-title mb-4 flex items-center gap-2"><Scale size={15} />Find Precedents</p>
            <div className="space-y-3">
              <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Matter Type</label>
                <select className="input-field" value={matterType} onChange={e => setMatterType(e.target.value)}>{MATTER_TYPES.map(t => <option key={t}>{t}</option>)}</select>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Facts of the Case</label>
                <textarea className="input-field" rows={4} value={facts} onChange={e => setFacts(e.target.value)} placeholder="Briefly describe the facts of your case..."/>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Court</label>
                <select className="input-field" value={court} onChange={e => setCourt(e.target.value)}>{COURTS.map(c => <option key={c}>{c}</option>)}</select>
              </div>
              <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={() => precedentMut.mutate()} disabled={!facts || precedentMut.isPending}>
                <BookOpen size={14} />{precedentMut.isPending ? 'Finding...' : 'Find Precedents'}
              </button>
            </div>
          </div>
          <div className="card p-5" style={{ minHeight: 400 }}>
            <p className="section-title mb-4">Relevant Precedents</p>
            {precedentMut.isPending ? (
              <div className="flex flex-col items-center justify-center h-48 gap-3">
                <div className="w-7 h-7 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--brand)' }} />
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Finding relevant precedents...</p>
              </div>
            ) : precedentMut.data ? (
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'Inter',sans-serif", fontSize: 13, lineHeight: 1.8, color: 'var(--text-secondary)', overflowY: 'auto', maxHeight: 500 }}>{precedentMut.data.result}</pre>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 gap-2" style={{ color: 'var(--text-muted)' }}>
                <Scale size={28} style={{ opacity: 0.3 }} />
                <p className="text-sm">Enter case facts to find relevant precedents</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
"""

# ── Limitation Calculator Page ────────────────────────────────────────────
limitation_page = r"""import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { Clock, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const CASE_TYPES = [
  { value: 'civil', label: 'Civil Suit (General)' },
  { value: 'contract', label: 'Contract Breach' },
  { value: 'property', label: 'Property / Immovable' },
  { value: 'cheque_bounce', label: 'Cheque Bounce (NI Act 138)' },
  { value: 'consumer', label: 'Consumer Complaint' },
  { value: 'labour', label: 'Labour / Employment' },
  { value: 'tort', label: 'Tort / Damages' },
  { value: 'execution', label: 'Decree Execution' },
];

export default function LimitationPage() {
  const [form, setForm] = useState({ cause_of_action_date: '', case_type: 'civil' });
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));
  const mut = useMutation({ mutationFn: () => api.post('/extra/law/limitation-period', form).then(r => r.data) });
  const r = mut.data;

  return (
    <div className="p-6 fade-in-up">
      <div className="mb-6"><h1 className="page-title">Limitation Period Calculator</h1><p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Calculate filing deadlines under Limitation Act 1963</p></div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <p className="section-title mb-4 flex items-center gap-2"><Clock size={15} />Calculate Limitation</p>
          <div className="space-y-4">
            <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Case Type</label>
              <select className="input-field" value={form.case_type} onChange={set('case_type')}>
                {CASE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div><label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Date of Cause of Action *</label>
              <input type="date" className="input-field" value={form.cause_of_action_date} onChange={set('cause_of_action_date')}/>
            </div>
            <button className="btn-primary w-full" disabled={!form.cause_of_action_date || mut.isPending} onClick={() => mut.mutate()}>
              {mut.isPending ? 'Calculating...' : 'Calculate Limitation Period'}
            </button>
          </div>
        </div>

        <div>
          {r ? (
            <div className="space-y-4">
              <div className="card p-5" style={{
                background: r.is_expired ? 'rgba(239,68,68,0.06)' : r.is_urgent ? 'rgba(245,158,11,0.06)' : 'rgba(34,197,94,0.06)',
                borderColor: r.is_expired ? 'rgba(239,68,68,0.3)' : r.is_urgent ? 'rgba(245,158,11,0.3)' : 'rgba(34,197,94,0.3)',
              }}>
                <div className="flex items-center gap-3 mb-4">
                  {r.is_expired ? <XCircle size={24} style={{ color: '#f87171' }} />
                  : r.is_urgent ? <AlertTriangle size={24} style={{ color: '#fbbf24' }} />
                  : <CheckCircle size={24} style={{ color: '#4ade80' }} />}
                  <div>
                    <p className="font-bold text-lg" style={{ color: r.is_expired ? '#f87171' : r.is_urgent ? '#fbbf24' : '#4ade80' }}>{r.status}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{r.applicable_law}</p>
                  </div>
                </div>
                {[
                  ['Cause of Action', r.cause_of_action_date],
                  ['Limitation Period', r.limitation_period],
                  ['Last Date to File', r.expiry_date],
                  ['Days Remaining', r.is_expired ? `${Math.abs(r.days_remaining)} days OVERDUE` : `${r.days_remaining} days left`],
                ].map(([l, v]) => (
                  <div key={l} className="flex justify-between text-sm py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>{l}</span>
                    <span className="font-medium">{v}</span>
                  </div>
                ))}
              </div>
              {r.is_urgent && !r.is_expired && (
                <div className="card p-4" style={{ background: 'rgba(245,158,11,0.08)', borderColor: 'rgba(245,158,11,0.3)' }}>
                  <p className="text-sm font-medium" style={{ color: '#fbbf24' }}>Urgent: Less than 90 days remaining. File immediately.</p>
                </div>
              )}
              {r.is_expired && (
                <div className="card p-4" style={{ background: 'rgba(239,68,68,0.08)', borderColor: 'rgba(239,68,68,0.3)' }}>
                  <p className="text-sm font-medium" style={{ color: '#f87171' }}>Limitation expired. Consider filing for condonation of delay under Section 5 of Limitation Act.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="card p-10 text-center" style={{ color: 'var(--text-muted)' }}>
              <Clock size={32} className="mx-auto mb-2 opacity-20"/>
              Select case type and date to calculate
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"""

# Write all pages
files = {
    'TrialBalancePage.jsx': trial_balance_page,
    'GSTR2BPage.jsx': gstr2b_page,
    'LegalResearchPage.jsx': legal_research_page,
    'LimitationPage.jsx': limitation_page,
}

for name, content in files.items():
    path = os.path.join(PAGES, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created: {name}')

print('\nAll new frontend pages created!')
print('Now update App.js to add the new routes.')
