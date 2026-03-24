# fix_main2.py - directly repairs the broken bottom of main.py
import os

BASE = os.path.dirname(os.path.abspath(__file__))
main_path = os.path.join(BASE, 'main.py')

content = open(main_path, encoding='utf-8').read()
lines = content.split('\n')

# Find the line with create_app() call - we'll keep everything up to that
cutoff = 0
for i, line in enumerate(lines):
    if 'app = create_app()' in line:
        cutoff = i
        break

if cutoff == 0:
    print("ERROR: Could not find 'app = create_app()' in main.py")
    print("Showing full file:")
    for i, l in enumerate(lines):
        print(f"{i+1}: {l}")
    exit(1)

# Keep everything up to and including app = create_app()
clean_top = '\n'.join(lines[:cutoff+1])

# Check which routers are already imported in the top section
top = '\n'.join(lines[:cutoff])
router_imports = []
router_includes = []

router_map = [
    ('app.api.routes.legal_draft_routes',    'draft_router'),
    ('app.api.routes.legal_research_routes', 'research_router'),
    ('app.api.routes.financial_routes',      'financial_router'),
    ('app.api.routes.dashboard_routes',      'dashboard_router'),
    ('app.api.routes.gst_routes',            'gst_router'),
]

for mod, router in router_map:
    if f'from {mod}' not in top:
        router_imports.append(f'from {mod} import {router}')

# Build the clean ending
clean_end = '''

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''

# Combine: clean top + new imports + clean ending
new_imports_block = '\n'.join(router_imports)
if new_imports_block:
    # Insert imports before app = create_app()
    insert_before = f'app = create_app()'
    new_content = clean_top.replace(
        insert_before,
        new_imports_block + '\n\n' + insert_before
    )
else:
    new_content = clean_top

new_content = new_content.rstrip() + clean_end

open(main_path, 'w', encoding='utf-8').write(new_content)
print("✅ main.py fixed!")
print(f"   Added {len(router_imports)} missing imports")
print("\nVerifying - last 20 lines of main.py:")
final_lines = new_content.split('\n')
for i, l in enumerate(final_lines[-20:], start=len(final_lines)-19):
    print(f"{i:3}: {l}")

print("\nNow run: uvicorn main:app --port 8000")