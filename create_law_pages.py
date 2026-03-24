# -*- coding: utf-8 -*-
import os

PAGES = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\pages'

# ── MattersPage.jsx ───────────────────────────────────────────────────────
matters = r"""import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Shield, Plus, X, Calendar, ChevronRight } from 'lucide-react';

const lawAPI = {
  matters: (s) => api.get('/law/matters', { params: s ? { status: s } : {} }).then(r => r.data),
  getMatter: (id) => api.get(`/law/matters/${id}`).then(r => r.data),
  createMatter: (d) => api.post('/law/matters', d).then(r => r.data),
  updateMatter: (id, d) => api.put(`/law/matters/${id}`, d).then(r => r.data),
  deleteMatter: (id) => api.delete(`/law/matters/${id}`).then(r => r.data),
};

const STATUS_COLORS = {
  urgent:'badge-danger', active:'badge-warning',
  discovery:'badge-info', pending:'badge-default', closed:'badge-success'
};
const AREAS = ['Civil','Criminal','Corporate','IP Trademark','Labour Employment','Family','Real Estate','Consumer','NCLT','Tax'];
const COURTS = ['Supreme Court of India','High Court Delhi','High Court Bombay','High Court Madras','District Court','NCLT Mumbai','NCLT Delhi','IP Appellate Board','Labour Court','Consumer Forum','RERA Authority'];

function AddModal({ onClose }) {
  const qc = useQueryClient();
  const [f, setF] = useState({ title:'', practice_area:'Civil', court:'', client_name:'', opposite_party:'', brief:'', status:'pending', relief_sought:'' });
  const set = k => e => setF(p => ({ ...p, [k]: e.target.value }));
  const mut = useMutation({ mutationFn: () => lawAPI.createMatter(f), onSuccess: () => { qc.invalidateQueries(['matters']); onClose(); } });
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{background:'rgba(0,0,0,0.75)'}}>
      <div className="card w-full max-w-2xl max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b" style={{borderColor:'var(--border)'}}>
          <p className="section-title">New Legal Matter</p>
          <button onClick={onClose} style={{color:'var(--text-muted)'}}><X size={18}/></button>
        </div>
        <div className="p-5 space-y-4">
          <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Case Title *</label><input className="input-field" value={f.title} onChange={set('title')} placeholder="e.g. Ramesh Gupta vs ABC Builders"/></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Practice Area</label><select className="input-field" value={f.practice_area} onChange={set('practice_area')}>{AREAS.map(a=><option key={a}>{a}</option>)}</select></div>
            <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Status</label><select className="input-field" value={f.status} onChange={set('status')}><option value="pending">Pending</option><option value="active">Active</option><option value="urgent">Urgent</option><option value="discovery">Discovery</option></select></div>
            <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Client Name</label><input className="input-field" value={f.client_name} onChange={set('client_name')} placeholder="Party A"/></div>
            <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Opposite Party</label><input className="input-field" value={f.opposite_party} onChange={set('opposite_party')} placeholder="Respondent"/></div>
          </div>
          <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Court</label><select className="input-field" value={f.court} onChange={set('court')}><option value="">Select...</option>{COURTS.map(c=><option key={c}>{c}</option>)}</select></div>
          <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Brief</label><textarea className="input-field" rows={3} value={f.brief} onChange={set('brief')} placeholder="Description..."/></div>
          <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Relief Sought</label><input className="input-field" value={f.relief_sought} onChange={set('relief_sought')} placeholder="e.g. Injunction + damages"/></div>
          {mut.error && <p className="text-xs" style={{color:'var(--danger)'}}>{mut.error.response?.data?.detail}</p>}
          <div className="flex gap-3"><button className="btn-ghost flex-1" onClick={onClose}>Cancel</button><button className="btn-primary flex-1" disabled={!f.title||mut.isPending} onClick={()=>mut.mutate()}>{mut.isPending?'Creating...':'Create Matter'}</button></div>
        </div>
      </div>
    </div>
  );
}

export default function MattersPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState(null);
  const { data: matters=[], isLoading } = useQuery({ queryKey:['matters',filter], queryFn:()=>lawAPI.matters(filter) });
  const { data: detail } = useQuery({ queryKey:['matter',selected], queryFn:()=>lawAPI.getMatter(selected), enabled:!!selected });
  const updateMut = useMutation({ mutationFn:({id,data})=>lawAPI.updateMatter(id,data), onSuccess:()=>qc.invalidateQueries(['matters']) });
  const deleteMut = useMutation({ mutationFn:(id)=>lawAPI.deleteMatter(id), onSuccess:()=>{ qc.invalidateQueries(['matters']); setSelected(null); } });

  return (
    <div className="p-6 fade-in-up">
      {showAdd && <AddModal onClose={()=>setShowAdd(false)}/>}
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">Matters & Cases</h1><p className="text-sm" style={{color:'var(--text-secondary)'}}>Manage all legal matters</p></div>
        <button className="btn-primary flex items-center gap-2 text-sm" onClick={()=>setShowAdd(true)}><Plus size={15}/>New Matter</button>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-5">
        {[{l:'Urgent',v:matters.filter(m=>m.status==='urgent').length,c:'#ef4444'},{l:'Active',v:matters.filter(m=>m.status==='active').length,c:'#f59e0b'},{l:'Total',v:matters.length,c:'#5c78f5'}].map((s,i)=>(
          <div key={i} className="card p-4 text-center"><p className="text-2xl font-bold" style={{color:s.c}}>{s.v}</p><p className="text-xs mt-1" style={{color:'var(--text-muted)'}}>{s.l}</p></div>
        ))}
      </div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {['','urgent','active','discovery','pending','closed'].map(s=>(
          <button key={s} onClick={()=>setFilter(s)} className={filter===s?'btn-primary text-sm':'btn-ghost text-sm'}>{s||'All'}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card overflow-hidden">
          <div className="p-4 border-b" style={{borderColor:'var(--border)'}}><p className="section-title">Matters ({matters.length})</p></div>
          {isLoading ? <div className="p-4 space-y-2">{Array(4).fill(0).map((_,i)=><div key={i} className="skeleton h-16 rounded-lg"/>)}</div>
          : matters.length===0 ? <div className="p-10 text-center" style={{color:'var(--text-muted)'}}>No matters yet. Click New Matter to add one.</div>
          : matters.map(m=>(
            <div key={m.id} className="flex items-center gap-3 p-4 border-b cursor-pointer hover:bg-white/5 transition-colors" style={{borderColor:'var(--border)',background:selected===m.id?'rgba(92,120,245,0.08)':''}} onClick={()=>setSelected(m.id)}>
              <div style={{flex:1,minWidth:0}}>
                <p className="font-medium text-sm truncate">{m.title}</p>
                <p className="text-xs mt-0.5" style={{color:'var(--text-muted)'}}>{m.matter_number} · {m.practice_area} · {m.client_name}</p>
                {m.next_hearing && <p className="text-xs mt-0.5 flex items-center gap-1" style={{color:'var(--text-muted)'}}><Calendar size={10}/> {new Date(m.next_hearing).toLocaleDateString('en-IN')}</p>}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={STATUS_COLORS[m.status]||'badge-default'}>{m.status}</span>
                <ChevronRight size={14} style={{color:'var(--text-muted)'}}/>
              </div>
            </div>
          ))}
        </div>
        <div>
          {!selected ? <div className="card p-10 text-center" style={{color:'var(--text-muted)'}}><Shield size={32} className="mx-auto mb-2 opacity-20"/>Select a matter to view details</div>
          : detail ? (
            <div className="card overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b" style={{borderColor:'var(--border)'}}>
                <div><p className="font-semibold text-sm">{detail.matter_number}</p><p className="text-xs" style={{color:'var(--text-muted)'}}>{detail.practice_area} · {detail.court}</p></div>
                <div className="flex gap-2">
                  <select className="input-field text-xs py-1" style={{width:120}} value={detail.status} onChange={e=>updateMut.mutate({id:detail.id,data:{status:e.target.value}})}>
                    {['pending','active','urgent','discovery','closed'].map(s=><option key={s}>{s}</option>)}
                  </select>
                  <button className="btn-ghost text-xs py-1" style={{color:'var(--danger)'}} onClick={()=>deleteMut.mutate(detail.id)}>Delete</button>
                </div>
              </div>
              <div className="p-4 space-y-3">
                <p className="font-semibold">{detail.title}</p>
                {[['Client',detail.client_name],['Opposite Party',detail.opposite_party],['Relief Sought',detail.relief_sought]].filter(r=>r[1]).map(([l,v])=>(
                  <div key={l} className="flex gap-2"><p className="text-xs font-medium w-28 flex-shrink-0" style={{color:'var(--text-muted)'}}>{l}</p><p className="text-sm">{v}</p></div>
                ))}
                {detail.brief && <div className="p-3 rounded-lg text-sm" style={{background:'var(--bg-elevated)',border:'1px solid var(--border)',color:'var(--text-secondary)'}}>{detail.brief}</div>}
                {detail.hearings?.length>0 && (
                  <div>
                    <p className="text-xs font-semibold mb-2" style={{color:'var(--text-muted)'}}>HEARINGS</p>
                    {detail.hearings.map(h=>(
                      <div key={h.id} className="flex items-center gap-2 p-2 rounded text-xs mb-1" style={{background:'var(--bg-elevated)'}}>
                        <Calendar size={12} style={{color:'var(--brand)'}}/><span className="font-medium">{new Date(h.hearing_date).toLocaleDateString('en-IN')}</span>
                        <span style={{color:'var(--text-muted)'}}>{h.purpose}</span>
                        {h.is_attended && <span className="badge-success ml-auto">Attended</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
"""

