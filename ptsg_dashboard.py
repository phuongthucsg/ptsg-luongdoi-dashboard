import requests
import os
import os
import json
import re
from datetime import datetime

APP_ID = os.environ.get("LARK_APP_ID", "cli_a966701989389ed0")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "4VvnxEcYH2eF7MeygjPiHg55ufbWqQ8h")

APP_TOKEN = "Gg5TbludRa8oHcswRpNls8C9gZd"
TABLE_ID = "tbl1SH0zppLyePdB"

COL_NGAY = "Ngày"
COL_TO_DOI = "Tổ Đội"
COL_LUONG = "Tổng Lương/ Ngày"
COL_CONG_TRINH = "Công trình"

OUTPUT_FILE = "ptsg_dashboard.html"


def get_access_token():
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Lỗi lấy token: {data}")
    print("✅ Lấy token thành công")
    return data["tenant_access_token"]


def get_all_records(token):
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    all_records = []
    page_token = None
    page = 1
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Lỗi lấy dữ liệu: {data}")
        items = data["data"]["items"]
        all_records.extend(items)
        print(f"  Trang {page}: {len(items)} records")
        if not data["data"].get("has_more"):
            break
        page_token = data["data"]["page_token"]
        page += 1
    print(f"✅ Tổng cộng: {len(all_records)} records")
    return all_records


def parse_money(val):
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        clean = re.sub(r'[₫,\s]', '', val)
        try:
            return int(float(clean))
        except:
            return 0
    return 0


def parse_date(val):
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val / 1000).strftime('%Y/%m/%d')
    if isinstance(val, str):
        return val[:10].replace('-', '/')
    return None


def get_text(val):
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        parts = []
        for item in val:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts).strip()
    if isinstance(val, (int, float)):
        return str(val)
    return ""


def process_records(records):
    data = []
    for r in records:
        fields = r.get("fields", {})
        ngay = parse_date(fields.get(COL_NGAY))
        to_doi = get_text(fields.get(COL_TO_DOI, ""))
        luong = parse_money(fields.get(COL_LUONG, 0))
        cong_trinh = get_text(fields.get(COL_CONG_TRINH, ""))
        if ngay and to_doi:
            data.append({"ngay": ngay, "to_doi": to_doi, "cong_trinh": cong_trinh, "luong": luong})
        else:
            print(f"  ⚠️  Bỏ qua: ngay={fields.get(COL_NGAY)}, to_doi={fields.get(COL_TO_DOI)}")
    return data


