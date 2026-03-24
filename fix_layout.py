path = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\components\layout\AppLayout.jsx'
content = open(path, encoding='utf-8').read()

# Remove ALL the extra import lines we added
content = content.replace(
    ", AlertTriangle, UserPlus, Settings, Building2 } from 'lucide-react';",
    " } from 'lucide-react';"
)
content = content.replace(
    ", AlertTriangle, UserPlus, Settings, Calendar, Clock, Building2 } from 'lucide-react';",
    " } from 'lucide-react';"
)

# Now find the lucide import line and print it so we can see exactly what's there
import re
match = re.search(r"import \{[^}]+\} from 'lucide-react';", content)
if match:
    print('Current import line:')
    print(match.group())
    
open(path, 'w', encoding='utf-8').write(content)
print('Cleaned up imports')