# ── CourtCalendarPage.jsx ─────────────────────────────────────────────────
calendar = r"""import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Calendar, Clock, CheckCircle, Plus, X } from 'lucide-react';

export default function CourtCalendarPage() {
  const qc = useQueryClient();
  const [days, setDays] = useState(30);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ matter_id:'', hearing_date:'', hearing_time:'10:30', court:'', purpose:'', notes:'' });
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}));

  const { data: hearings=[], isLoading } = useQuery({ queryKey:['hearings',days], queryFn:()=>api.get('/law/hearings',{params:{days}}).then(r=>r.data) });
  const { data: matters=[] } = useQuery({ queryKey:['matters'], queryFn:()=>api.get('/law/matters').then(r=>r.data) });

  const addMut = useMutation({
    mutationFn: ()=>api.post('/law/hearings',{...form,matter_id:parseInt(form.matter_id)}).then(r=>r.data),
    onSuccess: ()=>{ qc.invalidateQueries(['hearings']); setShowAdd(false); setForm({matter_id:'',hearing_date:'',hearing_time:'10:30',court:'',purpose:'',notes:''}); }
  });
  const attendMut = useMutation({ mutationFn:(id)=>api.put(`/law/hearings/${id}/attend`,{}).then(r=>r.data), onSuccess:()=>qc.invalidateQueries(['hearings']) });

  const today = hearings.filter(h=>h.is_today);
  const upcoming = hearings.filter(h=>!h.is_today);

  return (
    <div className="p-6 fade-in-up">
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{background:'rgba(0,0,0,0.75)'}}>
          <div className="card w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b" style={{borderColor:'var(--border)'}}>
              <p className="section-title">Add Court Hearing</p>
              <button onClick={()=>setShowAdd(false)} style={{color:'var(--text-muted)'}}><X size={18}/></button>
            </div>
            <div className="p-5 space-y-4">
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Matter *</label>
                <select className="input-field" value={form.matter_id} onChange={set('matter_id')}><option value="">Select...</option>{matters.map(m=><option key={m.id} value={m.id}>{m.matter_number} - {m.title}</option>)}</select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Date *</label><input type="date" className="input-field" value={form.hearing_date} onChange={set('hearing_date')}/></div>
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Time</label><input type="time" className="input-field" value={form.hearing_time} onChange={set('hearing_time')}/></div>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Court</label><input className="input-field" placeholder="e.g. High Court Delhi - Court 5" value={form.court} onChange={set('court')}/></div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Purpose</label><input className="input-field" placeholder="e.g. Final Arguments" value={form.purpose} onChange={set('purpose')}/></div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Notes</label><textarea className="input-field" rows={2} value={form.notes} onChange={set('notes')}/></div>
              <div className="flex gap-3"><button className="btn-ghost flex-1" onClick={()=>setShowAdd(false)}>Cancel</button><button className="btn-primary flex-1" disabled={!form.matter_id||!form.hearing_date||addMut.isPending} onClick={()=>addMut.mutate()}>{addMut.isPending?'Adding...':'Add Hearing'}</button></div>
            </div>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">Court Calendar</h1><p className="text-sm" style={{color:'var(--text-secondary)'}}>Upcoming hearings and deadlines</p></div>
        <div className="flex gap-3">
          <select className="input-field w-36" value={days} onChange={e=>setDays(+e.target.value)}><option value={7}>Next 7 days</option><option value={14}>Next 14 days</option><option value={30}>Next 30 days</option><option value={60}>Next 60 days</option></select>
          <button className="btn-primary flex items-center gap-2 text-sm" onClick={()=>setShowAdd(true)}><Plus size={15}/>Add Hearing</button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="card p-4 text-center"><p className="text-2xl font-bold" style={{color:'#ef4444'}}>{today.length}</p><p className="text-xs mt-1" style={{color:'var(--text-muted)'}}>Today</p></div>
        <div className="card p-4 text-center"><p className="text-2xl font-bold" style={{color:'#f59e0b'}}>{hearings.filter(h=>h.days_left<=7&&!h.is_today).length}</p><p className="text-xs mt-1" style={{color:'var(--text-muted)'}}>This Week</p></div>
        <div className="card p-4 text-center"><p className="text-2xl font-bold">{hearings.length}</p><p className="text-xs mt-1" style={{color:'var(--text-muted)'}}>Total Upcoming</p></div>
      </div>
      {today.length>0 && (
        <div className="card overflow-hidden mb-4">
          <div className="p-3 border-b" style={{borderColor:'var(--border)',background:'rgba(239,68,68,0.08)'}}><p className="text-sm font-semibold" style={{color:'#f87171'}}>Today</p></div>
          {today.map(h=><HRow key={h.id} h={h} onAttend={()=>attendMut.mutate(h.id)}/>)}
        </div>
      )}
      <div className="card overflow-hidden">
        <div className="p-4 border-b" style={{borderColor:'var(--border)'}}><p className="section-title">Upcoming ({upcoming.length})</p></div>
        {isLoading ? <div className="p-4 space-y-2">{Array(3).fill(0).map((_,i)=><div key={i} className="skeleton h-14 rounded"/>)}</div>
        : upcoming.length===0 ? <div className="p-10 text-center" style={{color:'var(--text-muted)'}}><Calendar size={28} className="mx-auto mb-2 opacity-20"/>No upcoming hearings</div>
        : upcoming.map(h=><HRow key={h.id} h={h} onAttend={()=>attendMut.mutate(h.id)}/>)}
      </div>
    </div>
  );
}

function HRow({h,onAttend}){
  const col = h.is_today?'#ef4444':h.is_urgent?'#f59e0b':'#22c55e';
  const badge = h.is_today?'badge-danger':h.is_urgent?'badge-warning':'badge-success';
  return (
    <div className="flex items-center gap-3 p-4 border-b hover:bg-white/5 transition-colors" style={{borderColor:'var(--border)'}}>
      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{background:col}}/>
      <div style={{flex:1,minWidth:0}}>
        <p className="font-medium text-sm">{h.client_name} - {h.court}</p>
        <p className="text-xs" style={{color:'var(--text-muted)'}}>{h.matter_number} · {h.purpose}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {h.hearing_time && <span className="text-xs flex items-center gap-1" style={{color:'var(--text-muted)'}}><Clock size={10}/>{h.hearing_time}</span>}
        <span className={badge}>{h.is_today?'Today':`${h.days_left}d`}</span>
        {!h.is_attended ? <button className="btn-ghost text-xs py-1" onClick={onAttend}>Mark Attended</button>
        : <span className="badge-success flex items-center gap-1"><CheckCircle size={10}/>Done</span>}
      </div>
    </div>
  );
}
"""

