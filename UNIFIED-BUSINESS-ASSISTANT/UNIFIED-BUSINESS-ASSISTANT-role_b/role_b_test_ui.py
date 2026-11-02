from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

API_URL = "http://127.0.0.1:8001/query"
PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Role B Data Service Tester</title>
<style>
:root{color-scheme:dark;font:15px system-ui,sans-serif;background:#0b1220;color:#e5edf8}body{max-width:1100px;margin:36px auto;padding:0 20px}h1{font-size:24px}p{color:#a8b7cb}form{display:flex;gap:10px;margin:22px 0}input{flex:1;min-width:0;padding:12px;border:1px solid #41516a;border-radius:8px;background:#111c2e;color:inherit}button{padding:12px 20px;border:0;border-radius:8px;background:#13c8e8;color:#06121d;font-weight:700;cursor:pointer}button:disabled{opacity:.6;cursor:wait}#status{margin:14px 0}.table-wrap{overflow:auto;max-height:65vh;border:1px solid #34445c;border-radius:8px}table{border-collapse:collapse;width:100%;white-space:nowrap}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #29364b}th{position:sticky;top:0;background:#183247;color:#46d5f0}tr:nth-child(even){background:#111b2a}details{margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#080d16;padding:14px;border-radius:8px;color:#7fe1f4}.error{color:#ff9c9c}
</style>
</head>
<body>
<h1>Role B Data Service Tester</h1>
<p>Questions are sent directly to Role B at <code>127.0.0.1:8001/query</code>. Results shown here come from Role B's response.</p>
<form id="question-form"><input id="question" placeholder="Ask a database question, e.g. List all products" required><button id="send">Run query</button></form>
<div id="status" role="status">Ready.</div><div id="result"></div>
<script>
const form=document.querySelector('#question-form'), input=document.querySelector('#question'), button=document.querySelector('#send'), statusBox=document.querySelector('#status'), result=document.querySelector('#result');
form.addEventListener('submit',async event=>{event.preventDefault();button.disabled=true;statusBox.textContent='Sending question to Role B…';result.replaceChildren();try{const response=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:input.value})});const data=await response.json();if(!response.ok||!data.success){throw new Error(data.error||JSON.stringify(data.detail||data))}statusBox.textContent=`Role B returned ${data.row_count} row(s).`;const details=document.createElement('details'),summary=document.createElement('summary'),sql=document.createElement('pre');summary.textContent='Generated SQL';sql.textContent=data.sql||'';details.append(summary,sql);result.append(details);if(data.columns?.length){const wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table'),thead=document.createElement('thead'),headRow=document.createElement('tr');for(const col of data.columns){const th=document.createElement('th');th.textContent=col;headRow.append(th)}thead.append(headRow);table.append(thead);const tbody=document.createElement('tbody');for(const row of data.rows||[]){const tr=document.createElement('tr');for(const col of data.columns){const td=document.createElement('td');td.textContent=row[col]===null?'NULL':String(row[col]??'');tr.append(td)}tbody.append(tr)}table.append(tbody);wrap.append(table);result.append(wrap)}else if(data.rows?.length===0){const empty=document.createElement('p');empty.textContent='Query succeeded with no matching rows.';result.append(empty)}}catch(error){statusBox.className='error';statusBox.textContent=`Request failed: ${error.message}`}finally{button.disabled=false}});
</script>
</body>
</html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        payload = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/query":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            outbound = Request(API_URL, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(outbound, timeout=90) as response:
                status, payload = response.status, response.read()
        except HTTPError as exc:
            status, payload = exc.code, exc.read()
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            status, payload = 502, json.dumps({"error": f"Could not reach Role B: {exc}"}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print("[Role B test UI] " + fmt % args)

if __name__ == "__main__":
    print("Role B test UI: http://127.0.0.1:8501")
    HTTPServer(("127.0.0.1", 8501), Handler).serve_forever()
