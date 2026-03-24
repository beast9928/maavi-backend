import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import date, timedelta
from app.db.database import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models import User, Client, Invoice, ComplianceItem
from app.models import InvoiceType, ComplianceType, ComplianceStatus

def seed():
    print('Creating database tables...')
    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == 'demo@cacopilot.in').first()
        if existing:
            user = existing
            print('User exists, updating data...')
        else:
            user = User(
                email='demo@cacopilot.in',
                full_name='Demo CA',
                hashed_password=get_password_hash('demo@1234'),
                firm_name='Demo CA Firm',
                role='ca_admin',
                is_active=True,
            )
            db.add(user)
            db.flush()

        today = date.today()
        clients_data = [
            {'company_name':'TechVision Pvt Ltd','gstin':'27AABCT1332L1ZX','pan':'AABCT1332L','email':'accounts@techvision.in','state':'Maharashtra','business_type':'Private Limited'},
            {'company_name':'Sunrise Exports','gstin':'29AADCS5739D1ZV','pan':'AADCS5739D','email':'finance@sunrise.co.in','state':'Karnataka','business_type':'Partnership'},
            {'company_name':'Green Retail Solutions','gstin':'33AAECG7142K1ZP','pan':'AAECG7142K','email':'gst@greenretail.in','state':'Tamil Nadu','business_type':'LLP'},
        ]
        clients = []
        for cd in clients_data:
            c = db.query(Client).filter(Client.gstin == cd['gstin']).first()
            if not c:
                c = Client(ca_user_id=user.id, is_active=True, **cd)
                db.add(c)
                db.flush()
            clients.append(c)
        db.commit()

        invs = [
            (clients[0],'sale','INV-001','TechVision','ABC Corp',100000,9,9,0,18000,118000),
            (clients[0],'sale','INV-002','TechVision','XYZ Ltd',85000,9,9,0,15300,100300),
            (clients[0],'purchase','BILL-045','Cloud Services','TechVision',25000,9,9,0,4500,29500),
            (clients[1],'sale','EXP-101','Sunrise Exports','Global Trade',250000,0,0,0,0,250000),
            (clients[1],'purchase','PURCH-023','Raw Materials Co','Sunrise',80000,9,9,0,14400,94400),
            (clients[2],'sale','GR-201','Green Retail','Reliance',180000,6,6,0,21600,201600),
            (clients[2],'purchase','GR-089','Wholesale Dist','Green Retail',120000,6,6,0,14400,134400),
        ]
        for c,itype,num,vendor,buyer,taxable,cr,sr,ir,ttax,total in invs:
            if not db.query(Invoice).filter(Invoice.invoice_number==num, Invoice.client_id==c.id).first():
                inv = Invoice(
                    client_id=c.id,
                    invoice_type=InvoiceType.SALE if itype=='sale' else InvoiceType.PURCHASE,
                    invoice_number=num,
                    invoice_date=today - timedelta(days=30),
                    vendor_name=vendor,
                    vendor_gstin=c.gstin,
                    buyer_name=buyer,
                    buyer_gstin=c.gstin,
                    taxable_amount=float(taxable),
                    cgst_rate=float(cr), cgst_amount=float(taxable*cr/100),
                    sgst_rate=float(sr), sgst_amount=float(taxable*sr/100),
                    igst_rate=float(ir), igst_amount=0.0,
                    total_tax=float(ttax),
                    total_amount=float(total),
                    payment_status='paid',
                    is_reconciled=True,
                    gst_verified=True,
                )
                db.add(inv)
        db.flush()

        comps = [
            (clients[0],ComplianceType.GST_FILING,'GSTR-1','Mar 2024',today+timedelta(days=3),18000),
            (clients[0],ComplianceType.GST_FILING,'GSTR-3B','Mar 2024',today+timedelta(days=10),18000),
            (clients[0],ComplianceType.TDS_RETURN,'Q4 2023-24','Q4 2023-24',today+timedelta(days=5),5000),
            (clients[1],ComplianceType.GST_FILING,'GSTR-1','Mar 2024',today+timedelta(days=3),0),
            (clients[1],ComplianceType.GST_FILING,'GSTR-3B','Mar 2024',today+timedelta(days=10),14400),
            (clients[2],ComplianceType.GST_FILING,'GSTR-1','Mar 2024',today+timedelta(days=3),21600),
            (clients[2],ComplianceType.TDS_RETURN,'Q4 2023-24','Q4 2023-24',today-timedelta(days=2),3000),
        ]
        for cl,ctype,desc,period,due,amount in comps:
            if not db.query(ComplianceItem).filter(ComplianceItem.client_id==cl.id, ComplianceItem.period==period, ComplianceItem.compliance_type==ctype).first():
                status = ComplianceStatus.OVERDUE if due < today else ComplianceStatus.PENDING
                db.add(ComplianceItem(
                    client_id=cl.id, compliance_type=ctype,
                    period=period, due_date=due, status=status,
                    amount_payable=float(amount), amount_paid=0.0, penalty_amount=0.0,
                ))
        db.commit()
        print('')
        print('=' * 50)
        print('Seed complete!')
        print('  Email:    demo@cacopilot.in')
        print('  Password: demo@1234')
        print('  Clients:  3')
        print('  Invoices: 7')
        print('=' * 50)
    except Exception as e:
        db.rollback()
        print('Seed failed:', e)
        import traceback; traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    seed()
