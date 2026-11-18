import json, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if len(sys.argv) != 3:
    sys.exit('usage: build_xlsx.py data.json out.xlsx')
d = json.load(open(sys.argv[1]))
S, P = d['summary']['cur'], d['summary']['prev']
F = 'Arial'
BLUE = Font(name=F, size=10, color='0000FF')
BLK = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
H1 = Font(name=F, size=14, bold=True)
HDR = Font(name=F, size=10, bold=True, color='303030')
NOTE = Font(name=F, size=9, italic=True, color='616161')
WARN = Font(name=F, size=10, bold=True, color='8A6116')
HFILL = PatternFill('solid', fgColor='F1F1F1')
WFILL = PatternFill('solid', fgColor='FFF1E3')
TFILL = PatternFill('solid', fgColor='F7F7F7')
LINE = Border(bottom=Side(style='thin', color='E3E3E3'))
USD, USD2, PCT, PCT2, INT, DEC = '$#,##0;($#,##0);-', '$#,##0.00;($#,##0.00);-', '0.0%;-0.0%;-', '0.00%;-0.00%;-', '#,##0;(#,##0);-', '0.00'
PP = '+0.0" pts";-0.0" pts";-'
DIVN = {'men': "Men's", 'youth': 'Youth'}

wb = Workbook()


def sheet(name, title, sub, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name
    ws.sheet_view.showGridLines = False
    ws['A1'] = title; ws['A1'].font = H1
    ws['A2'] = sub; ws['A2'].font = NOTE
    if d['meta']['filler']:
        ws['A3'] = 'FILLER DATA. Synthetic numbers for agreeing on structure. Do not use for decisions.'
        ws['A3'].font = WARN; ws['A3'].fill = WFILL
    return ws


def header(ws, row, labels, widths=None):
    for i, l in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=l)
        c.font = HDR; c.fill = HFILL; c.border = LINE
        c.alignment = Alignment(horizontal='left' if i == 1 else 'right', vertical='center', wrap_text=True)
    ws.row_dimensions[row].height = 30
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w


