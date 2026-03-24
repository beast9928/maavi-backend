content = open('app/api/routes/clients.py').read()

old = 'summary = ClientSummary.model_validate(c)'

new = ('summary = ClientSummary(\n'
       '            id=c.id,\n'
       '            company_name=c.company_name,\n'
       '            pan=c.pan,\n'
       '            gstin=c.gstin,\n'
       '            email=c.email,\n'
       '            phone=c.phone,\n'
       '            address=c.address,\n'
       '            state=c.state,\n'
       '            business_type=c.business_type,\n'
       '            industry=c.industry,\n'
       '            is_active=c.is_active,\n'
       '            notes=c.notes,\n'
       '            created_at=c.created_at,\n'
       '            total_invoices=len(c.invoices) if hasattr(c, "invoices") else 0,\n'
       '            total_revenue=sum(i.total_amount or 0 for i in c.invoices) if hasattr(c, "invoices") else 0,\n'
       '            pending_compliance=len([x for x in c.compliance_items if str(x.status).endswith("PENDING")]) if hasattr(c, "compliance_items") else 0,\n'
       '            gst_mismatches=len([x for x in c.gst_mismatches if not x.is_resolved]) if hasattr(c, "gst_mismatches") else 0,\n'
       '        )')

if old in content:
    content = content.replace(old, new)
    open('app/api/routes/clients.py', 'w').write(content)
    print('FIXED successfully')
else:
    print('Pattern not found. Current file around line 40-50:')
    lines = content.split('\n')
    for i, l in enumerate(lines[35:55], 36):
        print(i, l)