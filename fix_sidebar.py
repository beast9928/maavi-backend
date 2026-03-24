import re

path = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\components\layout\AppLayout.jsx'
content = open(path, encoding='utf-8').read()

# Fix imports
if 'AlertTriangle' not in content:
    content = content.replace(
        "} from 'lucide-react';",
        ", AlertTriangle, UserPlus, Settings, Calendar, Clock, Building2 } from 'lucide-react';"
    )

# Fix NAV array - replace entire NAV
old_nav_start = 'const NAV = ['
nav_end = '];'

new_nav = """const NAV = [
  { to: '/dashboard',     icon: LayoutDashboard,  label: 'Dashboard',   section: 'CA Modules' },
  { to: '/clients',       icon: Users,             label: 'Clients',     section: '' },
  { to: '/invoices',      icon: FileText,          label: 'Invoices',    section: '' },
  { to: '/documents',     icon: FolderOpen,        label: 'Documents',   section: '' },
  { to: '/compliance',    icon: ShieldCheck,       label: 'Compliance',  section: '' },
  { to: '/reports',       icon: BarChart3,         label: 'Reports',     section: '' },
  { to: '/matters',       icon: Building2,         label: 'Matters',     section: 'Law Modules' },
  { to: '/court-calendar',icon: Calendar,          label: 'Court Cal.',  section: '' },
  { to: '/drafting',      icon: FileText,          label: 'AI Drafting', section: '' },
  { to: '/legal-billing', icon: Clock,             label: 'Billing',     section: '' },
  { to: '/chat',          icon: MessageSquareText, label: 'AI Chat',     section: 'General' },
  { to: '/team',          icon: UserPlus,          label: 'Team',        section: '' },
  { to: '/settings',      icon: Settings,          label: 'Settings',    section: '' },
];"""

# Find and replace the NAV array
import re
content = re.sub(r'const NAV = \[.*?\];', new_nav, content, flags=re.DOTALL)

open(path, 'w', encoding='utf-8').write(content)
print('Sidebar updated with all pages!')
print('Check http://localhost:3000 now')