def put(ws, r, c, v, fmt=None, font=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font or (BLUE if not (isinstance(v, str) and v.startswith('=')) and not isinstance(v, str) else BLK)
    if isinstance(v, str) and not v.startswith('='):
        cell.font = font or BLK
    if fmt:
        cell.number_format = fmt
    cell.border = LINE
    return cell


period = f"{d['meta']['period']['label']} vs. {d['meta']['compare']['label']} · PSD Web view · code \"{d['meta']['discount_code']}\""

# ---------------- Summary ----------------
ws = sheet('Summary', d['meta']['title'], period, first=True)
r0 = 5
header(ws, r0, ['Inputs', 'Current', 'Prior', 'Change', 'Source'], [34, 16, 16, 14, 58])
inputs = [
    ('GB net sales ($)', 'gb_net_sales', USD, 'Polar net sales, orders with _fit_id lines (incl. add-ons)'),
    ('GB orders', 'gb_orders', INT, 'Distinct order_id on lines whose order_line_properties contain _fit_id'),
    ('Outfits', 'outfits', INT, 'Distinct _fit_id'),
    ('Builder units', 'units', INT, 'custom_60206 (units) on _fit lines'),
    ('Builder list value ($)', 'gb_gross_sales', USD, 'Polar gross sales on _fit lines'),
    ('Builder discount ($)', 'gb_discounts', USD, 'Polar discounts on _fit lines (code allocation)'),
    ('Add-on net sales ($)', 'addon_net_sales', USD, 'Order net sales (code Build Your Outfit) minus builder-line net sales'),
    ('Orders with add-ons', 'addon_orders', INT, 'GB orders containing a non-_fit line'),
    ('New-customer GB orders', 'new_orders', INT, 'Polar purchase_type = new'),
    ('Web net sales ($)', 'web_net_sales', USD, 'Polar PSD Web view (Business Channel) net sales: excl. TikTok Shop, POS, CampMystery codes, trybe/sample-request tags'),
    ('Web orders', 'web_orders', INT, 'Polar PSD Web view orders (same filters)'),
    ('Builder sessions', 'sessions_visited', INT, 'Polar Pixel, page_paths_in_session contains /pages/gift-builder'),
    ('Landing sessions', 'landers', INT, 'Polar Pixel, landing_page_path = /pages/gift-builder'),
    ('ATC sessions', 'atc_sessions', INT, 'Polar Pixel add-to-cart sessions (builder sessions)'),
    ('Checkout sessions', 'checkout_sessions', INT, 'Polar Pixel checkout-started sessions (builder sessions)'),
    ('Converted sessions (any order)', 'converted_sessions', INT, 'Polar Pixel checkout-completed sessions (builder sessions)'),
]
ref = {}
for i, (lab, k, fmt, src) in enumerate(inputs):
    r = r0 + 1 + i
    put(ws, r, 1, lab); put(ws, r, 2, S[k], fmt); put(ws, r, 3, P[k], fmt)
    put(ws, r, 4, f'=IF(C{r}=0,0,B{r}/C{r}-1)', PCT)
    put(ws, r, 5, src, font=NOTE)
    ref[k] = r
r1 = r0 + len(inputs) + 2
header(ws, r1, ['KPIs (calculated)', 'Current', 'Prior', 'Change', 'Definition'])
kpis = [
    ('AOV ($)', 'gb_net_sales', 'gb_orders', USD2, 'rel', 'GB net sales ÷ GB orders'),
    ('Outfits per order', 'outfits', 'gb_orders', DEC, 'rel', 'Outfits ÷ GB orders'),
    ('Avg. kit discount', 'gb_discounts', 'gb_gross_sales', PCT, 'pp', 'Builder discount ÷ builder list value'),
    ('Share of web net sales', 'gb_net_sales', 'web_net_sales', PCT, 'pp', 'GB net sales ÷ web net sales'),
    ('Share of web orders', 'gb_orders', 'web_orders', PCT, 'pp', 'GB orders ÷ web orders'),
    ('Landing share of builder sessions', 'landers', 'sessions_visited', PCT, 'pp', 'Landing sessions ÷ builder sessions'),
    ('Add-to-cart rate', 'atc_sessions', 'sessions_visited', PCT, 'pp', 'ATC sessions ÷ builder sessions'),
    ('Checkout rate', 'checkout_sessions', 'sessions_visited', PCT2, 'pp', 'Checkout sessions ÷ builder sessions'),
    ('Builder conversion rate', 'gb_orders', 'sessions_visited', PCT2, 'pp', 'GB orders ÷ builder sessions'),
    ('Any-order conversion rate', 'converted_sessions', 'sessions_visited', PCT2, 'pp', 'Converted sessions ÷ builder sessions'),
    ('New-customer share', 'new_orders', 'gb_orders', PCT, 'pp', 'New-customer GB orders ÷ GB orders'),
    ('Add-on attach rate', 'addon_orders', 'gb_orders', PCT, 'pp', 'Orders with add-ons ÷ GB orders'),
    ('Avg. add-on value ($)', 'addon_net_sales', 'addon_orders', USD2, 'rel', 'Add-on net sales ÷ orders with add-ons'),
    ('Units per outfit', 'units', 'outfits', DEC, 'rel', 'Builder units ÷ outfits'),
]
for i, (lab, n, dn, fmt, kind, df) in enumerate(kpis):
    r = r1 + 1 + i
    a, b = ref[n], ref[dn]
    put(ws, r, 1, lab, font=BOLD)
    put(ws, r, 2, f'=IF(B{b}=0,0,B{a}/B{b})', fmt)
    put(ws, r, 3, f'=IF(C{b}=0,0,C{a}/C{b})', fmt)
    if kind == 'pp':
        put(ws, r, 4, f'=(B{r}-C{r})*100', PP)
    else:
        put(ws, r, 4, f'=IF(C{r}=0,0,B{r}/C{r}-1)', PCT)
    put(ws, r, 5, df, font=NOTE)
rn = r1 + len(kpis) + 2
ws.cell(row=rn, column=1, value='Blue = input pulled from Polar (filler for now). Black = formula. Rate changes are in percentage points.').font = NOTE
ws.freeze_panes = 'A6'

# ---------------- Division ----------------
ws = sheet('Division', "Men's vs Youth", period)
header(ws, 5, ['Division', 'Orders', 'Outfits', 'Units', 'Net sales ($)', 'List value ($)', 'Discount ($)',
               'Share of outfits', 'Share of net sales', 'Avg. per outfit ($)', 'Discount %', 'Prior outfits', 'Outfits vs. prior'],
       [16, 10, 10, 10, 14, 14, 13, 12, 12, 13, 11, 11, 12])
DV, pDV = d['division']['cur'], d['division']['prev']
for i, k in enumerate(['men', 'youth']):
    r = 6 + i
    v = DV[k]
    put(ws, r, 1, DIVN[k])
    for c, key, fmt in [(2, 'orders', INT), (3, 'outfits', INT), (4, 'units', INT), (5, 'net_sales', USD), (6, 'gross_sales', USD), (7, 'discounts', USD)]:
        put(ws, r, c, v[key], fmt)
    put(ws, r, 8, f'=IF(C$8=0,0,C{r}/C$8)', PCT)
    put(ws, r, 9, f'=IF(E$8=0,0,E{r}/E$8)', PCT)
    put(ws, r, 10, f'=IF(C{r}=0,0,E{r}/C{r})', USD2)
    put(ws, r, 11, f'=IF(F{r}=0,0,G{r}/F{r})', PCT)
    put(ws, r, 12, pDV[k]['outfits'], INT)
    put(ws, r, 13, f'=IF(L{r}=0,0,C{r}/L{r}-1)', PCT)
r = 8
put(ws, r, 1, 'Total', font=BOLD)
put(ws, r, 2, f"='Summary'!B{ref['gb_orders']}", INT, Font(name=F, size=10, bold=True, color='008000'))
for c, fmt in [(3, INT), (4, INT), (5, USD), (6, USD), (7, USD), (12, INT)]:
    L = get_column_letter(c); put(ws, r, c, f'=SUM({L}6:{L}7)', fmt, BOLD)
put(ws, r, 8, '=SUM(H6:H7)', PCT, BOLD); put(ws, r, 9, '=SUM(I6:I7)', PCT, BOLD)
put(ws, r, 10, '=IF(C8=0,0,E8/C8)', USD2, BOLD); put(ws, r, 11, '=IF(F8=0,0,G8/F8)', PCT, BOLD)
put(ws, r, 13, '=IF(L8=0,0,C8/L8-1)', PCT, BOLD)
for c in range(1, 14):
    ws.cell(row=8, column=c).fill = TFILL
ws['A9'] = 'Division orders count an order once per division it contains, so they add up to more than total orders. Outfit metrics exclude add-on items.'
ws['A9'].font = NOTE
header(ws, 11, ['Order mix', 'Orders', 'Share', 'Prior orders', 'Prior share', 'Change'])
M, pM = d['order_mix']['cur'], d['order_mix']['prev']
for i, (k, lab) in enumerate([('men_only', "Men's only"), ('youth_only', 'Youth only'), ('mixed', "Mixed (men's + youth)")]):
    r = 12 + i
    put(ws, r, 1, lab); put(ws, r, 2, M[k], INT); put(ws, r, 3, f'=IF(B$15=0,0,B{r}/B$15)', PCT)
    put(ws, r, 4, pM[k], INT); put(ws, r, 5, f'=IF(D$15=0,0,D{r}/D$15)', PCT); put(ws, r, 6, f'=(C{r}-E{r})*100', PP)
put(ws, 15, 1, 'Total', font=BOLD); put(ws, 15, 2, '=SUM(B12:B14)', INT, BOLD); put(ws, 15, 3, '=SUM(C12:C14)', PCT, BOLD)
put(ws, 15, 4, '=SUM(D12:D14)', INT, BOLD); put(ws, 15, 5, '=SUM(E12:E14)', PCT, BOLD)
ws.freeze_panes = 'B6'

# ---------------- Kit x Division ----------------
ws = sheet('Kit x Division', 'Kit × division performance', period)
cols = ['Kit (_fit)', 'Kit name', 'Division', 'Kit price ($)', 'Compare-at ($)', 'Outfits', 'Orders', 'Units', 'Net sales ($)',
        'List value ($)', 'Discount ($)', 'Share of outfits', 'Share of net sales', 'Share within division', 'Avg. per outfit ($)',
        'Discount %', 'Prior outfits', 'Prior net sales ($)', 'Outfits vs. prior', 'Net sales vs. prior']
header(ws, 5, cols, [9, 36, 10, 11, 12, 9, 9, 9, 13, 13, 12, 11, 11, 12, 12, 10, 10, 13, 11, 11])
rows = sorted(d['kit_division'], key=lambda x: -x['net_sales'])
n = len(rows); last = 5 + n; tot = last + 1
for i, k in enumerate(rows):
    r = 6 + i
    put(ws, r, 1, k['kit']); put(ws, r, 2, k['kit_name']); put(ws, r, 3, DIVN[k['division']])
    for c, key, fmt in [(4, 'price', USD), (5, 'compare_at', USD), (6, 'outfits', INT), (7, 'orders', INT), (8, 'units', INT),
                        (9, 'net_sales', USD), (10, 'gross_sales', USD), (11, 'discounts', USD), (17, 'prev_outfits', INT), (18, 'prev_net_sales', USD)]:
        put(ws, r, c, k[key], fmt)
    put(ws, r, 12, f'=IF(F${tot}=0,0,F{r}/F${tot})', PCT)
    put(ws, r, 13, f'=IF(I${tot}=0,0,I{r}/I${tot})', PCT)
    put(ws, r, 14, f'=IF(SUMIF($C$6:$C${last},C{r},$F$6:$F${last})=0,0,F{r}/SUMIF($C$6:$C${last},C{r},$F$6:$F${last}))', PCT)
    put(ws, r, 15, f'=IF(F{r}=0,0,I{r}/F{r})', USD2)
    put(ws, r, 16, f'=IF(J{r}=0,0,K{r}/J{r})', PCT)
    put(ws, r, 19, f'=IF(Q{r}=0,0,F{r}/Q{r}-1)', PCT)
    put(ws, r, 20, f'=IF(R{r}=0,0,I{r}/R{r}-1)', PCT)
put(ws, tot, 1, 'Total', font=BOLD)
for c, fmt in [(6, INT), (7, INT), (8, INT), (9, USD), (10, USD), (11, USD), (12, PCT), (13, PCT), (17, INT), (18, USD)]:
    L = get_column_letter(c); put(ws, tot, c, f'=SUM({L}6:{L}{last})', fmt, BOLD)
put(ws, tot, 15, f'=IF(F{tot}=0,0,I{tot}/F{tot})', USD2, BOLD); put(ws, tot, 16, f'=IF(J{tot}=0,0,K{tot}/J{tot})', PCT, BOLD)
put(ws, tot, 19, f'=IF(Q{tot}=0,0,F{tot}/Q{tot}-1)', PCT, BOLD); put(ws, tot, 20, f'=IF(R{tot}=0,0,I{tot}/R{tot}-1)', PCT, BOLD)
for c in range(1, 21):
    ws.cell(row=tot, column=c).fill = TFILL
ws.cell(row=tot + 1, column=1, value='Kit price = _fit_price on the orders; compare-at = list value of the outfit items. Kit-row orders add up to more than total orders when an order holds several kits.').font = NOTE
ws.cell(row=tot + 2, column=1, value=f"Check: outfit total should equal Division!C8 → ").font = NOTE
put(ws, tot + 2, 6, f"=F{tot}-'Division'!C8", INT, Font(name=F, size=10, color='008000'))
ws.freeze_panes = 'D6'
ws.auto_filter.ref = f'A5:T{last}'

# ---------------- Daily ----------------
ws = sheet('Daily', 'Daily trend', period)
header(ws, 5, ['Date', 'Net sales ($)', 'Orders', 'Outfits', 'Builder sessions', 'Conv. rate', 'AOV ($)', 'Prior date',
               'Prior net sales ($)', 'Prior orders', 'Prior outfits', 'Prior sessions', 'Net sales vs. prior'],
       [12, 13, 9, 9, 12, 10, 11, 12, 13, 10, 10, 11, 12])
import datetime as dt
for i, x in enumerate(d['daily']):
    r = 6 + i
    put(ws, r, 1, dt.date.fromisoformat(x['date']), 'mmm d, yyyy', BLUE)
    put(ws, r, 2, x['net_sales'], USD); put(ws, r, 3, x['orders'], INT); put(ws, r, 4, x['outfits'], INT); put(ws, r, 5, x['sessions_visited'], INT)
    put(ws, r, 6, f'=IF(E{r}=0,0,C{r}/E{r})', PCT2); put(ws, r, 7, f'=IF(C{r}=0,0,B{r}/C{r})', USD2)
    if x.get('prev_date'):
        put(ws, r, 8, dt.date.fromisoformat(x['prev_date']), 'mmm d, yyyy', BLUE)
        put(ws, r, 9, x['prev_net_sales'], USD); put(ws, r, 10, x['prev_orders'], INT); put(ws, r, 11, x['prev_outfits'], INT); put(ws, r, 12, x['prev_sessions_visited'], INT)
    put(ws, r, 13, f'=IF(I{r}=0,0,B{r}/I{r}-1)', PCT)
r = 6 + len(d['daily'])
put(ws, r, 1, 'Total', font=BOLD)
for c, fmt in [(2, USD), (3, INT), (4, INT), (5, INT), (9, USD), (10, INT), (11, INT), (12, INT)]:
    L = get_column_letter(c); put(ws, r, c, f'=SUM({L}6:{L}{r-1})', fmt, BOLD)
put(ws, r, 6, f'=IF(E{r}=0,0,C{r}/E{r})', PCT2, BOLD); put(ws, r, 7, f'=IF(C{r}=0,0,B{r}/C{r})', USD2, BOLD)
put(ws, r, 13, f'=IF(I{r}=0,0,B{r}/I{r}-1)', PCT, BOLD)
for c in range(1, 14):
    ws.cell(row=r, column=c).fill = TFILL
ws.freeze_panes = 'B6'

# ---------------- Traffic ----------------
ws = sheet('Traffic', 'Builder page traffic', period + ' · Polar Pixel sessions that viewed ' + d['meta']['landing_path'])
header(ws, 5, ['Funnel step', 'Sessions', '% of builder sessions', 'Step conversion', 'Prior', 'Prior %', 'Change'], [34, 12, 14, 14, 12, 12, 12])
steps = [('Viewed the builder', 'sessions_visited'), ('Added to cart', 'atc_sessions'), ('Reached checkout', 'checkout_sessions'), ('Placed a Gift Builder order', 'gb_orders')]
for i, (lab, k) in enumerate(steps):
    r = 6 + i
    put(ws, r, 1, lab); put(ws, r, 2, f"='Summary'!B{ref[k]}", INT, Font(name=F, size=10, color='008000'))
    put(ws, r, 3, f'=IF(B$6=0,0,B{r}/B$6)', PCT2)
    put(ws, r, 4, '' if i == 0 else f'=IF(B{r-1}=0,0,B{r}/B{r-1})', PCT)
    put(ws, r, 5, f"='Summary'!C{ref[k]}", INT, Font(name=F, size=10, color='008000'))
    put(ws, r, 6, f'=IF(E$6=0,0,E{r}/E$6)', PCT2); put(ws, r, 7, f'=(C{r}-F{r})*100', PP)
row = 12
for title, key in [('How they arrived', 'entry'), ('By channel', 'by_channel'), ('By device', 'by_device')]:
    header(ws, row, [title, 'Sessions', 'Share of sessions', 'ATC rate', 'Conv. rate'])
    rs = d['traffic'][key] or [{'segment': '(no sessions)', 'sessions': 0, 'atc_rate': 0, 'cvr': 0}]
    first = row + 1; lastr = row + len(rs)
    for i, x in enumerate(rs):
        r = first + i
        put(ws, r, 1, x['segment']); put(ws, r, 2, x['sessions'], INT)
        put(ws, r, 3, f'=IF(SUM($B${first}:$B${lastr})=0,0,B{r}/SUM($B${first}:$B${lastr}))', PCT)
        put(ws, r, 4, x['atc_rate'], PCT); put(ws, r, 5, x['cvr'], PCT2)
    put(ws, lastr + 1, 1, 'Total', font=BOLD); put(ws, lastr + 1, 2, f'=SUM(B{first}:B{lastr})', INT, BOLD)
    put(ws, lastr + 1, 4, f'=IF(B{lastr+1}=0,0,SUMPRODUCT(B{first}:B{lastr},D{first}:D{lastr})/B{lastr+1})', PCT, BOLD)
    put(ws, lastr + 1, 5, f'=IF(B{lastr+1}=0,0,SUMPRODUCT(B{first}:B{lastr},E{first}:E{lastr})/B{lastr+1})', PCT2, BOLD)
    for c in range(1, 6):
        ws.cell(row=lastr + 1, column=c).fill = TFILL
    row = lastr + 3
ws.cell(row=row, column=1, value='Green = linked from Summary. Segment conv. rate = builder sessions that placed any order ÷ builder sessions. Mid-session = builder sessions minus landing sessions.').font = NOTE

# ---------------- Top picks ----------------
ws = sheet('Top Picks', 'What shoppers pick', period + ' · units per product within each _fit_slot')
header(ws, 5, ['Slot', 'Product', 'Units', 'Share of slot'], [14, 36, 10, 12])
r = 6
names = {'fit-3pk': '3-Pack', 'fit-shorts': 'Shorts', 'fit-tee': 'Tee', 'fit-hoodie': 'Hoodie', 'fit-pants': 'Pants'}
for slot in ['fit-3pk', 'fit-shorts', 'fit-tee', 'fit-hoodie', 'fit-pants']:
    for p in d['top_picks'].get(slot, []):
        put(ws, r, 1, f'{names[slot]} ({slot})'); put(ws, r, 2, p['product']); put(ws, r, 3, p['units'], INT); put(ws, r, 4, p['share'], PCT)
        r += 1
ws.cell(row=r + 1, column=1, value='Share of slot is against all units in the slot, not only the top 5 shown.').font = NOTE
ws.freeze_panes = 'A6'

# ---------------- Kits config ----------------
ws = sheet('Kit Config', 'Kit pricing', 'Prices seen on this period\'s orders (fallback: skill config / Shopify Fit metaobject)')
header(ws, 5, ['Handle', 'Name', 'Slots', "Men's price ($)", "Men's compare-at ($)", "Men's discount", 'Youth price ($)', 'Youth compare-at ($)', 'Youth discount'],
       [9, 38, 36, 13, 15, 12, 13, 15, 12])
for i, k in enumerate(d['kits']):
    r = 6 + i
    put(ws, r, 1, k['handle']); put(ws, r, 2, k['name']); put(ws, r, 3, ', '.join(k['slots']))
    put(ws, r, 4, k['price']['men'], USD); put(ws, r, 5, k['compare_at']['men'], USD); put(ws, r, 6, f'=IF(E{r}=0,0,1-D{r}/E{r})', PCT)
    put(ws, r, 7, k['price']['youth'], USD); put(ws, r, 8, k['compare_at']['youth'], USD); put(ws, r, 9, f'=IF(H{r}=0,0,1-G{r}/H{r})', PCT)

# ---------------- Definitions ----------------
ws = sheet('Definitions', 'Definitions & data sources', 'How each metric will be computed when wired to Polar')
header(ws, 5, ['Metric', 'Definition', 'Polar source'], [26, 70, 70])
defs = [
    ('Gift Builder order', 'Order with at least one line carrying _fit_id. Code-only orders (no builder lines) are excluded and listed in the run issues.', 'shopify_sales_main, rule order_line_properties CONTAINS "key":"_fit_id", PSD Web view'),
    ('Outfit', 'One kit added in the builder: one distinct _fit_id.', 'Parsed from order_line_properties'),
    ('Division', '_fit_division (men / youth). Orders holding both are mixed.', 'order_line_properties'),
    ('Kit', '_fit handle: us, uh, ut, uts, utsh, sp. Price = _fit_price; compare-at = list value of the outfit items.', 'order_line_properties; names from skill config'),
    ('Slot', '_fit_slot: fit-3pk, fit-shorts, fit-tee, fit-hoodie, fit-pants.', 'order_line_properties'),
    ('Net sales', 'Gross sales + discounts + returns (discounts and returns stored negative). Excludes shipping and tax. Returns keep landing after the period ends.', 'shopify_sales_main.computed.net_sales'),
    ('Add-ons', 'Order net sales minus builder-line net sales.', 'order_id breakdown, order_discount_code IS "Build Your Outfit"'),
    ('List value / discount', 'Gross sales and discounts on builder lines.', 'raw.gross_sales, raw.discounts'),
    ('Share of web', 'GB orders or net sales ÷ PSD Web orders or net sales; both in the PSD Web view.', 'Polar view "PSD Web": excl. TikTok Shop + POS sales channels, CampMystery codes, trybe / sample-request tagged orders'),
    ('New-customer orders', 'GB orders that were the customer\'s first order.', 'purchase_type = new'),
    ('Builder sessions', 'Sessions whose page paths include the builder page. Bot sessions included.', 'Polar Pixel page_paths_in_session CONTAINS /pages/gift-builder'),
    ('Landing sessions', 'Sessions that started on the builder page.', 'Polar Pixel landing_page_path IS /pages/gift-builder'),
    ('Add-to-cart rate', 'Builder sessions with an add to cart ÷ builder sessions.', 'polar_pixel_funnel_product_added_to_cart_sessions'),
    ('Conversion rate', 'GB orders ÷ builder sessions; segment tables use sessions that placed any order.', 'polar_pixel_funnel_checkout_completed_sessions + Shopify orders'),
]
for i, row_ in enumerate(defs):
    r = 6 + i
    for c, v in enumerate(row_, 1):
        cell = put(ws, r, c, v, font=BOLD if c == 1 else BLK)
        cell.alignment = Alignment(wrap_text=True, vertical='top')

for w in wb.worksheets:
    w.sheet_properties.tabColor = None
wb.save(sys.argv[2])
print(f'build_xlsx.py: OK → {sys.argv[2]}' + (' (FILLER)' if d['meta']['filler'] else ''))
