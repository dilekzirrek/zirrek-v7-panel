"""Public OKX spot market snapshot. No private research, credentials, or orders."""
import json
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen

EXCLUDED={"XNVDA","XSKHY","XAAPL","XAMD","XINTC","XMRVL","XCOIN","XDELL","XTSM","XAVGO","XMSFT","XWDC","XNBIS","XBE","XCBRS","XGEV","XTQQQ","OKSOL"}
STABLE={"USDC","USDT","DAI","FDUSD","TUSD","USDE","EUR","USD"}
def fetch(path):
    with urlopen(Request("https://www.okx.com/api/v5/"+path,headers={"User-Agent":"Zirrek-V7-Public-Market/1.0"}),timeout=30) as r:
        obj=json.load(r)
    if str(obj.get("code"))!="0" or not isinstance(obj.get("data"),list):
        raise RuntimeError("OKX response unavailable")
    return obj["data"]

def main():
    instruments=fetch("public/instruments?instType=SPOT")
    tickers=fetch("market/tickers?instType=SPOT")
    allowed={i["instId"] for i in instruments
             if i.get("state")=="live" and i.get("quoteCcy")=="USDT"
             and i.get("baseCcy") not in STABLE|EXCLUDED
             and i.get("instId","").count("-")==1}
    ranked=[]
    for t in tickers:
        if t.get("instId") not in allowed:
            continue
        try:
            last=float(t["last"]); op=float(t["open24h"]); base_volume=float(t["volCcy24h"])
            bid=float(t.get("bidPx") or 0); ask=float(t.get("askPx") or 0)
            turnover=last*base_volume
            if not(last>0 and op>0 and turnover>=1_000_000 and bid>0 and ask>=bid and (ask-bid)/last<=0.005):
                continue
            ranked.append((turnover,t,last,op))
        except (ValueError,KeyError,TypeError):
            continue
    ranked.sort(key=lambda x:x[0],reverse=True)
    chosen=ranked[:50]
    if len(chosen)!=50:
        raise RuntimeError("Insufficient validated liquid spot tickers: "+str(len(chosen)))
    records=[]
    for turnover,t,last,op in chosen:
        records.append({"symbol":t["instId"].replace("-",""),
                        "status":"ANALIZ_BEKLENIYOR","price":last,
                        "change24h":round((last/op-1)*100,3),
                        "quote_volume24h":round(turnover,2)})
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"source":"OKX public spot",
             "market":"USDT","real_orders":False,"count":50,"analysis_available":False,"coins":records}
    Path("data.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PUBLIC MARKET SNAPSHOT OK: 50 liquid USDT spot coins; research signals intentionally unavailable.")

if __name__=="__main__":
    main()
