import json
import os
import urllib.request

TAVILY_API_KEY = "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"
GEMINI_API_KEY = "AQ.Ab8RN6IBmuJ_dqCUqfcM6r4v80KAKfTPL_xgfp36O3_IRq6CAw"

def tavily_search():
    url = "https://api.tavily.com/search"
    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": "site:kariyer.net OR site:linkedin.com/jobs OR site:savunmakariyer.com 'staj' OR 'yazılım mühendisi' OR 'aday mühendislik' 2026",
        "search_depth": "basic",
        "max_results": 10
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def parse_with_gemini(search_data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    Aşağıdaki arama sonuçlarından SADECE Mühendislik/Yazılım aktif staj ve iş ilanlarını çıkar.
    SADECE JSON döndür:
    {{"results": [{{"company": "...", "position": "...", "country": "TR", "url": "...", "type": ["staj"], "note": "..."}}]}}
    Arama Verisi: {json.dumps(search_data.get('results', []))}
    """
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json).get("results", [])

def main():
    db_file = "jobs.json"
    existing_jobs = []
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            existing_jobs = json.load(f)

    try:
        search_results = tavily_search()
        new_jobs = parse_with_gemini(search_results)
        
        added = 0
        for job in new_jobs:
            is_dup = any(e.get('company','').lower() == job.get('company','').lower() and 
                         e.get('position','').lower() == job.get('position','').lower() for e in existing_jobs)
            if not is_dup:
                existing_jobs.append({
                    "id": f"auto-{os.urandom(3).hex()}",
                    "company": job.get("company"),
                    "position": job.get("position"),
                    "country": job.get("country", "TR"),
                    "status": "open",
                    "type": job.get("type", ["staj"]),
                    "applicationOpen": True,
                    "links": [{"label": "İlan Linki", "url": job.get("url"), "domain": "link.com"}] if job.get("url") else [],
                    "note": job.get("note", "7/24 Otomatik Otomasyon Tarafından Eklendi")
                })
                added += 1

        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(existing_jobs, f, ensure_ascii=False, indent=2)
            
        print(f"Tarama tamamlandı. {added} yeni ilan eklendi.")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
