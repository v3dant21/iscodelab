"""Immutable sample bills. Never represents a registered supplier or live tax invoice."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from zoneinfo import ZoneInfo


def rounded(value):
    return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def tax_breakdown(order_lines):
    lines = []
    for line in order_lines:
        gross = line['price'] * line['quantity']
        base = rounded(Decimal(gross) / Decimal('1.05'))
        central = rounded(Decimal(base) * Decimal('0.025'))
        lines.append({**line, 'gross': gross, 'taxable': base, 'cgst': central, 'sgst': central,
                      'rounding': gross - base - central * 2})
    return {'lines': lines, 'taxable': sum(x['taxable'] for x in lines), 'cgst': sum(x['cgst'] for x in lines), 'sgst': sum(x['sgst'] for x in lines), 'rounding': sum(x['rounding'] for x in lines)}


def snapshot(order, customer, outlet):
    lines = tax_breakdown(order.lines)['lines']
    return {'number': f'DEMO-{order.id:010d}', 'issued': order.accepted,
            'seller': 'Dum & Dastaan Sample Restaurant (fictional)', 'seller_address': 'Sample billing address, Hyderabad, Telangana (fictional)',
            'gstin': 'NOT REGISTERED — SAMPLE ONLY', 'customer': (getattr(order,'contact',None) or {}).get('email',customer.email), 'customer_name': (getattr(order,'contact',None) or {}).get('name',getattr(customer,'name','') or ''), 'address': order.request['address'],
            'outlet': outlet.name, 'lines': lines, 'total': order.total,
            'taxable': sum(x['taxable'] for x in lines), 'cgst': sum(x['cgst'] for x in lines),
            'sgst': sum(x['sgst'] for x in lines), 'rounding': sum(x['rounding'] for x in lines),
            'payment': order.payment, 'paid': order.total if order.payment == 'PAID' else order.due if order.payment == 'DEPOSIT_PAID' else 0,
            'order_id': order.id}


def render_bill(bill):
    e = lambda value: escape(str(value))
    money = lambda value: f'₹{value / 100:,.2f}'
    date = datetime.fromtimestamp(bill['issued'], ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST')
    rows = ''.join(f'<tr><td>{e(x["name"])}<small>{e(x["portion"])}{ " · Extra raita" if x["addon"] else ""}</small></td><td>{x["quantity"]}</td><td>{money(x["price"])}</td><td>{money(x["taxable"])}</td><td>{money(x["cgst"])}</td><td>{money(x["sgst"])}</td><td>{money(x["gross"])}</td></tr>' for x in bill['lines'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(bill['number'])} · Demo tax invoice</title>
<style>body{{font:14px/1.5 system-ui;color:#30251e;background:#fffaf3;margin:0;padding:24px}}main{{max-width:960px;margin:auto;background:white;padding:32px;border:1px solid #e8dacf}}h1{{font-size:28px;margin:8px 0}}h2{{font-size:16px}}small{{display:block}}.notice{{background:#fff0de;border:1px solid #b04b16;padding:14px}}.parties{{display:flex;gap:40px;justify-content:space-between;margin:24px 0}}.parties>div{{flex:1;overflow-wrap:anywhere}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{text-align:right;padding:10px 6px;border-bottom:1px solid #ddd}}th:first-child,td:first-child{{text-align:left}}.totals{{max-width:360px;margin:24px 0 24px auto}}.totals p{{display:flex;justify-content:space-between;gap:20px}}button,a{{color:#9c340d}}button{{padding:10px 18px;cursor:pointer}}.actions{{max-width:960px;margin:0 auto 20px;display:flex;gap:24px;align-items:center}}.scroll{{overflow:auto}}@media print{{@page{{size:A4;margin:12mm}}body{{padding:0;background:white}}main{{padding:0;border:0}}.actions{{display:none}}thead{{display:table-header-group}}tr,.parties,.totals{{break-inside:avoid}}}}@media(max-width:600px){{body{{padding:10px}}main{{padding:16px}}.parties{{display:block}}}}</style></head><body>
<nav class="actions"><a href="/orders">← Your orders</a><button onclick="window.print()">Print / Save as PDF</button></nav><main>
<div class="notice"><strong>DEMO TAX INVOICE — NOT VALID FOR TAX PURPOSES</strong><br>Fictional supplier details and illustrative 5% tax. No real payment or GST collection is certified.</div>
<h1>Demo tax invoice</h1><p><strong>{e(bill['number'])}</strong> · Order #{bill['order_id']}<br>Issued {date}</p>
<div class="parties"><div><h2>From</h2><strong>{e(bill['seller'])}</strong><p>{e(bill['seller_address'])}<br>GSTIN: {e(bill['gstin'])}<br>Kitchen: {e(bill['outlet'])}</p></div><div><h2>Bill to / Delivery address</h2><strong>{e(bill['customer'])}</strong><p>{e(bill['address'])}</p></div></div>
<p>Amounts in INR. Unit prices include the illustrative tax. Sample CGST 2.5% + SGST 2.5%; this rate is not a determination of your restaurant’s tax liability.</p>
<div class="scroll"><table><thead><tr><th>Item / customisation</th><th>Qty</th><th>Unit price</th><th>Taxable</th><th>CGST 2.5%</th><th>SGST 2.5%</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="totals"><p><span>Taxable amount</span><strong>{money(bill['taxable'])}</strong></p><p><span>CGST · 2.5%</span><span>{money(bill['cgst'])}</span></p><p><span>SGST · 2.5%</span><span>{money(bill['sgst'])}</span></p><p><span>Rounding adjustment</span><span>{money(bill['rounding'])}</span></p><p><strong>Grand total</strong><strong>{money(bill['total'])}</strong></p><p><span>Simulated amount paid</span><span>{money(bill['paid'])}</span></p><p><span>Demo balance due</span><strong>{money(bill['total']-bill['paid'])}</strong></p></div>
<p>Payment state at issue: {e(bill['payment'].replace('_',' '))}. This is a saved billing snapshot.</p><hr><small>Digitally generated sample only. Not digitally signed, not a GST portal e-invoice, and not eligible for input tax credit. A genuine invoice requires verified supplier and tax details and the applicable production billing workflow.</small></main></body></html>'''


def render_pdf(bill):
    """Generate a real PDF attachment from the immutable encrypted invoice snapshot."""
    from io import BytesIO
    from pathlib import Path
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    if 'DumHouse' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DumHouse', str(Path(__file__).parent / 'fonts' / 'DejaVuSans.ttf')))
    styles = getSampleStyleSheet()
    normal = ParagraphStyle('Invoice', parent=styles['Normal'], fontName='DumHouse', fontSize=9, leading=14, spaceAfter=6)
    title = ParagraphStyle('InvoiceTitle', parent=normal, fontSize=19, leading=25, spaceAfter=12)
    p = lambda value: Paragraph(escape(str(value)), normal)
    money = lambda value: f'₹{value/100:,.2f}'
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=42, title=bill['number'], invariant=1)
    items = [Paragraph('Dum &amp; Dastaan · Sample tax invoice', title),
             p('DEMO — NOT VALID FOR TAX PURPOSES. Fictional supplier details; test payments only.'),
             p(f"{bill['number']} · Order #{bill['order_id']}"),
             p(datetime.fromtimestamp(bill['issued'], ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST')),
             p(bill['seller']), p(bill['seller_address']), p('GSTIN: '+bill['gstin']),
             p('Kitchen: '+bill['outlet']), Spacer(1,10),
             p('Bill to: '+bill.get('customer_name', '')+' · '+bill['customer']), p(bill['address']), Spacer(1,12)]
    rows = [[p(x) for x in ['Item / portion', 'Qty', 'Unit price', 'Total (INR)']]]
    for line in bill['lines']:
        rows.append([p(line['name']+' · '+line['portion']+(' · Extra raita' if line['addon'] else '')),p(line['quantity']),p(money(line['price'])),p(money(line['gross']))])
    table = Table(rows, colWidths=[280,40,90,113], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f6eee5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#e8dacf')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7)]))
    items += [table, Spacer(1,14)]
    for label, value in [('Taxable amount',bill['taxable']),('CGST 2.5%',bill['cgst']),('SGST 2.5%',bill['sgst']),('Rounding',bill['rounding']),('Grand total',bill['total']),('Simulated amount paid',bill['paid']),('Balance due',bill['total']-bill['paid'])]:
        items.append(p(f'{label}: {money(value)}'))
    items += [p('Prices include illustrative 5% GST. Payment state at issue: '+bill['payment']),p('Digitally generated sample, not digitally signed or a GST portal e-invoice. Not eligible for input tax credit.')]
    def footer(canvas, document):
        canvas.setFont('DumHouse',8); canvas.drawString(36,22,f"{bill['number']} · Page {document.page}")
    from functools import partial
    from reportlab.pdfgen.canvas import Canvas
    doc.build(items,onFirstPage=footer,onLaterPages=footer,canvasmaker=partial(Canvas,invariant=1))
    return out.getvalue()