def generate_html(data):
    data_json = json.dumps(data, ensure_ascii=False)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>PTSG — Dashboard Lương Tổ Đội</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Be Vietnam Pro', sans-serif; background: #0f1117; color: #e8eaf0; padding: 20px; min-height: 100vh; }
  h1 { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 4px; }
  .subtitle { font-size: 12px; color: #6b7280; margin-bottom: 20px; }
  .filters { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: flex-end; }
  .filter-group { display: flex; flex-direction: column; gap: 5px; }
  label { font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
  input[type="date"], select { background: #1e2130; border: 1px solid #2d3148; color: #e8eaf0; padding: 8px 12px; border-radius: 8px; font-size: 13px; font-family: 'Be Vietnam Pro', sans-serif; outline: none; }
  .btn { background: #4f6ef7; color: #fff; border: none; padding: 8px 18px; border-radius: 8px; font-size: 13px; font-family: 'Be Vietnam Pro', sans-serif; font-weight: 600; cursor: pointer; align-self: flex-end; }
  .btn:hover { background: #3d5ce6; }
  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .card { background: #1e2130; border: 1px solid #2d3148; border-radius: 12px; padding: 14px 16px; }
  .card-label { font-size: 11px; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .card-value { font-size: 20px; font-weight: 700; color: #fff; }
  .card-value.highlight { color: #4f6ef7; }
  .card-value.green { color: #34d399; }
  table { width: 100%; border-collapse: collapse; background: #1e2130; border-radius: 12px; overflow: hidden; border: 1px solid #2d3148; margin-bottom: 16px; }
  thead { background: #252840; }
  th { padding: 12px 14px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #9ca3af; border-bottom: 1px solid #2d3148; }
  th.right, td.right { text-align: right; }
  td { padding: 11px 14px; font-size: 13px; border-bottom: 1px solid #1a1d2e; color: #d1d5db; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #252840; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .luong-val { font-weight: 600; color: #34d399; }
  .total-row td { background: #252840; font-weight: 700; color: #fff; border-top: 2px solid #4f6ef7; }
  .week-info { font-size: 12px; color: #6b7280; margin-bottom: 12px; padding: 8px 12px; background: #1e2130; border-radius: 8px; border-left: 3px solid #4f6ef7; }
  .empty { text-align: center; padding: 40px; color: #6b7280; font-size: 14px; }
  .updated { font-size: 11px; color: #4b5563; margin-top: 16px; }
</style>
</head>
<body>
<h1>📊 Dashboard Lương Tổ Đội — PTSG</h1>
<p class="subtitle">Dữ liệu cập nhật lúc: """ + now + """ · Tổng """ + str(len(data)) + """ bản ghi</p>
<div class="filters">
  <div class="filter-group"><label>Từ ngày</label><input type="date" id="dateFrom"></div>
  <div class="filter-group"><label>Đến ngày</label><input type="date" id="dateTo"></div>
  <div class="filter-group"><label>Tổ đội</label><select id="toDoi"><option value="">Tất cả</option></select></div>
  <div class="filter-group"><label>Công trình</label><select id="congTrinh"><option value="">Tất cả</option></select></div>
  <button class="btn" onclick="calculate()">Tính lương</button>
</div>
<div class="week-info" id="weekInfo">Chọn khoảng ngày và nhấn Tính lương</div>
<div class="summary-cards" id="summaryCards"></div>
<table>
  <thead><tr><th>Tổ Đội</th><th>Công Trình</th><th class="right">Số ngày công</th><th class="right">Tổng Lương</th><th class="right">TB / Ngày</th></tr></thead>
  <tbody id="tableBody"><tr><td colspan="5" class="empty">Nhấn "Tính lương" để xem kết quả</td></tr></tbody>
</table>
<p class="updated">⏱ Dữ liệu lấy từ Lark Base lúc """ + now + """. Chạy lại script để cập nhật.</p>
<script>
const RAW = """ + data_json + """;
const COLORS = ['#4f6ef7','#34d399','#f59e0b','#f472b6','#a78bfa','#60a5fa','#fb923c'];
function fmt(n) { return '₫' + n.toLocaleString('vi-VN'); }
function parseDate(s) { const [y,m,d] = s.split('/'); return new Date(+y,+m-1,+d); }
function toInput(d) { return d.toISOString().split('T')[0]; }
function buildWeeks() {
  const dates = RAW.map(r => parseDate(r.ngay));
  const minD = new Date(Math.min(...dates)), maxD = new Date(Math.max(...dates));
  const sel = document.getElementById('weekPicker');
  let cur = new Date(minD);
  cur.setDate(cur.getDate() - ((cur.getDay()+6)%7));
  while (cur <= maxD) {
    const mon = new Date(cur), sun = new Date(cur);
    sun.setDate(sun.getDate()+6);
    const opt = document.createElement('option');
    opt.value = toInput(mon)+'|'+toInput(sun);
    opt.textContent = mon.getDate()+'/'+(mon.getMonth()+1)+' - '+sun.getDate()+'/'+(sun.getMonth()+1)+'/'+sun.getFullYear();
    sel.appendChild(opt);
    cur.setDate(cur.getDate()+7);
  }
  if (sel.options.length > 1) {
    sel.selectedIndex = sel.options.length-1;
    const [f,t] = sel.value.split('|');
    document.getElementById('dateFrom').value = f;
    document.getElementById('dateTo').value = t;
  }
}
function buildFilters() {
  const toDois = [...new Set(RAW.map(r => r.to_doi))].sort();
  const cts = [...new Set(RAW.map(r => r.cong_trinh))].sort();
  toDois.forEach(td => { const o = document.createElement('option'); o.value=td; o.textContent=td; document.getElementById('toDoi').appendChild(o); });
  cts.forEach(c => { const o = document.createElement('option'); o.value=c; o.textContent=c; document.getElementById('congTrinh').appendChild(o); });
}
document.getElementById('weekPicker').addEventListener('change', function() {
  if (!this.value) return;
  const [f,t] = this.value.split('|');
  document.getElementById('dateFrom').value = f;
  document.getElementById('dateTo').value = t;
});
function calculate() {
  const from = new Date(document.getElementById('dateFrom').value);
  const to = new Date(document.getElementById('dateTo').value);
  to.setHours(23,59,59);
  const filterTD = document.getElementById('toDoi').value;
  const filterCT = document.getElementById('congTrinh').value;
  const filtered = RAW.filter(r => {
    const d = parseDate(r.ngay);
    return d >= from && d <= to && (!filterTD || r.to_doi===filterTD) && (!filterCT || r.cong_trinh===filterCT);
  });
  const grouped = {};
  filtered.forEach(r => {
    const key = r.to_doi+'||'+r.cong_trinh;
    if (!grouped[key]) grouped[key] = {to_doi:r.to_doi, cong_trinh:r.cong_trinh, luong:0, ngay:0};
    grouped[key].luong += r.luong;
    grouped[key].ngay += 1;
  });
  const rows = Object.values(grouped).sort((a,b) => b.luong-a.luong);
  const totalLuong = rows.reduce((s,v) => s+v.luong, 0);
  const totalNgay = rows.reduce((s,v) => s+v.ngay, 0);
  const toDois = [...new Set(rows.map(r => r.to_doi))];
  const fromStr = from.toLocaleDateString('vi-VN');
  const toStr = new Date(document.getElementById('dateTo').value).toLocaleDateString('vi-VN');
  document.getElementById('weekInfo').textContent = 'Kỳ tính lương: '+fromStr+' → '+toStr+' · '+filtered.length+' bản ghi';
  document.getElementById('summaryCards').innerHTML =
    '<div class="card"><div class="card-label">Tổng lương kỳ</div><div class="card-value green">'+fmt(totalLuong)+'</div></div>'+
    '<div class="card"><div class="card-label">Số tổ đội</div><div class="card-value highlight">'+toDois.length+'</div></div>'+
    '<div class="card"><div class="card-label">Tổng ngày công</div><div class="card-value">'+totalNgay+'</div></div>'+
    '<div class="card"><div class="card-label">TB / tổ đội</div><div class="card-value">'+(toDois.length?fmt(Math.round(totalLuong/toDois.length)):'₫0')+'</div></div>';
  const tbody = document.getElementById('tableBody');
  if (!rows.length) { tbody.innerHTML='<tr><td colspan="5" class="empty">Không có dữ liệu</td></tr>'; return; }
  tbody.innerHTML = rows.map(v => {
    const idx = toDois.indexOf(v.to_doi)%COLORS.length;
    return '<tr><td><span class="badge" style="background:'+COLORS[idx]+'22;color:'+COLORS[idx]+'">'+v.to_doi+'</span></td>'+
      '<td style="color:#9ca3af;font-size:12px">'+v.cong_trinh+'</td>'+
      '<td class="right">'+v.ngay+' ngày</td>'+
      '<td class="right luong-val">'+fmt(v.luong)+'</td>'+
      '<td class="right">'+fmt(Math.round(v.luong/v.ngay))+'</td></tr>';
  }).join('') +
    '<tr class="total-row"><td colspan="2">TỔNG CỘNG</td><td class="right">'+totalNgay+' ngày</td><td class="right">'+fmt(totalLuong)+'</td><td class="right">—</td></tr>';
}
buildWeeks(); buildFilters(); calculate();
</script>
</body>
</html>"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Dashboard đã tạo: {OUTPUT_FILE}")


def main():
    print("🚀 Bắt đầu lấy dữ liệu từ Lark Base...")
    token = get_access_token()
    print("📥 Đang tải dữ liệu...")
    records = get_all_records(token)
    print("⚙️  Đang xử lý dữ liệu...")
    data = process_records(records)
    print(f"✅ Xử lý xong: {len(data)} bản ghi hợp lệ")
    print("🎨 Đang tạo dashboard...")
    generate_html(data)
    print()
    print(f"✨ Hoàn thành! Mở file '{OUTPUT_FILE}' trong trình duyệt để xem.")


if __name__ == "__main__":
    main()
