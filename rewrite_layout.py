# -*- coding: utf-8 -*-
import re

path = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\components\layout\AppLayout.jsx'

content = open(path, encoding='utf-8').read()

# Step 1: Clean ALL lucide imports - find the full import block and replace it
content = re.sub(
    r"import \{[^}]+\} from 'lucide-react';",
    "import { LayoutDashboard, Users, FileText, FolderOpen, ShieldCheck, BarChart3, MessageSquareText, LogOut, Menu, X, Bell, Sparkles, Building2, AlertTriangle, UserPlus, Settings, Calendar, Clock } from 'lucide-react';",
    content
)

# Step 2: Replace NAV array completely
new_nav = """const NAV = [
  { to: '/dashboard',      icon: LayoutDashboard,   label: 'Dashboard'   },
  { to: '/clients',        icon: Users,             label: 'Clients'     },
  { to: '/invoices',       icon: FileText,          label: 'Invoices'    },
  { to: '/documents',      icon: FolderOpen,        label: 'Documents'   },
  { to: '/compliance',     icon: ShieldCheck,       label: 'Compliance'  },
  { to: '/reports',        icon: BarChart3,         label: 'Reports'     },
  { to: '/matters',        icon: Building2,         label: 'Matters'     },
  { to: '/court-calendar', icon: Calendar,          label: 'Court Cal.'  },
  { to: '/drafting',       icon: FileText,          label: 'AI Drafting' },
  { to: '/legal-billing',  icon: Clock,             label: 'Billing'     },
  { to: '/chat',           icon: MessageSquareText, label: 'AI Chat'     },
  { to: '/team',           icon: UserPlus,          label: 'Team'        },
  { to: '/settings',       icon: Settings,          label: 'Settings'    },
];"""

content = re.sub(r'const NAV = \[.*?\];', new_nav, content, flags=re.DOTALL)

open(path, 'w', encoding='utf-8').write(content)
print('AppLayout.jsx rewritten successfully!')
print('All law firm pages now in sidebar.')