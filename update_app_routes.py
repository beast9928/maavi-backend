# -*- coding: utf-8 -*-
import re

APP = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\App.js'
LAYOUT = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\components\layout\AppLayout.jsx'

# Update App.js
content = open(APP, encoding='utf-8').read()
if 'TrialBalancePage' not in content:
    new_imports = """import TrialBalancePage from './pages/TrialBalancePage';
import GSTR2BPage from './pages/GSTR2BPage';
import LegalResearchPage from './pages/LegalResearchPage';
import LimitationPage from './pages/LimitationPage';
"""
    content = new_imports + content
    new_routes = """          <Route path="trial-balance" element={<TrialBalancePage />} />
          <Route path="gstr2b" element={<GSTR2BPage />} />
          <Route path="legal-research" element={<LegalResearchPage />} />
          <Route path="limitation" element={<LimitationPage />} />
"""
    content = content.replace('          <Route path="settings"', new_routes + '          <Route path="settings"')
    open(APP, 'w', encoding='utf-8').write(content)
    print('App.js updated with new routes')
else:
    print('App.js already has new routes')

# Update AppLayout - add new nav items
content = open(LAYOUT, encoding='utf-8').read()
if 'trial-balance' not in content:
    new_ca_items = """  { to: '/trial-balance',  icon: BarChart3,         label: 'Fin. Statements'},
  { to: '/gstr2b',         icon: FileText,          label: 'GSTR-2B Recon.'  },
"""
    new_law_items = """  { to: '/legal-research',  icon: Search,           label: 'Legal Research'  },
  { to: '/limitation',      icon: Clock,            label: 'Limitation Calc.' },
"""
    # Add after reports in CA section
    content = content.replace(
        "  { to: '/matters',",
        new_ca_items + "  { to: '/matters',"
    )
    # Add after billing in law section
    content = content.replace(
        "  { to: '/chat',",
        new_law_items + "  { to: '/chat',"
    )
    # Add Search to imports
    content = content.replace(
        'MessageSquareText, LogOut, Calendar, Clock, Menu, X, Bell, Sparkles, Building2, AlertTriangle, UserPlus, Settings',
        'MessageSquareText, LogOut, Calendar, Clock, Menu, X, Bell, Sparkles, Building2, AlertTriangle, UserPlus, Settings, Search'
    )
    open(LAYOUT, 'w', encoding='utf-8').write(content)
    print('AppLayout updated with new nav items')
else:
    print('AppLayout already has new items')

print('\nDone! Frontend will auto-reload.')
print('New pages available:')
print('  CA: /trial-balance, /gstr2b')
print('  Law: /legal-research, /limitation')
