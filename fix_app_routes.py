app_js = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\App.js'
content = open(app_js, encoding='utf-8').read()

new_imports = """import GSTPage from './pages/GSTPage';
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
"""

new_routes = """          <Route path="gst" element={<GSTPage />} />
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
"""

# Add imports at top
content = new_imports + content

# Add routes before the wildcard route
content = content.replace(
    '          <Route path="*" element={<Navigate to="/dashboard" replace />} />',
    new_routes + '          <Route path="*" element={<Navigate to="/dashboard" replace />} />'
)

open(app_js, 'w', encoding='utf-8').write(content)
print('App.js fixed with all routes!')
print('Frontend will auto-reload in 10 seconds.')