# ── LegalDraftingPage.jsx ─────────────────────────────────────────────────
drafting = r"""import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { Sparkles, Download, Clock } from 'lucide-react';

const DOC_TYPES = ['Legal Notice','Service Agreement','NDA','Demand Notice','Legal Opinion','Plaint','Affidavit','Rent Agreement','Employment Contract','Power of Attorney'];
const COURTS = ['Delhi High Court','Bombay High Court','Madras High Court','NCLT Mumbai','District Court','Consumer Forum','RERA Authority','Labour Court'];

export default function LegalDraftingPage() {
  const [form, setForm] = useState({ doc_type:'Legal Notice', client_name:'', opposite_party:'', subject:'', jurisdiction:'Delhi High Court', relief:'', matter_id:null });
  const [doc, setDoc] = useState(null);
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}));

  const { data: drafts=[] } = useQuery({ queryKey:['drafts'], queryFn:()=>api.get('/law/drafts').then(r=>r.data) });
  const { data: matters=[] } = useQuery({ queryKey:['matters'], queryFn:()=>api.get('/law/matters').then(r=>r.data) });

  const genMut = useMutation({ mutationFn:()=>api.post('/law/draft',form).then(r=>r.data), onSuccess:(d)=>setDoc(d) });

  const download = () => {
    if(!doc) return;
    const b = new Blob([doc.content],{type:'text/plain'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = doc.title+'.txt';
    a.click();
  };

  return (
    <div className="p-6 fade-in-up">
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">AI Legal Drafting</h1><p className="text-sm" style={{color:'var(--text-secondary)'}}>Generate complete legal documents with GPT-4o</p></div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="card p-5">
            <p className="section-title mb-4 flex items-center gap-2"><Sparkles size={16} style={{color:'var(--brand)'}}/>Document Details</p>
            <div className="space-y-3">
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Document Type</label><select className="input-field" value={form.doc_type} onChange={set('doc_type')}>{DOC_TYPES.map(t=><option key={t}>{t}</option>)}</select></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Client / Party A *</label><input className="input-field" placeholder="Full name" value={form.client_name} onChange={set('client_name')}/></div>
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Opposite Party</label><input className="input-field" placeholder="Respondent" value={form.opposite_party} onChange={set('opposite_party')}/></div>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Matter / Subject *</label><textarea className="input-field" rows={3} placeholder="Describe the matter..." value={form.subject} onChange={set('subject')}/></div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Jurisdiction</label><select className="input-field" value={form.jurisdiction} onChange={set('jurisdiction')}>{COURTS.map(c=><option key={c}>{c}</option>)}</select></div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Relief Sought</label><input className="input-field" placeholder="e.g. Refund + interest" value={form.relief} onChange={set('relief')}/></div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Link to Matter</label>
                <select className="input-field" value={form.matter_id||''} onChange={e=>setForm(f=>({...f,matter_id:e.target.value||null}))}>
                  <option value="">None</option>{matters.map(m=><option key={m.id} value={m.id}>{m.matter_number} - {m.title}</option>)}
                </select>
              </div>
              <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={()=>genMut.mutate()} disabled={!form.client_name||!form.subject||genMut.isPending}>
                <Sparkles size={15}/>{genMut.isPending?'Generating with AI...':'Generate Document'}
              </button>
            </div>
          </div>
          {drafts.length>0 && (
            <div className="card overflow-hidden">
              <div className="p-4 border-b flex items-center gap-2" style={{borderColor:'var(--border)'}}><Clock size={14} style={{color:'var(--text-muted)'}}/><p className="section-title text-sm">Recent Drafts</p></div>
              {drafts.slice(0,5).map(d=>(
                <div key={d.id} className="flex items-center gap-3 p-3 border-b cursor-pointer hover:bg-white/5" style={{borderColor:'var(--border)'}} onClick={()=>api.get(`/law/drafts/${d.id}`).then(r=>setDoc(r.data))}>
                  <div style={{flex:1,minWidth:0}}><p className="text-xs font-medium truncate">{d.title}</p><p className="text-xs" style={{color:'var(--text-muted)'}}>{d.doc_type} · {new Date(d.created_at).toLocaleDateString('en-IN')}</p></div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card overflow-hidden" style={{minHeight:500}}>
          <div className="flex items-center justify-between p-4 border-b" style={{borderColor:'var(--border)'}}>
            <p className="section-title">Generated Document</p>
            {doc && <button className="btn-ghost text-xs py-1 flex items-center gap-1" onClick={download}><Download size={12}/>Download</button>}
          </div>
          <div className="p-4" style={{maxHeight:700,overflowY:'auto'}}>
            {genMut.isPending ? (
              <div className="flex flex-col items-center justify-center h-64 gap-3">
                <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{borderColor:'var(--brand)'}}/>
                <p className="text-sm" style={{color:'var(--text-secondary)'}}>AI is generating your document...</p>
              </div>
            ) : doc ? (
              <pre style={{whiteSpace:'pre-wrap',fontFamily:"'Inter',sans-serif",fontSize:13,lineHeight:1.9,color:'var(--text-secondary)'}}>{doc.content}</pre>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 gap-3">
                <Sparkles size={32} style={{color:'var(--text-muted)',opacity:0.3}}/>
                <p className="text-sm" style={{color:'var(--text-muted)'}}>Fill the form and click Generate</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
"""

