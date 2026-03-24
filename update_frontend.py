import os

FRONT = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src'
app_js = FRONT + r'\App.js'
layout = FRONT + r'\components\layout\AppLayout.jsx'

# Update App.js
c = open(app_js, encoding='utf-8').read()
if 'MattersPage' not in c:
    imp = "import MattersPage from './pages/MattersPage';\nimport LegalDraftingPage from './pages/LegalDraftingPage';\nimport CourtCalendarPage from './pages/CourtCalendarPage';\nimport LegalBillingPage from './pages/LegalBillingPage';\n"
    c = imp + c
    new_routes = '          <Route path="matters" element={<MattersPage />} />\n          <Route path="court-calendar" element={<CourtCalendarPage />} />\n          <Route path="drafting" element={<LegalDraftingPage />} />\n          <Route path="legal-billing" element={<LegalBillingPage />} />\n'
    c = c.replace('          <Route path="settings"', new_routes + '          <Route path="settings"')
    open(app_js, 'w', encoding='utf-8').write(c)
    print('App.js updated')
else:
    print('App.js already done')

# Update AppLayout
c = open(layout, encoding='utf-8').read()
if '/matters' not in c:
    nav = "  { to: '/matters',        icon: Shield,        label: 'Matters'       },\n  { to: '/court-calendar', icon: Calendar,      label: 'Court Cal.'    },\n  { to: '/drafting',       icon: FileText,      label: 'AI Drafting'   },\n  { to: '/legal-billing',  icon: Clock,         label: 'Legal Billing' },\n"
    c = c.replace("  { to: '/settings'", nav + "  { to: '/settings'")
    c = c.replace('MessageSquareText, LogOut', 'MessageSquareText, LogOut, Calendar, Clock')
    open(layout, 'w', encoding='utf-8').write(c)
    print('AppLayout updated')
else:
    print('AppLayout already done')

print('Done!')