# ── LegalBillingPage.jsx ──────────────────────────────────────────────────
billing = r"""import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Plus, X, CheckCircle } from 'lucide-react';

export default function LegalBillingPage() {
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [filterMatter, setFilterMatter] = useState('');
  const [form, setForm] = useState({ matter_id:'', entry_date:new Date().toISOString().slice(0,10), hours:'', rate_per_hour:5000, description:'' });
  const set = k => e => setForm(f=>({...f,[k]:e.target.value}));

  const { data: entries=[], isLoading } = useQuery({ queryKey:['time-entries',filterMatter], queryFn:()=>api.get('/law/time-entries',{params:filterMatter?{matter_id:filterMatter}:{}}).then(r=>r.data) });
  const { data: summary } = useQuery({ queryKey:['billing-summary'], queryFn:()=>api.get('/law/billing-summary').then(r=>r.data) });
  const { data: matters=[] } = useQuery({ queryKey:['matters'], queryFn:()=>api.get('/law/matters').then(r=>r.data) });

  const addMut = useMutation({
    mutationFn:()=>api.post('/law/time-entries',{...form,matter_id:parseInt(form.matter_id),hours:parseFloat(form.hours),rate_per_hour:parseFloat(form.rate_per_hour)}).then(r=>r.data),
    onSuccess:()=>{ qc.invalidateQueries(['time-entries']); qc.invalidateQueries(['billing-summary']); setShowAdd(false); setForm({matter_id:'',entry_date:new Date().toISOString().slice(0,10),hours:'',rate_per_hour:5000,description:''}); }
  });
  const billMut = useMutation({ mutationFn:(id)=>api.put(`/law/time-entries/${id}/bill`).then(r=>r.data), onSuccess:()=>{ qc.invalidateQueries(['time-entries']); qc.invalidateQueries(['billing-summary']); } });

  const fmt = (n) => '₹' + (n||0).toLocaleString('en-IN');

  return (
    <div className="p-6 fade-in-up">
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{background:'rgba(0,0,0,0.75)'}}>
          <div className="card w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b" style={{borderColor:'var(--border)'}}>
              <p className="section-title">Log Time Entry</p>
              <button onClick={()=>setShowAdd(false)} style={{color:'var(--text-muted)'}}><X size={18}/></button>
            </div>
            <div className="p-5 space-y-4">
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Matter *</label>
                <select className="input-field" value={form.matter_id} onChange={set('matter_id')}><option value="">Select...</option>{matters.map(m=><option key={m.id} value={m.id}>{m.matter_number} - {m.title}</option>)}</select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Date</label><input type="date" className="input-field" value={form.entry_date} onChange={set('entry_date')}/></div>
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Hours *</label><input type="number" className="input-field" placeholder="e.g. 2.5" min="0.5" step="0.5" value={form.hours} onChange={set('hours')}/></div>
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Rate/Hour (Rs)</label><input type="number" className="input-field" value={form.rate_per_hour} onChange={set('rate_per_hour')}/></div>
                <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Amount</label><input className="input-field" readOnly value={form.hours&&form.rate_per_hour?fmt(parseFloat(form.hours)*parseFloat(form.rate_per_hour)):'--'}/></div>
              </div>
              <div><label className="block text-xs font-medium mb-1" style={{color:'var(--text-secondary)'}}>Description</label><textarea className="input-field" rows={2} placeholder="e.g. Court appearance, research..." value={form.description} onChange={set('description')}/></div>
              <div className="flex gap-3"><button className="btn-ghost flex-1" onClick={()=>setShowAdd(false)}>Cancel</button><button className="btn-primary flex-1" disabled={!form.matter_id||!form.hours||addMut.isPending} onClick={()=>addMut.mutate()}>{addMut.isPending?'Logging...':'Log Time'}</button></div>
            </div>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="page-title">Legal Billing</h1><p className="text-sm" style={{color:'var(--text-secondary)'}}>Track billable hours and generate invoices</p></div>
        <button className="btn-primary flex items-center gap-2 text-sm" onClick={()=>setShowAdd(true)}><Plus size={15}/>Log Time</button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {[{l:'Total Billed',v:fmt(summary?.total_billed),c:'#22c55e'},{l:'Unbilled',v:fmt(summary?.total_unbilled),c:'#f59e0b'},{l:'Total Hours',v:`${summary?.total_hours||0}h`,c:'#5c78f5'},{l:'Entries',v:summary?.total_entries||0,c:'var(--text-primary)'}].map((s,i)=>(
          <div key={i} className="card p-4"><p className="text-xs font-medium mb-1" style={{color:'var(--text-muted)'}}>{s.l}</p><p className="text-xl font-bold" style={{color:s.c}}>{s.v}</p></div>
        ))}
      </div>
      <div className="flex gap-3 mb-4">
        <select className="input-field w-56" value={filterMatter} onChange={e=>setFilterMatter(e.target.value)}>
          <option value="">All Matters</option>{matters.map(m=><option key={m.id} value={m.id}>{m.matter_number}</option>)}
        </select>
      </div>
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead style={{background:'var(--bg-elevated)',borderBottom:'1px solid var(--border)'}}>
            <tr><th className="table-th">Date</th><th className="table-th hidden md:table-cell">Matter</th><th className="table-th">Description</th><th className="table-th">Hours</th><th className="table-th">Amount</th><th className="table-th">Status</th></tr>
          </thead>
          <tbody>
            {isLoading ? <tr><td colSpan={6} className="table-td text-center py-8" style={{color:'var(--text-muted)'}}>Loading...</td></tr>
            : entries.length===0 ? <tr><td colSpan={6} className="table-td text-center py-10" style={{color:'var(--text-muted)'}}>No time entries. Click Log Time to add one.</td></tr>
            : entries.map(e=>(
              <tr key={e.id} className="table-row">
                <td className="table-td" style={{color:'var(--text-secondary)'}}>{new Date(e.entry_date).toLocaleDateString('en-IN')}</td>
                <td className="table-td hidden md:table-cell"><p className="text-xs font-mono">{e.matter_number}</p></td>
                <td className="table-td" style={{color:'var(--text-secondary)',maxWidth:200}}><p className="text-xs truncate">{e.description||'--'}</p></td>
                <td className="table-td font-medium">{e.hours}h</td>
                <td className="table-td font-medium" style={{color:'#4ade80'}}>{fmt(e.amount)}</td>
                <td className="table-td">
                  {e.is_billed ? <span className="badge-success flex items-center gap-1 w-fit"><CheckCircle size={10}/>Billed</span>
                  : <button className="btn-ghost text-xs py-1" onClick={()=>billMut.mutate(e.id)}>Mark Billed</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
"""

# Write all files
files = {
    'MattersPage.jsx': matters,
    'CourtCalendarPage.jsx': calendar,
    'LegalDraftingPage.jsx': drafting,
    'LegalBillingPage.jsx': billing,
}

for name, content in files.items():
    path = os.path.join(PAGES, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created: {path}')

print('\nAll 4 law firm pages created successfully!')
print('Frontend will auto-reload.')