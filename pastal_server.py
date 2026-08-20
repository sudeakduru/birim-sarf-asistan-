import http.server
import socketserver
import json
import sqlite3
import urllib.request
import ssl
import os
import sys
import time
from agent_engine import PastalAgent

# Server configuration
PORT = int(os.environ.get("PORT", 3001))
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pastal_maliyet.db")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBQb6H0j18haWlg9musqOTS0WAbCVR8yE8")
GEMINI_MODEL = "gemini-2.5-flash"


# Setup SSL bypass for corporate networks
ssl_context = ssl._create_unverified_context()

# Initialize Database Schema
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if database has old schema (if it contains Kumas_ID in Maliyet_Calismalari but not Olculer_JSON)
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    columns = [col[1] for col in cursor.fetchall()]
    
    needs_rebuild = False
    if len(columns) > 0:
        if "Olculer_JSON" not in columns or "Kumas_ID" in columns:
            needs_rebuild = True
            
    if needs_rebuild:
        print("[MIGRATION] Cost-based schema found. Rebuilding tables for Physical Measurement-based schema...")
        cursor.execute("DROP TABLE IF EXISTS Maliyet_Calismalari")
        cursor.execute("DROP TABLE IF EXISTS Kumas_Kutuphanesi")
        cursor.execute("DROP TABLE IF EXISTS Model_Tanimlari")
        conn.commit()
    
    # 1. Model_Tanimlari (Alt, Üst, Elbise, Tulum)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Model_Tanimlari (
        Model_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Model_Adi TEXT NOT NULL,
        Urun_Grubu TEXT NOT NULL
    )
    """)
    
    # 2. Maliyet_Calismalari (Physical measurements & marker metrics)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Maliyet_Calismalari (
        Calisma_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Model_ID INTEGER NOT NULL,
        Kumas_Eni_cm INTEGER NOT NULL,
        Cekme_En_Yuzde REAL NOT NULL,
        Cekme_Boy_Yuzde REAL NOT NULL,
        Asorti_JSON TEXT NOT NULL,
        Olculer_JSON TEXT NOT NULL,
        Toplam_Asorti_Adet INTEGER NOT NULL,
        Hesaplanan_Birim_Metraj_M REAL,
        Hesaplanan_Pastal_Boyu_M REAL,
        Gerceklesen_Birim_Metraj_M REAL,
        Verimlilik_Yuzde REAL DEFAULT 90.0,
        Kayit_Tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Gerceklesen_Asorti_JSON TEXT,
        Gerceklesen_Kumas_Eni_cm INTEGER,
        Gerceklesen_Cekme_En_Yuzde REAL,
        Gerceklesen_Cekme_Boy_Yuzde REAL,
        FOREIGN KEY (Model_ID) REFERENCES Model_Tanimlari(Model_ID)
    )
    """)
    
    # Run Schema Migration to add Astar columns if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Astar_Eni_cm" not in current_cols:
        print("[MIGRATION] Adding Astar columns to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Astar_Eni_cm INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Astar_Cekme_En_Yuzde REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Astar_Cekme_Boy_Yuzde REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Hesaplanan_Astar_Birim_M REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Hesaplanan_Astar_Pastal_M REAL DEFAULT 0.0")
        conn.commit()
    
    # Run Schema Migration to add Tul columns if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Tul_Eni_cm" not in current_cols:
        print("[MIGRATION] Adding Tul columns to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Tul_Eni_cm INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Tul_Cekme_En_Yuzde REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Tul_Cekme_Boy_Yuzde REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Hesaplanan_Tul_Birim_M REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Hesaplanan_Tul_Pastal_M REAL DEFAULT 0.0")
        conn.commit()
    
    # Run Schema Migration to add Verimlilik_Yuzde if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Verimlilik_Yuzde" not in current_cols:
        print("[MIGRATION] Adding Verimlilik_Yuzde column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Verimlilik_Yuzde REAL DEFAULT 90.0")
        conn.commit()

    # Run Schema Migration to add Gerceklesen_Astar_Birim_M and Gerceklesen_Tul_Birim_M if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Gerceklesen_Astar_Birim_M" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Astar_Birim_M column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Astar_Birim_M REAL")
        conn.commit()
    if len(current_cols) > 0 and "Gerceklesen_Tul_Birim_M" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Tul_Birim_M column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Tul_Birim_M REAL")
        conn.commit()
        
    # Run Schema Migration to add Gerceklesen_Asorti_JSON if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Gerceklesen_Asorti_JSON" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Asorti_JSON column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Asorti_JSON TEXT")
        conn.commit()

    # Run Schema Migration to add Gerceklesen_Kumas_Eni_cm, Gerceklesen_Cekme_En_Yuzde, Gerceklesen_Cekme_Boy_Yuzde if missing
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Gerceklesen_Kumas_Eni_cm" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Kumas_Eni_cm column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Kumas_Eni_cm INTEGER")
        conn.commit()
    if len(current_cols) > 0 and "Gerceklesen_Cekme_En_Yuzde" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Cekme_En_Yuzde column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Cekme_En_Yuzde REAL")
        conn.commit()
    if len(current_cols) > 0 and "Gerceklesen_Cekme_Boy_Yuzde" not in current_cols:
        print("[MIGRATION] Adding Gerceklesen_Cekme_Boy_Yuzde column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Gerceklesen_Cekme_Boy_Yuzde REAL")
        conn.commit()
    if len(current_cols) > 0 and "Cep_Kumastan" not in current_cols:
        print("[MIGRATION] Adding Cep_Kumastan column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Cep_Kumastan INTEGER DEFAULT 1")
        conn.commit()

    # Agent migration columns and tables
    cursor.execute("PRAGMA table_info(Maliyet_Calismalari)")
    current_cols = [col[1] for col in cursor.fetchall()]
    if len(current_cols) > 0 and "Use_In_Calibration" not in current_cols:
        print("[MIGRATION] Adding Use_In_Calibration column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Use_In_Calibration INTEGER DEFAULT 1")
        conn.commit()
    if len(current_cols) > 0 and "Agent_Analysis_HTML" not in current_cols:
        print("[MIGRATION] Adding Agent_Analysis_HTML column to Maliyet_Calismalari...")
        cursor.execute("ALTER TABLE Maliyet_Calismalari ADD COLUMN Agent_Analysis_HTML TEXT")
        conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Agent_Decision_Logs (
        Log_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Calisma_ID INTEGER NOT NULL,
        Decision_Type TEXT NOT NULL,
        Is_Valid INTEGER NOT NULL DEFAULT 1,
        Is_Outlier INTEGER NOT NULL DEFAULT 0,
        Use_In_Calibration INTEGER NOT NULL DEFAULT 1,
        Reasoning TEXT,
        Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Calisma_ID) REFERENCES Maliyet_Calismalari(Calisma_ID)
    )
    """)
    conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ogrenme_Kayitlari (
        Log_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Hatalar TEXT,
        Dogrular TEXT,
        Tip TEXT,
        Tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    
    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM Model_Tanimlari")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO Model_Tanimlari (Model_Adi, Urun_Grubu)
        VALUES (?, ?)
        """, [
            ("Oversize T-shirt", "Üst Giyim"),
            ("Yazlık Çiçekli Elbise", "Elbise"),
            ("Kargo Denim Tulum", "Tulum")
        ])
    
    # Proactively clean up Fosfor models and their studies as requested by the user
    cursor.execute("SELECT Model_ID FROM Model_Tanimlari WHERE Model_Adi LIKE '%FOSFOR%'")
    fosfor_ids = [row[0] for row in cursor.fetchall()]
    for fid in fosfor_ids:
        cursor.execute("DELETE FROM Maliyet_Calismalari WHERE Model_ID = ?", (fid,))
        cursor.execute("DELETE FROM Model_Tanimlari WHERE Model_ID = ?", (fid,))
        
    conn.commit()
    conn.close()
import re

def parse_flexible_asorti(val):
    if not val:
        return {'S': 1, 'M': 2, 'L': 1}
    if isinstance(val, dict):
        return val
    
    val_str = str(val).strip()
    if not val_str:
        return {'S': 1, 'M': 2, 'L': 1}
        
    # 1. Standard JSON
    if val_str.startswith('{') and val_str.endswith('}'):
        try:
            d = json.loads(val_str)
            if isinstance(d, dict) and len(d) > 0:
                return d
        except Exception:
            pass

    # 2. Key-value pairs: "S:1, M:2, L:2", "S-1, M-2", "9-12(1), 1-2Y(2)", "36/1, 38/2"
    if ':' in val_str or '=' in val_str or '(' in val_str:
        pairs = re.findall(r'([A-Za-z0-9\-\.Y]+)\s*[:=\(\-]\s*(\d+)', val_str)
        if pairs:
            res = {}
            for sz, qty in pairs:
                sz = sz.strip('()')
                try:
                    q = int(qty)
                    if q > 0:
                        res[sz] = q
                except ValueError:
                    pass
            if res:
                return res

    # 3. Slash or dash pairs: "36/1, 38/2, 40/2" or "S/1, M/2"
    if '/' in val_str and ',' in val_str:
        parts = val_str.split(',')
        res = {}
        for p in parts:
            if '/' in p:
                s_q = p.split('/')
                if len(s_q) == 2:
                    sz = s_q[0].strip()
                    try:
                        q = int(s_q[1].strip())
                        if q > 0:
                            res[sz] = q
                    except ValueError:
                        pass
        if res:
            return res

    # 4. Positional ratios: "1-2-2-1", "1/2/2/1", "1 2 2 1"
    nums = re.findall(r'\d+', val_str)
    if nums:
        sizes = ['S', 'M', 'L', 'XL', 'XXL', '3XL']
        if len(nums) == 3:
            sizes = ['S', 'M', 'L']
        elif len(nums) == 5:
            sizes = ['XS', 'S', 'M', 'L', 'XL']
        elif len(nums) == 6:
            sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
            
        res = {}
        for idx, num in enumerate(nums):
            sz = sizes[idx] if idx < len(sizes) else f'Size_{idx+1}'
            res[sz] = int(num)
        return res
        
    return {'S': 1, 'M': 2, 'L': 1}

def get_smart_col_val(row, candidates):
    row_keys = list(row.keys())
    for cand in candidates:
        norm_cand = re.sub(r'[^a-z0-9]', '', cand.lower())
        for r_key in row_keys:
            norm_key = re.sub(r'[^a-z0-9]', '', str(r_key).lower())
            if norm_key == norm_cand or norm_key in norm_cand or norm_cand in norm_key:
                val = row[r_key]
                if val is not None and str(val).strip() != "":
                    return str(val).strip()
    return None

def parse_num(val, fallback):
    if val is None:
        return fallback
    try:
        s = str(val).replace(',', '.').strip()
        return float(s)
    except Exception:
        return fallback

import zipfile, xml.etree.ElementTree as ET

def parse_xlsx_native(file_bytes_io):
    try:
        zf = zipfile.ZipFile(file_bytes_io)
        shared_strings = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            ss_xml = zf.read('xl/sharedStrings.xml')
            root = ET.fromstring(ss_xml)
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag == 'si':
                    texts = [t.text for t in elem.iter() if (t.tag.split('}')[-1] if '}' in t.tag else t.tag) == 't' and t.text]
                    shared_strings.append(''.join(texts))
                
        sheet_name = None
        for name in zf.namelist():
            if 'xl/worksheets/sheet' in name and name.endswith('.xml'):
                sheet_name = name
                break
                
        if not sheet_name:
            return []
            
        sheet_xml = zf.read(sheet_name)
        root = ET.fromstring(sheet_xml)
        
        rows_data = []
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'row':
                row_cells = {}
                for c in elem:
                    c_tag = c.tag.split('}')[-1] if '}' in c.tag else c.tag
                    if c_tag == 'c':
                        cell_ref = c.attrib.get('r', '')
                        col_letter = ''.join(filter(str.isalpha, cell_ref))
                        cell_type = c.attrib.get('t', '')
                        val = ''
                        
                        for child in c:
                            ch_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            if ch_tag == 'v' and child.text:
                                val = child.text
                            elif ch_tag == 'is':
                                for t_el in child.iter():
                                    t_tag = t_el.tag.split('}')[-1] if '}' in t_el.tag else t_el.tag
                                    if t_tag == 't' and t_el.text:
                                        val = t_el.text
                                        
                        if cell_type == 's' and val.isdigit():
                            idx = int(val)
                            if idx < len(shared_strings):
                                val = shared_strings[idx]
                                
                        if col_letter:
                            row_cells[col_letter] = val
                if row_cells:
                    rows_data.append(row_cells)
                
        if len(rows_data) < 2:
            return []
            
        header_row = rows_data[0]
        result_rows = []
        for r in rows_data[1:]:
            row_dict = {}
            for col_letter, header_val in header_row.items():
                if header_val and str(header_val).strip():
                    row_dict[str(header_val).strip()] = str(r.get(col_letter, '')).strip()
            if any(v for v in row_dict.values()):
                result_rows.append(row_dict)
                
        return result_rows
    except Exception as e:
        print(f"[XLSX PARSER] Error parsing native xlsx: {e}")
        return []

def parse_raw_rows_to_json(raw_rows):
    items = []
    for i, row in enumerate(raw_rows):
        try:
            model_adi = get_smart_col_val(row, ['model_adi', 'model', 'model_kodu', 'style', 'modelname', 'style_name', 'model_name']) or f"Model-{i+1}"
            urun_grubu = get_smart_col_val(row, ['urun_grubu', 'urun', 'kategori', 'group', 'category']) or "Alt Giyim"
            
            kumas_eni_str = get_smart_col_val(row, ['kumas_eni_cm', 'kumas_eni', 'kumaseni', 'kumas eni', 'eni', 'en_cm', 'kumas_en', 'en'])
            kumas_eni = parse_num(kumas_eni_str, 175.0)
            
            cekme_en_str = get_smart_col_val(row, ['cekme_en_yuzde', 'cekme_en', 'encekme', 'en_cekme', 'cekmeen', 'cekme_eni', 'en_cekme_yuzde'])
            cekme_en = parse_num(cekme_en_str, 3.0)
            
            cekme_boy_str = get_smart_col_val(row, ['cekme_boy_yuzde', 'cekme_boy', 'boycekme', 'boy_cekme', 'cekmeboy', 'cekme_boyu', 'boy_cekme_yuzde'])
            cekme_boy = parse_num(cekme_boy_str, 3.0)
            
            asorti_raw = get_smart_col_val(row, ['asorti_json', 'asorti', 'beden_oranlari', 'asorti_dagilimi', 'beden_dagilimi', 'ratio', 'sizes'])
            asorti_data = parse_flexible_asorti(asorti_raw)
            
            real_tuketim_str = get_smart_col_val(row, ['gerceklesen_birim_metraj_m', 'gerceklesen_tuketim', 'gerceklesen_metraj', 'gerceklesen', 'atolye_gerceklesen', 'realize', 'atolye_tuketim', 'gerceklesen_m', 'gerceklesentuketim', 'gerceklesenmetraj'])
            real_tuketim = parse_num(real_tuketim_str, None) if real_tuketim_str is not None else None
            
            items.append({
                "model_adi": model_adi,
                "urun_grubu": urun_grubu,
                "kumas_eni_cm": kumas_eni,
                "cekme_en_yuzde": cekme_en,
                "cekme_boy_yuzde": cekme_boy,
                "verimlilik_yuzde": 90.0,
                "asorti": asorti_data,
                "olculer": {},
                "gerceklesen_tuketim": real_tuketim
            })
        except Exception as ex:
            print(f"[XLSX PARSER] Error converting row {i}: {ex}")
    return items

# Helper to call Gemini API for standard text tasks with retries
def call_gemini(prompt, system_prompt="You are a helpful assistant."):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[GEMINI] Attempt {attempt+1} calling Gemini failed: {e}")
            if attempt < 2:
                # Exponential backoff sleep (3s, 6s)
                time.sleep(3.0 * (attempt + 1))
            else:
                try:
                    print("Trying fallback model gemini-2.0-flash...")
                    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                    req = urllib.request.Request(fallback_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        return res_data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as fe:
                    print(f"Gemini fallback failed: {fe}")
    return None

# Helper to call Gemini API returning structured JSON with retries
def call_gemini_json(prompt, system_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[GEMINI JSON] Attempt {attempt+1} calling Gemini JSON failed: {e}")
            if attempt < 2:
                # Exponential backoff sleep (3s, 6s)
                time.sleep(3.0 * (attempt + 1))
            else:
                try:
                    print("Trying fallback model gemini-2.0-flash for JSON...")
                    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                    req = urllib.request.Request(fallback_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        return res_data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as fe:
                    print(f"Gemini fallback failed for JSON: {fe}")
    return None

# Initialize feedback calibration agent
agent = PastalAgent(DB_FILE, GEMINI_API_KEY, GEMINI_MODEL, call_gemini_json)

# Helper to call Gemini API with multimodal file data (PDF or image) with retries
def call_gemini_file(file_b64, mime_type, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": file_b64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[GEMINI FILE] Attempt {attempt+1} calling Gemini file failed: {e}")
            if attempt < 2:
                # Exponential backoff sleep (3s, 6s)
                time.sleep(3.0 * (attempt + 1))
            else:
                try:
                    print("Trying fallback model gemini-2.0-flash for multimodal analysis...")
                    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                    req = urllib.request.Request(fallback_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        return res_data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as fe:
                    print(f"Gemini fallback failed for multimodal: {fe}")
    return None

# Helper to robustly get measurement values case-insensitively with alias support
def get_val(d, keys, default=0.0):
    for k in keys:
        if k in d:
            return float(d[k])
        k_norm = k.lower().replace("_", "").replace(" ", "").replace("ş","s").replace("ı","i").replace("ğ","g").replace("ö","o").replace("ü","u").replace("ç","c")
        for dk in d.keys():
            dk_norm = dk.lower().replace("_", "").replace(" ", "").replace("ş","s").replace("ı","i").replace("ğ","g").replace("ö","o").replace("ü","u").replace("ç","c")
            if k_norm == dk_norm:
                return float(d[dk])
    return default

# Helper to calculate extra detail areas based on actual measurements (ruffles, plackets, straps, waistband height)
def calculate_extra_details_area(m):
    area_extra = 0.0
    
    # Helper to get value and the exact key matched
    def get_val_and_key(d, keys):
        for k in keys:
            if k in d:
                return float(d[k]), k
            k_norm = k.lower().replace("_", "").replace(" ", "").replace("ş","s").replace("ı","i").replace("ğ","g").replace("ö","o").replace("ü","u").replace("ç","c")
            for dk in d.keys():
                dk_norm = dk.lower().replace("_", "").replace(" ", "").replace("ş","s").replace("ı","i").replace("ğ","g").replace("ö","o").replace("ü","u").replace("ç","c")
                if k_norm == dk_norm:
                    return float(d[dk]), dk
        return 0.0, None

    # 1. Ruffles (Fırfır / Volan)
    firfir_eni, matched_key = get_val_and_key(m, ["firfir eni", "firfir_eni", "firfir_volan_eni_en_genis_nokta", "volan eni", "firfir"])
    if firfir_eni > 0 and matched_key:
        matched_key_lower = matched_key.lower()
        # Exclude sleeve/arm puffs or cuffs, neck puffs/collars from general body ruffles
        if "kol" not in matched_key_lower and "yaka" not in matched_key_lower:
            ref_length = get_val(m, ["etek_eni", "gogus", "bel", "basen"], 50.0)
            # Safe clamp: if etek_eni is massive circular (e.g. >100cm), clamp ref_length to chest/waist
            if ref_length > 100.0:
                ref_length = get_val(m, ["gogus", "bel"], 50.0)
            # Ruffles are gathered (typically 1.8x ratio) and have front & back (2 pieces).
            # Total length of ruffle strip is ref_length * 2 * 1.8 = ref_length * 3.6
            area_extra += (firfir_eni * (ref_length * 3.6)) * 1.15 / 10000.0
        
    # 2. Placket (Pat)
    pat_genisligi = get_val(m, ["pat genisligi", "pat_genisligi", "pat"], 0.0)
    if pat_genisligi > 0:
        ref_height = get_val(m, ["boy", "on_ag"], 50.0)
        # Plackets are typically double layer or front left + front right
        area_extra += (pat_genisligi * ref_height * 2.0) * 1.15 / 10000.0
        
    # 3. Straps (Askı)
    aski_eni = get_val(m, ["aski eni", "aski_eni", "aski"], 0.0)
    if aski_eni > 0:
        # Typically 2 straps of length around 35cm
        area_extra += 2.0 * (aski_eni * 35.0) * 1.15 / 10000.0
        
    return area_extra

# Pastal yerleşim verimliliği hesaplama motoru
def calculate_marker_efficiency(kumas_eni_cm, max_piece_width_cm, toplam_asorti_adet):
    """
    Kumaş enine göre kalıpların nasıl sığdığını analiz ederek pastal verimliliğini hesaplar.
    
    Mantık:
    - En geniş kalıp parçasının kumaş enine kaç kez sığdığına bakılır
    - Kalan boşluğa küçük parçaların (kol, yaka, cep vb.) sığma oranı tahmin edilir
    - Daha fazla parça (asorti) = daha iyi iç içe geçme (nesting) = daha yüksek verimlilik
    - Asla %100 olmaz, ortalama %86-87 civarı
    
    Returns: Verimlilik yüzdesi (82.0 - 95.0 arası)
    """
    if max_piece_width_cm <= 0 or kumas_eni_cm <= 0:
        return 87.0
    
    # Kumaş enine en geniş kalıp parçası kaç kez sığar?
    n_across = max(1, int(kumas_eni_cm / max_piece_width_cm))
    used_width = n_across * max_piece_width_cm
    gap_cm = kumas_eni_cm - used_width
    
    # Genişlik kullanım oranı
    width_ratio = used_width / kumas_eni_cm
    
    # Boşluğa küçük parçaların (kol, yaka, cep, biye vb.) sığma tahmini
    if gap_cm < 5:
        gap_fill = 0.90   # Neredeyse boşluk yok, çok verimli
    elif gap_cm < 15:
        gap_fill = 0.70   # Küçük boşluk, detay parçaları sığar
    elif gap_cm < 30:
        gap_fill = 0.50   # Orta boşluk, kısmen dolar
    elif gap_cm < 50:
        gap_fill = 0.35   # Büyük boşluk, az dolar
    else:
        gap_fill = 0.25   # Çok büyük boşluk
    
    # Efektif en kullanım oranı (ana parçalar + boşluk dolumu)
    effective_width_util = width_ratio + (1.0 - width_ratio) * gap_fill
    
    # Boy yönündeki kayıplar (parçalar arası boşluklar, kumaş başı-sonu fire)
    # Genellikle %92-94 arası (boy yönü daha verimli, parçalar uç uca dizilir)
    length_packing_factor = 0.93
    
    # Temel verimlilik = en kullanımı × boy kullanımı
    base_efficiency = effective_width_util * length_packing_factor * 100.0
    
    # Parça sayısı bonusu: daha fazla parça = daha iyi yerleşim imkanı
    # 8 adetten sonra her parça +0.25%, maksimum +4%
    piece_bonus = min(4.0, max(0.0, (toplam_asorti_adet - 8) * 0.25))
    
    efficiency = base_efficiency + piece_bonus
    
    # Kesin sınırlar: minimum %82, maksimum %95 (asla %100 olmaz)
    efficiency = max(82.0, min(95.0, efficiency))
    
    return round(efficiency, 1)

def predict_efficiency_with_ai(urun_grubu, kumas_eni_cm, asorti, olculer, max_piece_width_cm):
    # Constructing prompt for Gemini
    prompt = f"""
    Sen bir endüstriyel pastal yerleşim (optimum nesting) uzmanısın. Aşağıda detayları verilen tekstil kesim çalışmasının, kumaş eni, beden ölçüleri ve en geniş kalıp parçası eni göz önüne alınarak profesyonel bir pastal yerleşim programında (Gerber, Lectra vb.) yerleştirilmesi durumunda elde edilecek tahmini pastal yerleşim verimliliğini (%82.0 ile %95.0 arasında) tahmin etmeni istiyorum.
    
    ÜRÜN GRUBU: {urun_grubu}
    KUMAŞ ENİ: {kumas_eni_cm} cm
    EN GENİŞ KALIP PARÇASI ENİ: {max_piece_width_cm} cm
    ASORTİ DAĞILIMI (Adet/Oran): {json.dumps(asorti)}
    BEDEN ÖLÇÜLERİ: {json.dumps(olculer)}
    
    Yerleşim optimizasyon kuralları:
    - Kumaş eni ({kumas_eni_cm} cm) ile en geniş kalıp parçasının eni ({max_piece_width_cm} cm) arasındaki ilişki verimliliği doğrudan etkiler.
    - Eğer kumaş eni, en geniş kalıp parçasının eninin 3 katından küçükse (örneğin bu çalışmada kumaş eni 142 cm, en geniş kalıp eni ise {max_piece_width_cm} cm'dir; 3 x {max_piece_width_cm} = 151.2 cm > 142 cm), bu durumda kumaş enine yan yana 3 büyük panel (örn. arka beden) sığması imkansızdır. Bu durum yerleşimde geniş boşluklar bırakacağı için verimlilik ciddi oranda düşer ve genellikle %83.0 - %85.0 civarında kalır.
    - Eğer kumaş eni genişse (örneğin bebek/çocuk giyiminde kumaş eni 150 cm iken en geniş kalıp eni 25 cm ise), parçalar yan yana çok rahat dizilir ve verimlilik %90.0 - %95.0 arasına kadar çıkabilir.
    - Alt Giyim (pantolon vb.) ürünlerinde ön ve arka paneller ters-yüz edilerek ağ kısımları birbirinin içine geçebilir (interlocking). Ancak kumaş eni dar ve bedenler çok büyükse (40-50 beden arası kadın pantolonu gibi), bu interlocking esnekliği bile verimliliği %85.0'in üzerine çıkarmaya yetmeyebilir.
    
    Lütfen bu parametreleri gerçekçi bir şekilde analiz et ve yerleşim verimliliğini tahmin et.
    JSON formatında şu iki alanı döndür:
    - efficiency_percentage: (ondalıklı sayı, %82.0 - %95.0 arasında)
    - reasoning: (kısa Türkçe açıklama)
    """
    
    system_prompt = "Sen pastal yerleşim optimizasyonu ve tekstil mühendisliği analitiği uzmanı bir yapay zekasın. Kesin ve mantıklı yerleşim verimliliği tahminleri üretirsin."
    
    try:
        res_text = call_gemini_json(prompt, system_prompt)
        if res_text:
            res_json = json.loads(res_text)
            eff = float(res_json.get("efficiency_percentage", 87.0))
            # clamp between 82.0 and 95.0
            eff = max(82.0, min(95.0, eff))
            reasoning = res_json.get("reasoning", "")
            print(f"[AI EFFICIENCY] Predicted: {eff}% | Reason: {reasoning}")
            return round(eff, 1)
    except Exception as e:
        print(f"[AI EFFICIENCY] Error calling Gemini for efficiency prediction: {e}")
    
    return None

def get_size_measurements(olculer, size_name):
    if not olculer or not isinstance(olculer, dict):
        return {}
    size_name_str = str(size_name).strip()
    if size_name_str in olculer and olculer[size_name_str]:
        return olculer[size_name_str]
        
    for k, v in olculer.items():
        if not v: continue
        parts = [p.strip() for p in re.split(r'[/\-_ ]', k) if p.strip()]
        if size_name_str in parts:
            return v
            
    if '/' in size_name_str or '-' in size_name_str:
        parts = re.split(r'[/\-_ ]', size_name_str)
        for p in parts:
            p_clean = p.strip()
            if p_clean in olculer and olculer[p_clean]:
                return olculer[p_clean]
                
    size_num = re.sub(r'[^0-9]', '', size_name_str)
    if size_num:
        avail_numeric = []
        for k, v in olculer.items():
            if not v: continue
            k_nums = re.findall(r'\d+', k)
            for kn in k_nums:
                avail_numeric.append((abs(int(size_num) - int(kn)), k))
        if avail_numeric:
            avail_numeric.sort(key=lambda x: x[0])
            return olculer[avail_numeric[0][1]]
            
    available_sizes = list(olculer.keys())
    if available_sizes:
        return olculer[available_sizes[0]]
    return {}

def calculate_marker_cost(data, apply_learning=True):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    model_name = data.get("model_adi", "Gecici Model")
    urun_grubu = data.get("urun_grubu", "Alt Giyim")
    
    if "model_id" in data and data["model_id"]:
        cursor.execute("SELECT Model_Adi, Urun_Grubu FROM Model_Tanimlari WHERE Model_ID = ?", (data["model_id"],))
        model = cursor.fetchone()
        if model:
            model_name = model["Model_Adi"]
            urun_grubu = model["Urun_Grubu"]
        
    urun_grubu_lower = urun_grubu.lower().replace("ü", "u").replace("ö", "o").replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ç", "c")
    
    # Smart Auto-Correction of Urun_Grubu if PDF measurements indicate misclassification
    olculer_data = data.get("olculer", {})
    if olculer_data and isinstance(olculer_data, dict) and olculer_data.values():
        sample_m = list(olculer_data.values())[0]
        if isinstance(sample_m, dict):
            has_top_keys = any(("gogus" in k or "omuz" in k or "kol" in k or "yaka" in k or "pat_" in k or "roba" in k) and not ("paça" in k or "paca" in k or "bacak" in k) for k in sample_m.keys())
            has_bottom_keys = any(k in sample_m for k in ["yan_boy", "on_ag", "ic_ag", "baldir_genisligi", "paca_eni", "bacak_genisligi"])
            if has_top_keys and not has_bottom_keys and "alt" in urun_grubu_lower:
                boy_val = sample_m.get("boy") or sample_m.get("on_boy") or sample_m.get("arka_boy") or sample_m.get("omuzdan_boy_on") or sample_m.get("omuzdan_boy_arka") or sample_m.get("arka_ortadan_boy") or sample_m.get("omuzdan_boy_on_75cm_e_kadar") or sample_m.get("arka_ortadan_boy_75cm_e_kadar") or sample_m.get("omuzdan_on_boy_kemer_ribana_dahil") or sample_m.get("arka_ortadan_boy_kemer_ribana_dahil") or sample_m.get("omuzdan_arka_boy_kemer_ribana_dahil_75cm_e_kadar") or 0
                if "etek_eni" in sample_m or "etek_ucu_genisligi_duz" in sample_m or "etek_ucu_genisligi_on" in sample_m or boy_val > 80:
                    urun_grubu_lower = "elbise"
                else:
                    urun_grubu_lower = "ust giyim"
            elif has_bottom_keys and not has_top_keys and ("ust" in urun_grubu_lower or "elbise" in urun_grubu_lower):
                urun_grubu_lower = "alt giyim"
    
    kumas_correction_factor = 1.0
    astar_correction_factor = 1.0
    tul_correction_factor = 1.0
    
    kumas_samples_count = 0
    astar_samples_count = 0
    tul_samples_count = 0
    
    if apply_learning:
        # 1. Main Fabric calibration: Single Unified Learning Pool across all past workspace & AI training records
        ug_key = urun_grubu_lower[:3] if len(urun_grubu_lower) >= 3 else urun_grubu_lower
        cursor.execute("""
            SELECT Asorti_JSON, Olculer_JSON, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde, 
                   Verimlilik_Yuzde, Gerceklesen_Birim_Metraj_M, Astar_Eni_cm, Astar_Cekme_En_Yuzde, Astar_Cekme_Boy_Yuzde,
                   Tul_Eni_cm, Tul_Cekme_En_Yuzde, Tul_Cekme_Boy_Yuzde, Gerceklesen_Asorti_JSON,
                   Gerceklesen_Kumas_Eni_cm, Gerceklesen_Cekme_En_Yuzde, Gerceklesen_Cekme_Boy_Yuzde,
                   Cep_Kumastan
            FROM Maliyet_Calismalari c
            JOIN Model_Tanimlari m ON c.Model_ID = m.Model_ID
            WHERE c.Gerceklesen_Birim_Metraj_M IS NOT NULL 
              AND c.Gerceklesen_Birim_Metraj_M > 0
              AND (c.Use_In_Calibration IS NULL OR c.Use_In_Calibration = 1)
            ORDER BY 
              CASE WHEN LOWER(m.Urun_Grubu) LIKE '%' || ? || '%' THEN 0 ELSE 1 END,
              c.Kayit_Tarihi DESC
        """, (ug_key,))
        past_kumas_records = cursor.fetchall()
        kumas_ratios = []
        for row in past_kumas_records:
            try:
                # Use Gerceklesen_Asorti_JSON if available, otherwise fall back to Asorti_JSON
                asorti_data = row["Gerceklesen_Asorti_JSON"]
                if asorti_data and asorti_data.strip() != "":
                    asorti = json.loads(asorti_data)
                else:
                    asorti = json.loads(row["Asorti_JSON"])

                kumas_eni = row["Gerceklesen_Kumas_Eni_cm"] if row["Gerceklesen_Kumas_Eni_cm"] else row["Kumas_Eni_cm"]
                cekme_en = row["Gerceklesen_Cekme_En_Yuzde"] if row["Gerceklesen_Cekme_En_Yuzde"] is not None else row["Cekme_En_Yuzde"]
                cekme_boy = row["Gerceklesen_Cekme_Boy_Yuzde"] if row["Gerceklesen_Cekme_Boy_Yuzde"] is not None else row["Cekme_Boy_Yuzde"]
                cep_kumastan_val = row["Cep_Kumastan"] if "Cep_Kumastan" in row.keys() and row["Cep_Kumastan"] is not None else 1

                h_data = {
                    "model_id": data["model_id"],
                    "kumas_eni_cm": kumas_eni,
                    "cekme_en_yuzde": cekme_en,
                    "cekme_boy_yuzde": cekme_boy,
                    "verimlilik_yuzde": row["Verimlilik_Yuzde"] or 90.0,
                    "asorti": asorti,
                    "olculer": json.loads(row["Olculer_JSON"]),
                    "cep_kumastan": bool(cep_kumastan_val),
                    "astar_hesapla": row["Astar_Eni_cm"] > 0,
                    "astar_eni_cm": row["Astar_Eni_cm"],
                    "astar_cekme_en_yuzde": row["Astar_Cekme_En_Yuzde"],
                    "astar_cekme_boy_yuzde": row["Astar_Cekme_Boy_Yuzde"],
                    "tul_hesapla": row["Tul_Eni_cm"] > 0,
                    "tul_eni_cm": row["Tul_Eni_cm"],
                    "tul_cekme_en_yuzde": row["Tul_Cekme_En_Yuzde"],
                    "tul_cekme_boy_yuzde": row["Tul_Cekme_Boy_Yuzde"]
                }
                raw_res = calculate_marker_cost(h_data, apply_learning=False)
                raw_birim = raw_res["birim_metraj_m"]
                actual_birim = float(row["Gerceklesen_Birim_Metraj_M"])
                if raw_birim > 0 and actual_birim > 0:
                    kumas_ratios.append(actual_birim / raw_birim)
            except Exception as ex:
                print(f"[LEARNING] Error parsing main fabric calibration record: {ex}")
        if kumas_ratios:
            kumas_correction_factor = sum(kumas_ratios) / len(kumas_ratios)
            kumas_samples_count = len(kumas_ratios)
            print(f"[LEARNING] Main Fabric: Calibrated with {kumas_samples_count} records. Factor: {kumas_correction_factor:.4f}")

        # 2. Astar calibration
        cursor.execute("""
            SELECT Asorti_JSON, Olculer_JSON, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde, 
                   Verimlilik_Yuzde, Gerceklesen_Astar_Birim_M, Astar_Eni_cm, Astar_Cekme_En_Yuzde, Astar_Cekme_Boy_Yuzde,
                   Tul_Eni_cm, Tul_Cekme_En_Yuzde, Tul_Cekme_Boy_Yuzde, Gerceklesen_Asorti_JSON,
                   Gerceklesen_Kumas_Eni_cm, Gerceklesen_Cekme_En_Yuzde, Gerceklesen_Cekme_Boy_Yuzde
            FROM Maliyet_Calismalari c
            JOIN Model_Tanimlari m ON c.Model_ID = m.Model_ID
            WHERE m.Urun_Grubu = ? 
              AND c.Gerceklesen_Astar_Birim_M IS NOT NULL 
              AND c.Gerceklesen_Astar_Birim_M > 0
              AND (c.Use_In_Calibration IS NULL OR c.Use_In_Calibration = 1)
            ORDER BY c.Kayit_Tarihi DESC
        """, (urun_grubu,))
        past_astar_records = cursor.fetchall()
        astar_ratios = []
        for row in past_astar_records:
            try:
                # Use Gerceklesen_Asorti_JSON if available, otherwise fall back to Asorti_JSON
                asorti_data = row["Gerceklesen_Asorti_JSON"]
                if asorti_data and asorti_data.strip() != "":
                    asorti = json.loads(asorti_data)
                else:
                    asorti = json.loads(row["Asorti_JSON"])

                kumas_eni = row["Gerceklesen_Kumas_Eni_cm"] if row["Gerceklesen_Kumas_Eni_cm"] else row["Kumas_Eni_cm"]
                cekme_en = row["Gerceklesen_Cekme_En_Yuzde"] if row["Gerceklesen_Cekme_En_Yuzde"] is not None else row["Cekme_En_Yuzde"]
                cekme_boy = row["Gerceklesen_Cekme_Boy_Yuzde"] if row["Gerceklesen_Cekme_Boy_Yuzde"] is not None else row["Cekme_Boy_Yuzde"]

                h_data = {
                    "model_id": data["model_id"],
                    "kumas_eni_cm": kumas_eni,
                    "cekme_en_yuzde": cekme_en,
                    "cekme_boy_yuzde": cekme_boy,
                    "verimlilik_yuzde": row["Verimlilik_Yuzde"] or 90.0,
                    "asorti": asorti,
                    "olculer": json.loads(row["Olculer_JSON"]),
                    "astar_hesapla": True,
                    "astar_eni_cm": row["Astar_Eni_cm"],
                    "astar_cekme_en_yuzde": row["Astar_Cekme_En_Yuzde"],
                    "astar_cekme_boy_yuzde": row["Astar_Cekme_Boy_Yuzde"],
                    "tul_hesapla": row["Tul_Eni_cm"] > 0,
                    "tul_eni_cm": row["Tul_Eni_cm"],
                    "tul_cekme_en_yuzde": row["Tul_Cekme_En_Yuzde"],
                    "tul_cekme_boy_yuzde": row["Tul_Cekme_Boy_Yuzde"]
                }
                raw_res = calculate_marker_cost(h_data, apply_learning=False)
                raw_birim = raw_res["astar_birim_metraj_m"]
                actual_birim = float(row["Gerceklesen_Astar_Birim_M"])
                if raw_birim > 0 and actual_birim > 0:
                    astar_ratios.append(actual_birim / raw_birim)
            except Exception as ex:
                print(f"[LEARNING] Error parsing astar calibration record: {ex}")
        if astar_ratios:
            astar_correction_factor = sum(astar_ratios) / len(astar_ratios)
            astar_samples_count = len(astar_ratios)
            print(f"[LEARNING] Astar: Calibrated with {astar_samples_count} records. Factor: {astar_correction_factor:.4f}")

        # 3. Tulle calibration
        cursor.execute("""
            SELECT Asorti_JSON, Olculer_JSON, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde, 
                   Verimlilik_Yuzde, Gerceklesen_Tul_Birim_M, Astar_Eni_cm, Astar_Cekme_En_Yuzde, Astar_Cekme_Boy_Yuzde,
                   Tul_Eni_cm, Tul_Cekme_En_Yuzde, Tul_Cekme_Boy_Yuzde, Gerceklesen_Asorti_JSON,
                   Gerceklesen_Kumas_Eni_cm, Gerceklesen_Cekme_En_Yuzde, Gerceklesen_Cekme_Boy_Yuzde
            FROM Maliyet_Calismalari c
            JOIN Model_Tanimlari m ON c.Model_ID = m.Model_ID
            WHERE m.Urun_Grubu = ? 
              AND c.Gerceklesen_Tul_Birim_M IS NOT NULL 
              AND c.Gerceklesen_Tul_Birim_M > 0
              AND (c.Use_In_Calibration IS NULL OR c.Use_In_Calibration = 1)
            ORDER BY c.Kayit_Tarihi DESC
        """, (urun_grubu,))
        past_tul_records = cursor.fetchall()
        tul_ratios = []
        for row in past_tul_records:
            try:
                # Use Gerceklesen_Asorti_JSON if available, otherwise fall back to Asorti_JSON
                asorti_data = row["Gerceklesen_Asorti_JSON"]
                if asorti_data and asorti_data.strip() != "":
                    asorti = json.loads(asorti_data)
                else:
                    asorti = json.loads(row["Asorti_JSON"])

                kumas_eni = row["Gerceklesen_Kumas_Eni_cm"] if row["Gerceklesen_Kumas_Eni_cm"] else row["Kumas_Eni_cm"]
                cekme_en = row["Gerceklesen_Cekme_En_Yuzde"] if row["Gerceklesen_Cekme_En_Yuzde"] is not None else row["Cekme_En_Yuzde"]
                cekme_boy = row["Gerceklesen_Cekme_Boy_Yuzde"] if row["Gerceklesen_Cekme_Boy_Yuzde"] is not None else row["Cekme_Boy_Yuzde"]

                h_data = {
                    "model_id": data["model_id"],
                    "kumas_eni_cm": kumas_eni,
                    "cekme_en_yuzde": cekme_en,
                    "cekme_boy_yuzde": cekme_boy,
                    "verimlilik_yuzde": row["Verimlilik_Yuzde"] or 90.0,
                    "asorti": asorti,
                    "olculer": json.loads(row["Olculer_JSON"]),
                    "astar_hesapla": row["Astar_Eni_cm"] > 0,
                    "astar_eni_cm": row["Astar_Eni_cm"],
                    "astar_cekme_en_yuzde": row["Astar_Cekme_En_Yuzde"],
                    "astar_cekme_boy_yuzde": row["Astar_Cekme_Boy_Yuzde"],
                    "tul_hesapla": True,
                    "tul_eni_cm": row["Tul_Eni_cm"],
                    "tul_cekme_en_yuzde": row["Tul_Cekme_En_Yuzde"],
                    "tul_cekme_boy_yuzde": row["Tul_Cekme_Boy_Yuzde"]
                }
                raw_res = calculate_marker_cost(h_data, apply_learning=False)
                raw_birim = raw_res["tul_birim_metraj_m"]
                actual_birim = float(row["Gerceklesen_Tul_Birim_M"])
                if raw_birim > 0 and actual_birim > 0:
                    tul_ratios.append(actual_birim / raw_birim)
            except Exception as ex:
                print(f"[LEARNING] Error parsing tulle calibration record: {ex}")
        if tul_ratios:
            tul_correction_factor = sum(tul_ratios) / len(tul_ratios)
            tul_samples_count = len(tul_ratios)
            print(f"[LEARNING] Tulle: Calibrated with {tul_samples_count} records. Factor: {tul_correction_factor:.4f}")
            
    conn.close()
    
    kumas_eni_cm = int(data.get("kumas_eni_cm", 175))
    asorti = data.get("asorti", {})
    olculer = data.get("olculer", {})
    cekme_en = float(data.get("cekme_en_yuzde", 0.0))
    cekme_boy = float(data.get("cekme_boy_yuzde", 0.0))
    cep_kumastan = data.get("cep_kumastan", True)
    # verimlilik_yuzde: Dinamik olarak hesaplanacak (kalıp analizi sonrası)
    
    # 1. Calculate Toplam Asorti Adet
    toplam_asorti_adet = sum(int(v) for v in asorti.values() if str(v).isdigit())
    if toplam_asorti_adet == 0:
        toplam_asorti_adet = 1
        
    # 2. Calculate Cekme Katsayisi
    cekme_faktoru = (1.0 + abs(cekme_en) / 100.0) * (1.0 + abs(cekme_boy) / 100.0)
    
    # 3. Calculate net pattern area for each active size
    net_areas = {}
    total_net_area_m2 = 0.0
    total_cep_net_area_m2 = 0.0
    max_piece_width_cm = 0.0  # En geniş kalıp parçasını takip et (verimlilik hesabı için)
    
    for size_name, qty in asorti.items():
        qty = int(qty)
        if qty <= 0:
            continue
            
        m = get_size_measurements(olculer, size_name)
        
        # Calculate area based on Urun_Grubu
        if "alt" in urun_grubu_lower:
            bel = get_val(m, ["bel", "waist", "w14", "w13", "w222", "bel_kavisli_genisligi_ustten", "bel_genisligi_kavisli_alttan", "bel_genisligi", "bel_kavisli_genisligi"], 38.0)
            basen = get_val(m, ["basen", "hip", "hips", "w59", "basen_genisligi"], 50.0)
            if bel > 55.0: bel = bel / 2.0
            if basen > 65.0: basen = basen / 2.0
            on_ag = get_val(m, ["on ag", "on_ag", "front rise", "front_rise", "ag", "l19", "on_ag_uzunlugu_kemer_dahil", "on_ag_uzunlugu", "on_ag_kemer_dahil"], 24.0)
            arka_ag = get_val(m, ["arka ag", "arka_ag", "back rise", "back_rise", "l21", "arka_ag_uzunlugu_kemer_dahil", "arka_ag_uzunlugu", "arka_ag_kemer_dahil"], on_ag * 1.35)
            ic_ag = get_val(m, ["ic ag", "ic_ag", "inseam", "ic boy", "ic_boy", "l259", "l103", "ic_boy_40_cm_alti", "ic_boy_40cm_alti"], 0.0)
            etek_pile_acik = get_val(m, ["etek_ucu_genisligi_pile_acik", "etek_eni_pile_acik", "etek_eni", "hem_width"], 0.0)
            
            default_yan_boy = 98.0
            if on_ag > 0 and ic_ag > 0:
                default_yan_boy = on_ag + ic_ag
                
            yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "pantolon_boyu", "toplam_boy", "boy"], default_yan_boy)
            if yan_boy < 45.0:
                yan_boy = 98.0
            paca_eni = get_val(m, ["paca eni", "paca_eni", "hem width", "hem_width", "paca", "w252", "w178", "paca_genisligi_ic_boy_16_40_cm_arasi", "paca_genisligi", "paca_genisligi_ic_boy"], 22.0)
            
            kemer_h = get_val(m, ["kemer yuksekligi", "kemer_yuksekligi", "kemer", "b04", "kemer_boyu"], 4.0)
            basen_drop = get_val(m, ["basen_dusuklugu_kemer_dahil_yan", "basen_dusuklugu", "basen_drop", "basen_dusuklugu_kemer_dahil", "w17", "w17_basen_dusuklugu"], 0.0)
            
            if basen_drop <= 0:
                basen_drop = on_ag * 0.65
            
            effective_height = max(1.0, yan_boy - kemer_h)
            bacak_boy = max(1.0, effective_height - basen_drop)
            
            if etek_pile_acik > 60.0:
                total_pano_m2 = (2.0 * ((bel/2.0 + etek_pile_acik) / 2.0) * yan_boy) / 10000.0
                max_piece_width_cm = max(max_piece_width_cm, etek_pile_acik)
            else:
                on_bel = bel / 4.0
                on_basen = basen / 4.0 + on_ag * 0.30
                on_paca = paca_eni
                
                on_ust_alan = (on_bel + on_basen) / 2.0 * basen_drop
                on_alt_alan = (on_basen + on_paca) / 2.0 * bacak_boy
                
                arka_bel = bel / 4.0 + 2.0
                arka_basen = basen / 4.0 + arka_ag * 0.45
                arka_paca = paca_eni
                
                arka_ust_alan = (arka_bel + arka_basen) / 2.0 * basen_drop
                arka_alt_alan = (arka_basen + arka_paca) / 2.0 * bacak_boy
                
                total_pano_m2 = (2.0 * (on_ust_alan + on_alt_alan) + 2.0 * (arka_ust_alan + arka_alt_alan)) / 10000.0
                crotch_mult = 1.30 if paca_eni > 26.0 else 1.15
                total_pano_m2 *= crotch_mult
                max_piece_width_cm = max(max_piece_width_cm, arka_basen * 2, on_basen * 2, paca_eni * 2)
            
            area_kemer = bel * (kemer_h * 2.0) * 1.15 / 10000.0
            
            # Detay parçaları: cep torbaları, patlet, köprü vb.
            cep_torba_eni = get_val(m, ["on_cep_torba_eni", "cep_eni"], 9.0)
            cep_torba_boyu = get_val(m, ["on_cep_torba_boyu", "cep_boyu"], 12.0)
            area_cep = 2.0 * 2.0 * cep_torba_eni * cep_torba_boyu / 10000.0  # 2 cep x 2 katman
            
            if cep_kumastan:
                area_detay_cep = area_cep
            else:
                area_detay_cep = 0.0
                total_cep_net_area_m2 += area_cep * qty
            
            patlet_eni = get_val(m, ["patlet_eni", "patlet eni"], 3.0)
            patlet_boyu = get_val(m, ["patlet_boyu", "patlet boyu"], 12.0)
            area_patlet = patlet_eni * patlet_boyu / 10000.0
            
            kopru_eni = get_val(m, ["kopru_eni", "kopru eni"], 1.0)
            kopru_boyu = get_val(m, ["kopru_boyu", "kopru boyu"], 4.25)
            area_kopru = kopru_eni * kopru_boyu * 2.0 / 10000.0
            
            extra_details = calculate_extra_details_area(m)
            area_detay = max(area_detay_cep + area_patlet + area_kopru, extra_details)
            
            # Dikiş payı %15
            net_area = (total_pano_m2 + area_kemer + area_detay) * 1.15
            max_piece_width_cm = max(max_piece_width_cm, basen, paca_eni)
            
        elif "ust" in urun_grubu_lower or "orme" in urun_grubu_lower:
            gogus = get_val(m, ["gogus", "gogus_genisligi_on", "chest", "half chest", "half_chest", "width"], 50.0)
            boy = get_val(m, ["boy", "omuzdan_boy_on_75cm_e_kadar", "arka_ortadan_boy_75cm_e_kadar", "arka_ortadan_boy", "length", "body length", "body_length"], 65.0)
            kol_boyu = get_val(m, ["kol boyu", "kol_boyu", "kol_boyu_arka_ortadan", "kol_boyu_omuzdan", "kol_boyu_t_kol_uzun_kol", "kol_boyu_uzun_kol", "sleeve length", "sleeve_length", "kol"], 20.0)
            
            area_front = gogus * boy * 1.15 / 10000.0
            area_back = gogus * boy * 1.15 / 10000.0
            sleeve_width = get_val(m, ["kolevi_duz", "kolevi_duz_t_kol", "pazu_genisligi_t_kol", "pazu_genisligi", "kolevi", "kol_agzi_genisligi_kisa_kol_gergin", "sleeve_width"], boy / 3.0)
            area_kol = 2.0 * kol_boyu * sleeve_width * 1.15 / 10000.0 if kol_boyu > 0 else 0.0
            
            extra_details = calculate_extra_details_area(m)
            area_yaka = max(0.03, extra_details)
            net_area = area_front + area_back + area_kol + area_yaka
            max_piece_width_cm = max(max_piece_width_cm, gogus)
            
        elif "elbise" in urun_grubu_lower:
            gogus = get_val(m, ["gogus", "gogus_genisligi_on", "chest", "width"], 48.0)
            basen = get_val(m, ["basen", "hip", "hips"], 85.0)
            
            # Strap dress check
            aski_haric = get_val(m, ["on_boy_aski_haric", "boy_aski_haric"], 0.0)
            aski_boyu = get_val(m, ["aski_boyu_toplam", "aski_boyu", "askilik_boyu"], 15.0)
            if aski_haric > 0:
                boy = aski_haric + (aski_boyu / 2.0)
            else:
                boy = get_val(m, ["boy", "omuzdan_boy_on_75cm_e_kadar", "arka_ortadan_boy_75cm_e_kadar", "arka_ortadan_boy", "length", "total length", "total_length"], 90.0)
                
            kol_boyu = get_val(m, ["kol boyu", "kol_boyu", "kol_boyu_arka_ortadan", "kol_boyu_omuzdan", "kol_boyu_t_kol_uzun_kol", "kol_boyu_uzun_kol", "sleeve length", "sleeve_length", "kol"], 0.0)
            etek_eni = get_val(m, ["etek eni", "etek_eni", "etek_ucu_genisligi_kavisli", "etek_ucu_genisligi_on", "etek_ucu_genisligi_duz", "hem width", "hem_width", "etek"], 60.0)
            
            ust_bel_yeri = get_val(m, ["ust_bel_yeri_omuz_basindan_on", "ust_bel_yeri_omuz_basindan_arka", "bel_kesik_yeri_omuz_basindan_on", "bel_yeri_on_aski_noktasindan", "bel_kesik_yeri_on", "bel_kesik_yeri_arka", "bel_kesik_yeri", "ust_bel_yeri", "bodice_length"], 0.0)
            if 0.0 < ust_bel_yeri < boy:
                skirt_height = boy - ust_bel_yeri
                area_front = (gogus * ust_bel_yeri + ((gogus + etek_eni) / 2.0) * skirt_height) * 1.15 / 10000.0
                area_back = (gogus * ust_bel_yeri + ((gogus + etek_eni) / 2.0) * skirt_height) * 1.15 / 10000.0
            else:
                area_front = ((gogus + etek_eni) / 2.0) * boy * 1.15 / 10000.0
                area_back = ((gogus + etek_eni) / 2.0) * boy * 1.15 / 10000.0
                
            sleeve_width = get_val(m, ["kolevi_duz", "kolevi_duz_t_kol", "pazu_genisligi_t_kol", "pazu_genisligi", "kolevi", "kol_agzi_genisligi_kisa_kol_gergin", "sleeve_width"], 20.0)
            if sleeve_width == 20.0 and boy < 75.0:
                sleeve_width = 14.0
            area_kol = 2.0 * kol_boyu * sleeve_width * 1.15 / 10000.0 if kol_boyu > 0 else 0.0
            
            extra_details = calculate_extra_details_area(m)
            area_detay = max(0.04, extra_details)
            net_area = area_front + area_back + area_kol + area_detay
            max_piece_width_cm = max(max_piece_width_cm, gogus, etek_eni)
            
        elif "tulum" in urun_grubu_lower:
            gogus = get_val(m, ["gogus", "chest", "width"], 48.0)
            basen = get_val(m, ["basen", "hip", "hips"], 85.0)
            boy = get_val(m, ["boy", "length", "total length", "total_length"], 120.0)
            ic_ag = get_val(m, ["ic ag", "ic_ag", "inseam", "ic boy", "ic_boy"], 65.0)
            kol_boyu = get_val(m, ["kol boyu", "kol_boyu", "sleeve length", "sleeve_length", "kol"], 0.0)
            paca_eni = get_val(m, ["paca eni", "paca_eni", "hem width", "hem_width", "paca"], 22.0)
            
            area_upper = gogus * (boy - ic_ag) * 2.0 * 1.15 / 10000.0
            area_lower = 2.0 * ((basen / 2.0 + paca_eni) / 2.0) * ic_ag * 1.15 / 10000.0
            
            # Sleeve width: use armhole/kolevi if available, otherwise default to 20.0
            sleeve_width = get_val(m, ["kolevi_duz", "kolevi", "kol_agzi_genisligi_kisa_kol_gergin", "sleeve_width"], 20.0)
            if sleeve_width == 20.0 and boy < 100.0: # child/baby size clamp
                sleeve_width = 14.0
            area_kol = 2.0 * kol_boyu * sleeve_width * 1.15 / 10000.0 if kol_boyu > 0 else 0.0
            
            extra_details = calculate_extra_details_area(m)
            area_detay = max(0.05, extra_details)
            net_area = area_upper + area_lower + area_kol + area_detay
            max_piece_width_cm = max(max_piece_width_cm, gogus, basen / 4.0)
            
        else:
            # General default
            basen = get_val(m, ["basen", "hip", "hips"], 80.0)
            yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "boy"], 30.0)
            net_area = (basen * yan_boy * 2.2 * 1.15) / 10000.0
            max_piece_width_cm = max(max_piece_width_cm, basen / 2.0)
            
        net_areas[size_name] = round(net_area, 4)
        total_net_area_m2 += net_area * qty
        
    # 4. Dinamik Pastal Verimliliği Hesabı
    verimlilik_yuzde = None
    if apply_learning:
        verimlilik_yuzde = predict_efficiency_with_ai(urun_grubu, kumas_eni_cm, asorti, olculer, max_piece_width_cm)
        
    if verimlilik_yuzde is None:
        verimlilik_yuzde = calculate_marker_efficiency(kumas_eni_cm, max_piece_width_cm, toplam_asorti_adet)
        print(f"[MARKER] Matematiksel Verimlilik: {verimlilik_yuzde}% (en geniş kalıp: {max_piece_width_cm:.1f}cm, kumaş eni: {kumas_eni_cm}cm, asorti: {toplam_asorti_adet} adet)")
    else:
        print(f"[MARKER] AI Destekli Verimlilik: {verimlilik_yuzde}% (en geniş kalıp: {max_piece_width_cm:.1f}cm, kumaş eni: {kumas_eni_cm}cm, asorti: {toplam_asorti_adet} adet)")
    
    # 5. Pastal Boyu & Ortalama Birim Metraj (Metre)
    kumas_eni_m = kumas_eni_cm / 100.0
    pastal_boyu_m_raw = (total_net_area_m2 * cekme_faktoru) / (kumas_eni_m * (verimlilik_yuzde / 100.0))
    birim_metraj_m_raw = pastal_boyu_m_raw / toplam_asorti_adet
    
    # Apply learning correction factor
    pastal_boyu_m = pastal_boyu_m_raw * kumas_correction_factor
    birim_metraj_m = birim_metraj_m_raw * kumas_correction_factor
    
    # 5. Lining (Astar) Calculations
    astar_hesapla = data.get("astar_hesapla", False)
    astar_birim_metraj_m = 0.0
    astar_pastal_boyu_m = 0.0
    
    if astar_hesapla:
        astar_eni_cm = int(data.get("astar_eni_cm", 140))
        astar_cekme_en = float(data.get("astar_cekme_en_yuzde", 0.0))
        astar_cekme_boy = float(data.get("astar_cekme_boy_yuzde", 0.0))
        astar_cekme_faktoru = (1.0 + abs(astar_cekme_en) / 100.0) * (1.0 + abs(astar_cekme_boy) / 100.0)
        
        total_astar_net_area_m2 = 0.0
        for size_name, qty in asorti.items():
            qty = int(qty)
            if qty <= 0:
                continue
            m = olculer.get(size_name, {})
            
            if "alt" in urun_grubu_lower:
                basen = get_val(m, ["basen", "hip", "hips"], 80.0)
                on_ag = get_val(m, ["on ag", "on_ag", "front rise", "front_rise", "ag"], 20.0)
                ic_ag = get_val(m, ["ic ag", "ic_ag", "inseam", "ic boy", "ic_boy"], 0.0)
                default_yan_boy = 30.0
                if on_ag > 0 and ic_ag > 0:
                    default_yan_boy = on_ag + ic_ag
                yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "boy"], default_yan_boy)
                paca_eni = get_val(m, ["paca eni", "paca_eni", "hem width", "hem_width", "paca"], 25.0)
                
                area_front = 2.0 * ((basen / 4.0 + paca_eni) / 2.0) * max(1.0, yan_boy - 4.0) * 1.15 / 10000.0
                area_back = 2.0 * ((basen / 4.0 + 4.0 + paca_eni) / 2.0) * max(1.0, yan_boy - 4.0) * 1.15 / 10000.0
                astar_size_area = area_front + area_back
            elif "ust" in urun_grubu_lower or "orme" in urun_grubu_lower:
                gogus = get_val(m, ["gogus", "chest", "half chest", "half_chest", "width"], 50.0)
                boy = get_val(m, ["boy", "length", "body length", "body_length"], 65.0)
                kol_boyu = get_val(m, ["kol boyu", "kol_boyu", "sleeve length", "sleeve_length", "kol"], 20.0)
                
                area_front = gogus * boy * 1.15 / 10000.0
                area_back = gogus * boy * 1.15 / 10000.0
                area_kol = 2.0 * kol_boyu * (boy / 3.0) * 1.15 / 10000.0
                astar_size_area = area_front + area_back + area_kol
            elif "elbise" in urun_grubu_lower:
                gogus = get_val(m, ["gogus", "chest", "width"], 48.0)
                boy = get_val(m, ["boy", "length", "total length", "total_length"], 90.0)
                
                # Prioritize flat/lining hem width for the lining skirt
                astar_etek_eni = get_val(m, ["etek_ucu_genisligi_duz_astar", "astar_etek_eni", "astar_etek", "duz_etek_eni"], 60.0)
                if astar_etek_eni == 60.0:
                    astar_etek_eni = get_val(m, ["etek eni", "etek_eni", "hem width", "hem_width", "etek"], 60.0)
                
                ust_bel_yeri = get_val(m, ["ust_bel_yeri_omuz_basindan_on", "ust_bel_yeri_omuz_basindan_arka", "ust_bel_yeri", "bodice_length"], 0.0)
                if 0.0 < ust_bel_yeri < boy:
                    skirt_height = boy - ust_bel_yeri
                    area_front = (gogus * ust_bel_yeri + ((gogus + astar_etek_eni) / 2.0) * skirt_height) * 1.15 / 10000.0
                    area_back = (gogus * ust_bel_yeri + ((gogus + astar_etek_eni) / 2.0) * skirt_height) * 1.15 / 10000.0
                else:
                    area_front = ((gogus + astar_etek_eni) / 2.0) * boy * 1.15 / 10000.0
                    area_back = ((gogus + astar_etek_eni) / 2.0) * boy * 1.15 / 10000.0
                astar_size_area = area_front + area_back
            elif "tulum" in urun_grubu_lower:
                gogus = get_val(m, ["gogus", "chest", "width"], 48.0)
                basen = get_val(m, ["basen", "hip", "hips"], 85.0)
                boy = get_val(m, ["boy", "length", "total length", "total_length"], 120.0)
                ic_ag = get_val(m, ["ic ag", "ic_ag", "inseam", "ic boy", "ic_boy"], 65.0)
                paca_eni = get_val(m, ["paca eni", "paca_eni", "hem width", "hem_width", "paca"], 22.0)
                
                area_upper = gogus * (boy - ic_ag) * 2.0 * 1.15 / 10000.0
                area_lower = 2.0 * ((basen / 2.0 + paca_eni) / 2.0) * ic_ag * 1.15 / 10000.0
                astar_size_area = area_upper + area_lower
            else:
                basen = get_val(m, ["basen", "hip", "hips"], 80.0)
                yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "boy"], 30.0)
                astar_size_area = (basen * yan_boy * 2.2 * 1.15 * 0.8) / 10000.0
                
            total_astar_net_area_m2 += astar_size_area * qty
            
        astar_eni_m = astar_eni_cm / 100.0
        # Apply learning correction factor to lining pastal
        astar_pastal_boyu_m = ((total_astar_net_area_m2 * astar_cekme_faktoru) / (astar_eni_m * (verimlilik_yuzde / 100.0))) * astar_correction_factor
        astar_birim_metraj_m = astar_pastal_boyu_m / toplam_asorti_adet
        
    # 6. Tulle (Tul) Calculations
    tul_hesapla = data.get("tul_hesapla", False)
    tul_birim_metraj_m = 0.0
    tul_pastal_boyu_m = 0.0
    
    if tul_hesapla:
        tul_eni_cm = int(data.get("tul_eni_cm", 150))
        tul_cekme_en = float(data.get("tul_cekme_en_yuzde", 0.0))
        tul_cekme_boy = float(data.get("tul_cekme_boy_yuzde", 0.0))
        tul_cekme_faktoru = (1.0 + abs(tul_cekme_en) / 100.0) * (1.0 + abs(tul_cekme_boy) / 100.0)
        
        total_tul_net_area_m2 = 0.0
        for size_name, qty in asorti.items():
            qty = int(qty)
            if qty <= 0:
                continue
            m = olculer.get(size_name, {})
            
            if "elbise" in urun_grubu_lower:
                gogus = get_val(m, ["gogus", "chest", "width"], 48.0)
                boy = get_val(m, ["boy", "length", "total length", "total_length"], 90.0)
                
                # For tulle, prioritize the circular tulle hem width
                tul_etek_eni = get_val(m, ["tul_etek_eni", "tul_etek", "klos_etek_eni", "etek_ucu_genisligi_klos_etek_tuller", "tuller"], 140.0)
                if tul_etek_eni == 140.0:
                    tul_etek_eni = get_val(m, ["etek eni", "etek_eni", "hem width", "hem_width", "etek"], 140.0)
                    
                ust_bel_yeri = get_val(m, ["ust_bel_yeri_omuz_basindan_on", "ust_bel_yeri_omuz_basindan_arka", "ust_bel_yeri", "bodice_length"], 0.0)
                if 0.0 < ust_bel_yeri < boy:
                    skirt_height = boy - ust_bel_yeri
                    area_front = ((gogus + tul_etek_eni) / 2.0) * skirt_height * 1.15 / 10000.0
                    area_back = ((gogus + tul_etek_eni) / 2.0) * skirt_height * 1.15 / 10000.0
                else:
                    area_front = ((gogus + tul_etek_eni) / 2.0) * boy * 1.15 / 10000.0
                    area_back = ((gogus + tul_etek_eni) / 2.0) * boy * 1.15 / 10000.0
                tul_size_area = area_front + area_back
            elif "alt" in urun_grubu_lower:
                bel = get_val(m, ["bel", "waist"], 60.0)
                yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "boy"], 30.0)
                
                tul_etek_eni = get_val(m, ["tul_etek_eni", "tul_etek", "klos_etek_eni", "etek_ucu_genisligi_klos_etek_tuller", "tuller"], 100.0)
                if tul_etek_eni == 100.0:
                    tul_etek_eni = get_val(m, ["paca eni", "paca_eni", "hem width", "hem_width", "paca"], 100.0)
                    
                area_front = ((bel / 4.0 + tul_etek_eni) / 2.0) * yan_boy * 1.15 / 10000.0
                area_back = ((bel / 4.0 + tul_etek_eni) / 2.0) * yan_boy * 1.15 / 10000.0
                tul_size_area = area_front + area_back
            else:
                basen = get_val(m, ["basen", "hip", "hips"], 80.0)
                yan_boy = get_val(m, ["yan boy", "yan_boy", "outseam", "boy"], 30.0)
                tul_size_area = (basen * yan_boy * 2.2 * 1.15 * 0.8) / 10000.0
                
            total_tul_net_area_m2 += tul_size_area * qty
            
        tul_eni_m = tul_eni_cm / 100.0
        tul_pastal_boyu_m = ((total_tul_net_area_m2 * tul_cekme_faktoru) / (tul_eni_m * (verimlilik_yuzde / 100.0))) * tul_correction_factor
        tul_birim_metraj_m = tul_pastal_boyu_m / toplam_asorti_adet
        
    # Pocket (Cep) calculations
    cep_birim_metraj_m = 0.0
    cep_pastal_boyu_m = 0.0
    if total_cep_net_area_m2 > 0:
        cep_eni_cm = 140
        cep_eni_m = cep_eni_cm / 100.0
        cep_verimlilik = max(88.0, verimlilik_yuzde)
        cep_pastal_boyu_m = (total_cep_net_area_m2 * 1.15) / (cep_eni_m * (cep_verimlilik / 100.0))
        cep_birim_metraj_m = cep_pastal_boyu_m / toplam_asorti_adet

    return {
        "toplam_asorti_adet": toplam_asorti_adet,
        "cekme_faktoru": round(cekme_faktoru, 6),
        "total_net_area_m2": round(total_net_area_m2, 4),
        "net_areas": net_areas,
        "birim_metraj_m": round(birim_metraj_m, 4),
        "pastal_boyu_m": round(pastal_boyu_m, 4),
        "verimlilik_yuzde": verimlilik_yuzde,
        "astar_birim_metraj_m": round(astar_birim_metraj_m, 4),
        "astar_pastal_boyu_m": round(astar_pastal_boyu_m, 4),
        "tul_birim_metraj_m": round(tul_birim_metraj_m, 4),
        "tul_pastal_boyu_m": round(tul_pastal_boyu_m, 4),
        "cep_birim_metraj_m": round(cep_birim_metraj_m, 4),
        "cep_pastal_boyu_m": round(cep_pastal_boyu_m, 4),
        "total_cep_net_area_m2": round(total_cep_net_area_m2, 4),
        "correction_factor": round(kumas_correction_factor, 4),
        "astar_correction_factor": round(astar_correction_factor, 4),
        "tul_correction_factor": round(tul_correction_factor, 4),
        "learning_samples_count": kumas_samples_count,
        "astar_learning_samples_count": astar_samples_count,
        "tul_learning_samples_count": tul_samples_count
    }

# HTTP Request Handler class
class PastalHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/modeller":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Model_Tanimlari ORDER BY Model_Adi ASC")
            modeller = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(modeller).encode('utf-8'))
            return

        elif self.path == "/api/calismalar":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, m.Model_Adi, m.Urun_Grubu
                FROM Maliyet_Calismalari c
                JOIN Model_Tanimlari m ON c.Model_ID = m.Model_ID
                ORDER BY c.Kayit_Tarihi DESC
            """)
            calismalar = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(calismalar).encode('utf-8'))
            return

        elif self.path == "/api/ogrenme":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Ogrenme_Kayitlari ORDER BY Tarih DESC")
            ogrenmeler = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(ogrenmeler).encode('utf-8'))
            return

        elif self.path == "/api/db/export":
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Model_Tanimlari")
                modeller = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM Maliyet_Calismalari")
                calismalar = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM Ogrenme_Kayitlari")
                ogrenmeler = [dict(r) for r in cursor.fetchall()]
                conn.close()
                
                export_data = {
                    "modeller": modeller,
                    "calismalar": calismalar,
                    "ogrenmeler": ogrenmeler,
                    "exported_at": str(time.time())
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="pastal_maliyet_yedek.json"')
                self.end_headers()
                self.wfile.write(json.dumps(export_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        else:
            clean_path = self.path.split('?')[0]
            if clean_path == "/" or clean_path == "":
                clean_path = "/index.html"
            public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
            file_path = os.path.join(public_dir, clean_path.lstrip("/"))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                content_types = {
                    ".html": "text/html; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".js": "application/javascript; charset=utf-8",
                    ".json": "application/json; charset=utf-8",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                }
                content_type = content_types.get(ext, "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>404 - Sayfa Bulunamadi</h1>")

    def do_POST(self):
        global agent
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        data = {}
        if post_data:
            try:
                data = json.loads(post_data.decode('utf-8'))
            except Exception as je:
                print(f"JSON decode warning: {je}")
        
        # --- API: /api/ogrenme ---
        if self.path == "/api/ogrenme":
            try:
                hatalar = data.get('hatalar', '')
                dogrular = data.get('dogrular', '')
                tip = data.get('tip', 'olcu_duzeltme')
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Ogrenme_Kayitlari (Hatalar, Dogrular, Tip)
                    VALUES (?, ?, ?)
                """, (hatalar, dogrular, tip))
                conn.commit()
                conn.close()
                self.send_response(201)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Öğrenme kaydı eklendi."}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # --- API: /api/calculate ---
        elif self.path == "/api/calculate":
            try:
                results = calculate_marker_cost(data)
                
                # Serialize dynamic size dict to JSON string for SQLite storage
                asorti_json = json.dumps(data.get("asorti", {}))
                olculer_json = json.dumps(data.get("olculer", {}))
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO Maliyet_Calismalari (
                    Model_ID, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde,
                    Asorti_JSON, Olculer_JSON, Toplam_Asorti_Adet,
                    Hesaplanan_Birim_Metraj_M, Hesaplanan_Pastal_Boyu_M,
                    Astar_Eni_cm, Astar_Cekme_En_Yuzde, Astar_Cekme_Boy_Yuzde,
                    Hesaplanan_Astar_Birim_M, Hesaplanan_Astar_Pastal_M,
                    Tul_Eni_cm, Tul_Cekme_En_Yuzde, Tul_Cekme_Boy_Yuzde,
                    Hesaplanan_Tul_Birim_M, Hesaplanan_Tul_Pastal_M,
                    Verimlilik_Yuzde, Cep_Kumastan
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["model_id"], int(data["kumas_eni_cm"]), float(data["cekme_en_yuzde"]), float(data["cekme_boy_yuzde"]),
                    asorti_json, olculer_json, results["toplam_asorti_adet"], results["birim_metraj_m"], results["pastal_boyu_m"],
                    int(data.get("astar_eni_cm", 0)) if data.get("astar_hesapla", False) else 0,
                    float(data.get("astar_cekme_en_yuzde", 0.0)) if data.get("astar_hesapla", False) else 0.0,
                    float(data.get("astar_cekme_boy_yuzde", 0.0)) if data.get("astar_hesapla", False) else 0.0,
                    results.get("astar_birim_metraj_m", 0.0), results.get("astar_pastal_boyu_m", 0.0),
                    int(data.get("tul_eni_cm", 0)) if data.get("tul_hesapla", False) else 0,
                    float(data.get("tul_cekme_en_yuzde", 0.0)) if data.get("tul_hesapla", False) else 0.0,
                    float(data.get("tul_cekme_boy_yuzde", 0.0)) if data.get("tul_hesapla", False) else 0.0,
                    results.get("tul_birim_metraj_m", 0.0), results.get("tul_pastal_boyu_m", 0.0),
                    results["verimlilik_yuzde"],
                    1 if data.get("cep_kumastan", True) else 0
                ))
                calisma_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                results["calisma_id"] = calisma_id
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "results": results}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/calismalar/feedback (Save Realized Values via Agent) ---
        elif self.path == "/api/calismalar/feedback":
            try:
                calisma_id = data.get("calisma_id")
                gerceklesen_tuketim = data.get("gerceklesen_tuketim")
                gerceklesen_astar_tuketim = data.get("gerceklesen_astar_tuketim")
                gerceklesen_tul_tuketim = data.get("gerceklesen_tul_tuketim")
                gerceklesen_asorti = data.get("gerceklesen_asorti")
                gerceklesen_kumas_eni = data.get("gerceklesen_kumas_eni")
                gerceklesen_cekme_en = data.get("gerceklesen_cekme_en")
                gerceklesen_cekme_boy = data.get("gerceklesen_cekme_boy")
                
                if 'agent' not in globals() or agent is None:
                    agent = PastalAgent(DB_FILE, GEMINI_API_KEY, GEMINI_MODEL, call_gemini_json)
                # Delegate entirely to the PastalAgent
                agent_res = agent.analyze_feedback(
                    calisma_id=calisma_id,
                    gerceklesen_tuketim=gerceklesen_tuketim,
                    gerceklesen_astar_tuketim=gerceklesen_astar_tuketim,
                    gerceklesen_tul_tuketim=gerceklesen_tul_tuketim,
                    gerceklesen_asorti=gerceklesen_asorti,
                    gerceklesen_kumas_eni=gerceklesen_kumas_eni,
                    gerceklesen_cekme_en=gerceklesen_cekme_en,
                    gerceklesen_cekme_boy=gerceklesen_cekme_boy
                )
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(agent_res).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/calismalar/feedback/reset (Clear Realized Values) ---
        elif self.path == "/api/calismalar/feedback/reset":
            try:
                calisma_id = data.get("calisma_id")
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                if calisma_id:
                    cursor.execute("""
                        UPDATE Maliyet_Calismalari
                        SET Gerceklesen_Birim_Metraj_M = NULL,
                            Gerceklesen_Astar_Birim_M = NULL,
                            Gerceklesen_Tul_Birim_M = NULL,
                            Gerceklesen_Asorti_JSON = NULL,
                            Gerceklesen_Kumas_Eni_cm = NULL,
                            Gerceklesen_Cekme_En_Yuzde = NULL,
                            Gerceklesen_Cekme_Boy_Yuzde = NULL,
                            Use_In_Calibration = 1,
                            Agent_Analysis_HTML = NULL
                        WHERE Calisma_ID = ?
                    """, (int(calisma_id),))
                else:
                    cursor.execute("""
                        UPDATE Maliyet_Calismalari
                        SET Gerceklesen_Birim_Metraj_M = NULL,
                            Gerceklesen_Astar_Birim_M = NULL,
                            Gerceklesen_Tul_Birim_M = NULL,
                            Gerceklesen_Asorti_JSON = NULL,
                            Gerceklesen_Kumas_Eni_cm = NULL,
                            Gerceklesen_Cekme_En_Yuzde = NULL,
                            Gerceklesen_Cekme_Boy_Yuzde = NULL,
                            Use_In_Calibration = 1,
                            Agent_Analysis_HTML = NULL
                    """)
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/ogrenme/ekle (Custom Model/Category Rule Ingestion) ---
        elif self.path == "/api/ogrenme/ekle":
            try:
                kural_text = str(data.get("kural_text", "")).strip()
                model_or_klasman = str(data.get("model_or_klasman", "")).strip()
                if not kural_text:
                    raise ValueError("Özel kural metni girilmedi.")
                
                dogru_str = f"[{model_or_klasman}] {kural_text}" if model_or_klasman else kural_text
                hata_str = "Kullanıcı özel model/klasman imalat kuralı tanımı."
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Ogrenme_Kayitlari (Hatalar, Dogrular, Tip) VALUES (?, ?, 'analiz_kurali')", (hata_str, dogru_str))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Özel kural başarıyla öğrenme havuzuna eklendi ve kilitlendi."}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/calismalar/delete (Delete Specific Study) ---
        elif self.path == "/api/calismalar/delete":
            try:
                calisma_id = data.get("calisma_id")
                if not calisma_id:
                    raise ValueError("Calisma_ID is required.")
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Maliyet_Calismalari WHERE Calisma_ID = ?", (int(calisma_id),))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/toplu_ogrenme (Bulk Data Import & Calibration) ---
        elif self.path == "/api/toplu_ogrenme":
            try:
                kayitlar = data.get("kayitlar", [])
                if not kayitlar and isinstance(data, list):
                    kayitlar = data
                
                if not kayitlar:
                    raise ValueError("Yüklenecek imalat kaydı bulunamadı.")
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                processed_count = 0
                agent = PastalAgent(DB_FILE, GEMINI_API_KEY, GEMINI_MODEL, call_gemini_json)
                
                for item in kayitlar:
                    model_adi = str(item.get("model_adi", f"Model-{int(time.time())}")).strip()
                    urun_grubu = str(item.get("urun_grubu", "Alt Giyim")).strip()
                    olculer = item.get("olculer", {})
                    
                    # If no PDF technical spec measurements exist, assign baseline measurements so model is saved to DB
                    if not olculer or len(olculer) == 0:
                        if urun_grubu == "Alt Giyim":
                            olculer = {"M": {"bel": 75, "basen": 100, "yan_boy": 100, "paca_eni": 20}}
                        elif urun_grubu == "Elbise":
                            olculer = {"M": {"boy": 100, "gogus": 92, "bel": 76, "etek_eni": 60}}
                        elif urun_grubu == "Tulum":
                            olculer = {"M": {"boy": 140, "gogus": 92, "bel": 76, "paca_eni": 20}}
                        else:
                            olculer = {"M": {"boy": 70, "gogus": 96, "kol_boyu": 60}}
                    
                    # 1. Find or create model
                    cursor.execute("SELECT Model_ID FROM Model_Tanimlari WHERE Model_Adi = ?", (model_adi,))
                    row = cursor.fetchone()
                    if row:
                        model_id = row[0]
                    else:
                        cursor.execute("INSERT INTO Model_Tanimlari (Model_Adi, Urun_Grubu) VALUES (?, ?)", (model_adi, urun_grubu))
                        model_id = cursor.lastrowid
                        conn.commit()
                    
                    # 2. Build parameters
                    kumas_eni = float(item.get("kumas_eni_cm", 175))
                    cekme_en = float(item.get("cekme_en_yuzde", 3))
                    cekme_boy = float(item.get("cekme_boy_yuzde", 3))
                    verimlilik = float(item.get("verimlilik_yuzde", 90.0))
                    
                    asorti = parse_flexible_asorti(item.get("asorti"))
                    olculer = item.get("olculer", {})
                    
                    h_data = {
                        "model_id": model_id,
                        "kumas_eni_cm": kumas_eni,
                        "cekme_en_yuzde": cekme_en,
                        "cekme_boy_yuzde": cekme_boy,
                        "verimlilik_yuzde": verimlilik,
                        "asorti": asorti,
                        "olculer": olculer,
                        "cep_kumastan": bool(item.get("cep_kumastan", True)),
                        "astar_hesapla": bool(item.get("astar_hesapla", False)),
                        "astar_eni_cm": float(item.get("astar_eni_cm", 140)),
                        "astar_cekme_en_yuzde": float(item.get("astar_cekme_en_yuzde", 3)),
                        "astar_cekme_boy_yuzde": float(item.get("astar_cekme_boy_yuzde", 3)),
                        "tul_hesapla": bool(item.get("tul_hesapla", False)),
                        "tul_eni_cm": float(item.get("tul_eni_cm", 150)),
                        "tul_cekme_en_yuzde": float(item.get("tul_cekme_en_yuzde", 2)),
                        "tul_cekme_boy_yuzde": float(item.get("tul_cekme_boy_yuzde", 2))
                    }
                    
                    calc_res = calculate_marker_cost(h_data, apply_learning=False)
                    toplam_asorti = sum(asorti.values()) if asorti else 1
                    
                    cursor.execute("""
                    INSERT INTO Maliyet_Calismalari (
                        Model_ID, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde, Verimlilik_Yuzde,
                        Toplam_Asorti_Adet, Asorti_JSON, Olculer_JSON,
                        Hesaplanan_Birim_Metraj_M, Hesaplanan_Pastal_Boyu_M,
                        Astar_Eni_cm, Astar_Cekme_En_Yuzde, Astar_Cekme_Boy_Yuzde,
                        Hesaplanan_Astar_Birim_M, Hesaplanan_Astar_Pastal_M,
                        Tul_Eni_cm, Tul_Cekme_En_Yuzde, Tul_Cekme_Boy_Yuzde,
                        Hesaplanan_Tul_Birim_M, Hesaplanan_Tul_Pastal_M,
                        Cep_Kumastan
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        model_id, kumas_eni, cekme_en, cekme_boy, verimlilik,
                        toplam_asorti, json.dumps(asorti), json.dumps(olculer),
                        calc_res["birim_metraj_m"], calc_res["pastal_boyu_m"],
                        h_data["astar_eni_cm"], h_data["astar_cekme_en_yuzde"], h_data["astar_cekme_boy_yuzde"],
                        calc_res["astar_birim_metraj_m"], calc_res["astar_pastal_boyu_m"],
                        h_data["tul_eni_cm"], h_data["tul_cekme_en_yuzde"], h_data["tul_cekme_boy_yuzde"],
                        calc_res["tul_birim_metraj_m"], calc_res["tul_pastal_boyu_m"],
                        1 if h_data["cep_kumastan"] else 0
                    ))
                    calisma_id = cursor.lastrowid
                    conn.commit()
                    
                    gerceklesen_tuketim = item.get("gerceklesen_tuketim")
                    if gerceklesen_tuketim is not None:
                        try:
                            real_val = float(gerceklesen_tuketim)
                            cursor.execute("""
                                UPDATE Maliyet_Calismalari
                                SET Gerceklesen_Birim_Metraj_M = ?
                                WHERE Calisma_ID = ?
                            """, (real_val, calisma_id))
                            conn.commit()
                        except Exception as num_err:
                            print(f"[TOPLU ÖĞRENME] Gerceklesen metraj parse error: {num_err}")

                        def _run_async_feedback(cid=calisma_id, gt=gerceklesen_tuketim, itm=item, asr=asorti, ke=kumas_eni, ce=cekme_en, cb=cekme_boy):
                            try:
                                agent.analyze_feedback(
                                    calisma_id=cid,
                                    gerceklesen_tuketim=gt,
                                    gerceklesen_astar_tuketim=itm.get("gerceklesen_astar_tuketim"),
                                    gerceklesen_tul_tuketim=itm.get("gerceklesen_tul_tuketim"),
                                    gerceklesen_asorti=itm.get("gerceklesen_asorti", asr),
                                    gerceklesen_kumas_eni=itm.get("gerceklesen_kumas_eni", ke),
                                    gerceklesen_cekme_en=itm.get("gerceklesen_cekme_en", ce),
                                    gerceklesen_cekme_boy=itm.get("gerceklesen_cekme_boy", cb)
                                )
                            except Exception as fe:
                                print(f"[TOPLU ÖĞRENME] Background feedback analysis note: {fe}")
                        
                        import threading
                        threading.Thread(target=_run_async_feedback, daemon=True).start()
                    processed_count += 1
                
                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "processed_count": processed_count,
                    "message": f"{processed_count} adet imalat kaydı toplu olarak yüklendi, hesaplandı ve yapay zeka kalibrasyonuna dahil edildi."
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/toplu_preview (Exact Physical Calculation Preview) ---
        elif self.path == "/api/toplu_preview":
            try:
                if isinstance(data, list):
                    kayitlar = data
                elif isinstance(data, dict):
                    kayitlar = data.get("kayitlar", [])
                else:
                    kayitlar = []
                
                results_list = []
                for item in kayitlar:
                    olculer = item.get("olculer", {})
                    if not olculer or len(olculer) == 0:
                        results_list.append({
                            "model_adi": item.get("model_adi"),
                            "est_birim_metraj_m": 0.0,
                            "has_olculer": False
                        })
                        continue
                    
                    asorti = parse_flexible_asorti(item.get("asorti"))
                    h_data = {
                        "model_id": 1,
                        "urun_grubu": item.get("urun_grubu", "Alt Giyim"),
                        "kumas_eni_cm": float(item.get("kumas_eni_cm", 175)),
                        "cekme_en_yuzde": float(item.get("cekme_en_yuzde", 3)),
                        "cekme_boy_yuzde": float(item.get("cekme_boy_yuzde", 3)),
                        "verimlilik_yuzde": float(item.get("verimlilik_yuzde", 90.0)),
                        "asorti": asorti,
                        "olculer": olculer,
                        "cep_kumastan": True
                    }
                    calc_res = calculate_marker_cost(h_data, apply_learning=False)

                    results_list.append({
                        "model_adi": item.get("model_adi"),
                        "est_birim_metraj_m": calc_res.get("birim_metraj_m", 0.0),
                        "pastal_boyu_m": calc_res.get("pastal_boyu_m", 0.0),
                        "verimlilik_yuzde": calc_res.get("verimlilik_yuzde", 90.0),
                        "has_olculer": True
                    })
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "results": results_list}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/parse_excel (Native Python Backend Excel .xlsx/.xls Parser) ---
        elif self.path == "/api/parse_excel":
            try:
                import base64, io
                file_b64 = data.get("file_b64", "")
                file_bytes = base64.b64decode(file_b64)
                file_io = io.BytesIO(file_bytes)
                
                raw_rows = parse_xlsx_native(file_io)
                items = parse_raw_rows_to_json(raw_rows)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "items": items}).encode('utf-8'))
            except Exception as e:
                print(f"[API parse_excel] Error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/kumaslar (Deprecated, keep for backward compatibility safety) ---
        elif self.path == "/api/kumaslar":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "kumas_id": 1}).encode('utf-8'))

        # --- API: /api/modeller ---
        elif self.path == "/api/modeller":
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO Model_Tanimlari (Model_Adi, Urun_Grubu)
                VALUES (?, ?)
                """, (data["model_adi"], data["urun_grubu"]))
                model_id = cursor.lastrowid
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "model_id": model_id}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/modeller/delete ---
        elif self.path == "/api/modeller/delete":
            try:
                model_id = data.get("model_id")
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Maliyet_Calismalari WHERE Model_ID = ?", (int(model_id),))
                cursor.execute("DELETE FROM Model_Tanimlari WHERE Model_ID = ?", (int(model_id),))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
        # --- API: /api/db/import ---
        elif self.path == "/api/db/import":
            try:
                modeller = data.get("modeller", [])
                calismalar = data.get("calismalar", [])
                ogrenmeler = data.get("ogrenmeler", [])
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                model_map = {}
                for m in modeller:
                    cursor.execute("SELECT Model_ID FROM Model_Tanimlari WHERE Model_Adi = ?", (m["Model_Adi"],))
                    r = cursor.fetchone()
                    if r:
                        model_map[m["Model_ID"]] = r[0]
                    else:
                        cursor.execute("INSERT INTO Model_Tanimlari (Model_Adi, Urun_Grubu) VALUES (?, ?)", (m["Model_Adi"], m["Urun_Grubu"]))
                        model_map[m["Model_ID"]] = cursor.lastrowid
                
                for c in calismalar:
                    old_m_id = c.get("Model_ID")
                    new_m_id = model_map.get(old_m_id)
                    if new_m_id:
                        cursor.execute("""
                            INSERT INTO Maliyet_Calismalari (
                                Model_ID, Kumas_Eni_cm, Cekme_En_Yuzde, Cekme_Boy_Yuzde, Asorti_JSON, Olculer_JSON,
                                Toplam_Asorti_Adet, Hesaplanan_Birim_Metraj_M, Hesaplanan_Pastal_Boyu_M, Gerceklesen_Birim_Metraj_M,
                                Verimlilik_Yuzde, Gerceklesen_Asorti_JSON, Gerceklesen_Kumas_Eni_cm, Gerceklesen_Cekme_En_Yuzde, Gerceklesen_Cekme_Boy_Yuzde
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            new_m_id, c.get("Kumas_Eni_cm"), c.get("Cekme_En_Yuzde"), c.get("Cekme_Boy_Yuzde"),
                            c.get("Asorti_JSON"), c.get("Olculer_JSON"), c.get("Toplam_Asorti_Adet"),
                            c.get("Hesaplanan_Birim_Metraj_M"), c.get("Hesaplanan_Pastal_Boyu_M"), c.get("Gerceklesen_Birim_Metraj_M"),
                            c.get("Verimlilik_Yuzde", 90.0), c.get("Gerceklesen_Asorti_JSON"), c.get("Gerceklesen_Kumas_Eni_cm"),
                            c.get("Gerceklesen_Cekme_En_Yuzde"), c.get("Gerceklesen_Cekme_Boy_Yuzde")
                        ))
                
                for o in ogrenmeler:
                    cursor.execute("""
                        INSERT INTO Ogrenme_Kayitlari (Hatalar, Dogrular, Tip) VALUES (?, ?, ?)
                    """, (o.get("Hatalar"), o.get("Dogrular"), o.get("Tip")))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Veri tabanı yedeği başarıyla içe aktarıldı ve birleştirildi."}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

        # --- API: /api/chat/parse (Intent Parser - Gemini) ---
        elif self.path == "/api/chat/parse":
            user_text = data.get("text", "")
            system_prompt = (
                "You are an NLP parser for textile manufacturing software. Your job is to extract style/model name, product classification, fabric details, "
                "shrinkage percentages, size marker ratios (asorti), and measurement tables (olculer) from Turkish text.\n"
                "Return ONLY a clean valid JSON object with the following fields (use default values if not mentioned):\n"
                "- model_adi (string or null if not found)\n"
                "- urun_grubu (string or null, must be one of: 'Alt Giyim', 'Üst Giyim', 'Elbise', 'Tulum')\n"
                "- kumas_eni_cm (integer or null if not found)\n"
                "- cekme_en_yuzde (decimal or 0.0, use actual percentage like 5.0 for 5%, NOT 0.05)\n"
                "- cekme_boy_yuzde (decimal or 0.0, use actual percentage like 3.0 for 3%, NOT 0.03)\n"
                "- verimlilik_yuzde (decimal or 90.0, target efficiency percentage for the marker calculation, e.g. 92.5 for 92.5% efficiency)\n"
                "- asorti (JSON object mapping size names to integer ratios. Supported sizes can be XS, S, M, L, XL, XXL, or age ranges like 9-12m, 1-2y, 2-3y, 3-4y, 4-5y, 5-6y, 6-7y, 7-8y, 8-9y, 9-10y, 10y-11y, 11y-12y, 12y-13y, 13y-14y)\n"
                "- olculer (JSON object mapping size names to objects of measurements, e.g. {\"bel\": 60, \"basen\": 80, \"yan_boy\": 30})\n"
                "- astar_hesapla (boolean, true if lining/astar is mentioned, else false)\n"
                "- astar_eni_cm (integer or null, width of lining fabric)\n"
                "- astar_cekme_en_yuzde (decimal or 0.0, lining shrinkage width percentage)\n"
                "- astar_cekme_boy_yuzde (decimal or 0.0, lining shrinkage length percentage)\n"
                "- tul_hesapla (boolean, true if tulle/tül is mentioned, else false)\n"
                "- tul_eni_cm (integer or null, width of tulle fabric)\n"
                "- tul_cekme_en_yuzde (decimal or 0.0, tulle shrinkage width percentage)\n"
                "- tul_cekme_boy_yuzde (decimal or 0.0, tulle shrinkage length percentage)\n\n"
                "Example Input: 'TOMIX model elbise için 160 eninde kumaş, enine 5 boyuna 3 çekme var. Asorti 1-2-2-1 olcak. S bedende gogus 50, boy 90, etek_eni 60.'\n"
                "Example Output JSON:\n"
                "{\n"
                "  \"model_adi\": \"TOMIX\",\n"
                "  \"urun_grubu\": \"Elbise\",\n"
                "  \"kumas_eni_cm\": 160,\n"
                "  \"cekme_en_yuzde\": 5.0,\n"
                "  \"cekme_boy_yuzde\": 3.0,\n"
                "  \"astar_hesapla\": false,\n"
                "  \"astar_eni_cm\": null,\n"
                "  \"astar_cekme_en_yuzde\": 0.0,\n"
                "  \"astar_cekme_boy_yuzde\": 0.0,\n"
                "  \"tul_hesapla\": false,\n"
                "  \"tul_eni_cm\": null,\n"
                "  \"tul_cekme_en_yuzde\": 0.0,\n"
                "  \"tul_cekme_boy_yuzde\": 0.0,\n"
                "  \"asorti\": {\n"
                "    \"S\": 1,\n"
                "    \"M\": 2,\n"
                "    \"L\": 2,\n"
                "    \"XL\": 1\n"
                "  },\n"
                "  \"olculer\": {\n"
                "    \"S\": {\"gogus\": 50, \"boy\": 90, \"etek_eni\": 60}\n"
                "  }\n"
                "}\n"
                "Do not include any explanation or markdown formatting, just the raw JSON."
            )
            
            formula_summary = (
                "\n\nSistem metraj hesaplama formülü özetleri:\n"
                "- Alt Giyim: 4 Pano Alanı (Ön ve Arka yamuk alanları: bel, basen, paça ve boy kullanılarak) + Kemer + Detay (Cep, Patlet vb.) + %15 Fire.\n"
                "- Üst Giyim: Ön Gövde (Göğüs x Boy) + Arka Gövde (Göğüs x Boy) + 2 x Kol (Kol Boyu x Kol Genişliği) + Yaka + %15 Fire.\n"
                "- Elbise: Ön ve Arka ((Göğüs + Etek Eni) / 2 x Boy) + Kol (varsa) + %15 Fire.\n"
            )
            system_prompt += formula_summary
            
            conn_ogrenme = sqlite3.connect(DB_FILE)
            cursor_ogrenme = conn_ogrenme.cursor()
            try:
                cursor_ogrenme.execute("SELECT Dogrular FROM Ogrenme_Kayitlari WHERE Tip = 'analiz_kurali' ORDER BY Tarih DESC")
                kurallar = cursor_ogrenme.fetchall()
                if kurallar:
                    system_prompt += "\nKullanıcının belirlediği özel analiz ve hesaplama kuralları:\n"
                    for kural in kurallar:
                        if kural[0]:
                            system_prompt += f"- {kural[0]}\n"
            except sqlite3.OperationalError:
                pass
            finally:
                conn_ogrenme.close()
            
            response_text = call_gemini_json(user_text, system_prompt)
            parsed_json = {}
            if response_text:
                try:
                    clean_res = response_text.replace("```json", "").replace("```", "").strip()
                    parsed_json = json.loads(clean_res)
                except Exception as pe:
                    print(f"Error parsing Gemini response to JSON: {pe}. Raw output: {response_text}")
                    parsed_json = {"error": "JSON parse hatasi", "raw": response_text}
            else:
                parsed_json = {"error": "Gemini API rate limit or quota error"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(parsed_json).encode('utf-8'))

        # --- API: /api/chat/parse_file (Multimodal PDF/Image Analysis - Gemini) ---
        elif self.path == "/api/chat/parse_file":
            try:
                file_b64 = data.get("file_b64", "")
                mime_type = data.get("mime_type", "application/pdf")
                user_text = data.get("user_text", "")
                
                response_text = None
                
                if mime_type == "application/pdf":
                    try:
                        import base64
                        import io
                        import pypdf
                        
                        pdf_bytes = base64.b64decode(file_b64)
                        pdf_file = io.BytesIO(pdf_bytes)
                        reader = pypdf.PdfReader(pdf_file)
                        total_pages = len(reader.pages)
                        print(f"[PDF PARSER] Local text extraction starting for {total_pages} pages...")
                        
                        pages_to_read = []
                        for idx in range(total_pages):
                            page = reader.pages[idx]
                            text = page.extract_text() or ""
                            
                            # If total pages is <= 25, read everything to ensure no pages are missed
                            if total_pages <= 25:
                                pages_to_read.append((idx + 1, text))
                            else:
                                text_lower = text.lower()
                                # Clean text for robust keyword matching (e.g. toler\nance -> tolerance)
                                text_clean = text_lower.replace("-", "").replace("\n", "").replace(" ", "")
                                is_measurement_page = (
                                    "measurement" in text_clean or 
                                    "tolerans" in text_clean or 
                                    "ölçü" in text_clean or 
                                    "tolerance" in text_clean or 
                                    "tol(" in text_clean or 
                                    "pom" in text_clean or
                                    "size" in text_clean or
                                    "beden" in text_clean
                                )
                                # Read page 1, the last 6 pages, or pages matching keywords
                                if idx == 0 or idx >= total_pages - 6 or is_measurement_page:
                                    pages_to_read.append((idx + 1, text))
                        
                        combined_text_list = []
                        for page_num, text in pages_to_read:
                            combined_text_list.append(f"=== PAGE {page_num} ===\n{text}")
                        combined_text = "\n\n".join(combined_text_list)
                        
                        if user_text:
                            combined_text = combined_text + f"\n\nKullanıcının ekstra girdiği talimatlar/notlar (Lütfen bunları analiz edip kumas_eni_cm, cekme_en_yuzde, cekme_boy_yuzde, asorti ve olculer alanlarını doldururken öncelikli olarak kullanın):\n{user_text}"
                        
                        print(f"[PDF PARSER] Sending {len(combined_text)} characters of extracted text to Gemini API...")
                        prompt = (
                            "Bu bir teknik föy (tech pack) dokümanının metin çıktısıdır. Dokümandan model adı, ürün grubu, kumaş eni, çekme yüzdeleri, beden asortisi ve özellikle beden ölçülerini (measurement table) çıkar. SADECE JSON formatında veri üret.\n\n"
                            "Çıktı JSON Şeması:\n"
                            "{\n"
                            "  \"model_adi\": \"TOMIX-6S\",\n"
                            "  \"urun_grubu\": \"Elbise\",\n"
                            "  \"kumas_eni_cm\": 150,\n"
                            "  \"cekme_en_yuzde\": 0.0,\n"
                            "  \"cekme_boy_yuzde\": 0.0,\n"
                            "  \"verimlilik_yuzde\": 90.0,\n"
                            "  \"astar_hesapla\": false,\n"
                            "  \"astar_eni_cm\": 140,\n"
                            "  \"astar_cekme_en_yuzde\": 0.0,\n"
                            "  \"astar_cekme_boy_yuzde\": 0.0,\n"
                            "  \"tul_hesapla\": false,\n"
                            "  \"tul_eni_cm\": 150,\n"
                            "  \"tul_cekme_en_yuzde\": 0.0,\n"
                            "  \"tul_cekme_boy_yuzde\": 0.0,\n"
                            "  \"asorti\": {},\n"
                            "  \"olculer\": {\n"
                            "    \"7-8y\": { \"bel\": 65.0, \"basen\": 77.0, \"yan_boy\": 30.0, \"on_ag\": 21.5, \"paca_eni\": 23.75, \"gogus\": 38.0, \"boy\": 65.0, \"kol_boyu\": 18.0, \"etek_eni\": 51.0, \"astar_etek_eni\": 51.0, \"tul_etek_eni\": 145.4 }\n"
                            "  }\n"
                            "}\n\n"
                            "Kurallar:\n"
                            "1. Model Adı (model_adi): Föyün ilk sayfasında veya başlıklarında yer alan model adını veya stil kodunu çıkarın (örn: '1166750 - TOMIX-6S' veya '1160033 - FOSFOR'). Boş bırakmayın.\n"
                            "2. Ürün Grubu (urun_grubu): Modelin ürün grubunu tespit edip şu 4 değerden biri olarak kaydedin: 'Alt Giyim', 'Üst Giyim', 'Elbise', 'Tulum'.\n"
                            "   - Eğer ölçülerde omuzdan boy (OMUZDAN BOY-HPS / boy / length), göğüs (gogus / chest) ve etek ucu genişliği (etek_eni) varsa: 'Elbise'\n"
                            "   - Eğer ölçülerde omuzdan boy, göğüs ve kol boyu varsa fakat etek ucu genişliği yoksa: 'Üst Giyim'\n"
                            "   - Eğer ölçülerde bel, basen, yan boy, ön ağ, paça eni varsa ve üst gövdeye ait ölçüler yoksa: 'Alt Giyim'\n"
                            "   - Eğer ölçülerde omuzdan boy, göğüs, arka ağ, iç ağ, paça eni varsa: 'Tulum'\n"
                            "3. Kumaş Eni (kumas_eni_cm): Belirtilmişse çıkarın, yoksa 150 varsayın.\n"
                            "4. Çekme Oranları (cekme_en_yuzde, cekme_boy_yuzde): Değerleri doğrudan yüzde olarak yazın (örn: %5 çekme ise 5.0 yazın, 0.05 DEĞİL). Dokümanda yoksa 0.0 varsayın.\n"
                            "5. Verimlilik (verimlilik_yuzde): Föyde veya kullanıcı notlarında pastal yerleşim verimliliği belirtilmişse çıkarın (örn: %92 verimlilik için 92.0 yazın). Belirtilmemişse 90.0 varsayın. Boş bırakmayın.\n"
                            "6. Asorti (asorti): Kullanıcı notlarında / talimatlarında (user_text) belirtilmiş bir asorti oranı veya beden adetleri varsa (örneğin: 'Asorti 1-2-3-3-3-2-3-1' veya '1/3 ay 1, 3/6 ay 2...') KESİNLİKLE öncelikli olarak kullanıcının yazdığı asorti bilgisini alın. Kullanıcı yazmışsa föydeki asorti/adet bilgilerini tamamen yok sayın. Beden isimleri anahtar, adetler/oranlar integer değer olmalıdır.\n"
                            "7. Ölçüler (olculer) - ÇOK ÖNEMLİ, DİKKATLİ OKU:\n"
                            "   a) Dokümanın TÜM sayfalarını tara ve ölçü tablosunu (Measurement Table / Spec Table) bul.\n"
                            "   b) Tablonun SÜTUN BAŞLIKLARINI oku — bunlar beden isimleridir (örn: 32/XXS/22, 34/XS/24, 36/S/26, 38/M/28, 40/L/30, 42/XL/32, 44/2XL/34, 46/3XL/36, 48/4XL/38, 50/5XL, 52/6XL, 54/7XL veya XS, S, M, L, XL, XXL veya 9-12m, 1-2y, 2-3y vb.).\n"
                            "   c) Tablodaki HER SÜTUN (beden) için HER SATIR (ölçüm) değerini oku. Hiçbir sütunu ve satırı atlama.\n"
                            "   d) DOĞRULAMA: Tabloda kaç beden sütunu varsa olculer nesnesinde de BİREBİR aynı sayıda beden anahtarı olmalı.\n"
                            "   e) Beden başlıklarındaki birleşik tanımları (örn: '38/M/28' veya '38/M' veya '36/S') olculer ve asorti anahtarları için BİREBİR AYNI isimlerle kullanın.\n"
                            "8. Değer Normalizasyonu ve Bel/Basen Çiftleme Kuralı (TÜM BEDENLERDE TUTARLI UYGULA):\n"
                            "   - 'bel' (waist): Bel genişliği (W14, W13, W222, BEL KAVİSLİ GENİŞLİĞİ-ÜSTTEN, BEL GENİŞLİĞİ-KAVİSLİ-ALTTAN veya bel).\n"
                            "     KRİTİK KURAL: Tablodaki bel ölçüleri DÜZ/YARIM ÖLÇÜ (half-width, örn: küçük/ilk beden için ~25-50 cm arası) olarak verilmişse, TABLODAKİ TÜM BEDENLER DÜZ ÖLÇÜDÜR. Tablodaki TÜM BEDENLERİN bel değerlerini İSTİSNASIZ 2 İLE ÇARPARAK TAM ÇEVRE (circumference) olarak 'bel' anahtarına kaydedin (Örn: 32 beden 34.5 cm ise 34.5*2 = 69.0, 38 beden 41.5 cm ise 41.5*2 = 83.0, 54 beden 66.0 cm ise 66.0*2 = 132.0). Sakın küçük bedenleri çarpıp büyük bedenleri çarpmamazlık yapmayın! Bütün bedenler aynı çarpma kuralına tabidir.\n"
                            "   - 'basen' (hip): Basen genişliği (W59, BASEN GENİŞLİĞİ, basen veya hip).\n"
                            "     KRİTİK KURAL: Eğer küçük/ilk beden için basen ~30-60 cm arasında düz ölçü verilmişse, TABLODAKİ TÜM BEDENLER DÜZ ÖLÇÜDÜR. Tablodaki TÜM BEDENLERİN basen değerlerini İSTİSNASIZ 2 İLE ÇARPARAK TAM ÇEVRE olarak 'basen' anahtarına kaydedin (Örn: 32 beden 46.0 cm ise 46.0*2 = 92.0, 38 beden 53.5 cm ise 53.5*2 = 107.0, 54 beden 76.5 cm ise 76.5*2 = 153.0). Tüm bedenlere aynı işlemi tutarlı uygulayın.\n"
                            "   - 'gogus' (chest): Göğüs/beden genişliği (W221 veya chest). ÇARPMAYIN, düz yarım genişlik (half-width) olarak alın.\n"
                            "   - 'boy' (length): Toplam boy / ürün boyu (L04 veya HPS). Çarpmayın.\n"
                            "   - 'kol_boyu' (sleeve length): Kol boyu (S53 veya kol_boyu). EĞER 'ARKA ORTADAN' (center back) olarak verilmişse, omuzdan omuza genişliğin %50'sini çıkarın (kol_boyu = kol_boyu - omuzdan_omuza / 2).\n"
                            "   - 'etek_eni' (hem width): Etek eni/genişliği (W105 veya etek_eni). Çarpmayın.\n"
                            "   - 'on_ag' (front rise): Ön ağ (L19, ÖN AĞ UZUNLUĞU-KEMER DAHİL). Çarpmayın.\n"
                            "   - 'arka_ag' (back rise): Arka ağ (L21, ARKA AĞ UZUNLUĞU-KEMER DAHİL). Çarpmayın.\n"
                            "   - 'ic_ag' (inseam): İç boy/iç ağ (L259, L103, İÇ BOY-40 CM ALTI). Çarpmayın.\n"
                            "   - 'paca_eni' (leg opening / hem width): Paça genişliği (W252, W178, PAÇA GENİŞLİĞİ-İÇ BOY 16-40 CM ARASI). HER ZAMAN YARIM GENİŞLİK (half-width) olmalıdır. Çarpmayın.\n"
                            "   - 'basen_dusuklugu' (hip drop): Basen düşüklüğü (W17, BASEN DÜŞÜKLÜĞÜ-KEMER DAHİL-YAN). Çarpmayın.\n"
                            "   - 'baldir_genisligi' (thigh width): Baldır genişliği (W20, BALDIR GENİŞLİĞİ). Çarpmayın.\n"
                            "   - 'kemer_yuksekligi' (belt height): Kemer yüksekliği (B04, KEMER YÜKSEKLİĞİ). Çarpmayın.\n"
                            "9. Fırfır / Büzgü Kısıtlaması: Kol tepesi büzgü genişliği ('BÜZGÜ ENİ-KOL TEPESİ'), kol veya yaka ağzı büzgüleri gibi detayları 'firfir' veya 'firfir_eni' olarak kaydetmeyin. Bunları 'buzgu_eni_kol_tepesi' vb. kendi Türkçe isimleriyle kaydedin. 'firfir' sadece genel gövde/etek fırfırları için kullanılacaktır.\n"
                            "10. Tablodaki Diğer Tüm Ölçüm Başlıklarını (rows) Dahil Edin:\n"
                            "   - Teknik föy ölçü tablosundaki (Measurement Table) diğer tüm satırları da (örneğin: Arka Ağ / Back Rise, Baldır Genişliği / Thigh Width, Kemer Yüksekliği / Belt Height, Yaka Açıklığı, Cep Boyu, Fırfır Eni vb.) Türkçe isimleriyle veya anlaşılır anahtarlarla (örneğin: 'arka_ag', 'baldir_genisligi', 'kemer_yuksekligi') her bir beden için çıkarın. Sadece temel parametreleri değil, tablonun tamamındaki satırların tamamını her beden için çıkarıp olculer nesnesine ekleyin.\n"
                            "SADECE ham JSON döndür."
                        )
                        
                        if combined_text and len(combined_text.strip()) > 50:
                            print(f"[PDF PARSER] Executing fast text parse ({len(combined_text)} chars) via Gemini JSON API...")
                            response_text = call_gemini_json(combined_text, prompt)
                        else:
                            print("[PDF PARSER] Scanned PDF detected, falling back to multimodal API...")
                            response_text = None
                    except Exception as ex_pdf:
                        print(f"Local PDF text extraction failed: {ex_pdf}. Falling back to multimodal API...")
                        response_text = None
                
                if not response_text:
                    prompt = (
                        "Bu bir teknik föy (tech pack) dokümanıdır. Dokümandan model adı, ürün grubu, kumaş eni, çekme yüzdeleri, verimlilik, beden asortisi ve özellikle beden ölçülerini (measurement table) çıkar. SADECE JSON formatında veri üret.\n\n"
                        "Çıktı JSON Şeması:\n"
                        "{\n"
                        "  \"model_adi\": \"TOMIX-6S\",\n"
                        "  \"urun_grubu\": \"Elbise\",\n"
                        "  \"kumas_eni_cm\": 150,\n"
                        "  \"cekme_en_yuzde\": 0.0,\n"
                        "  \"cekme_boy_yuzde\": 0.0,\n"
                        "  \"verimlilik_yuzde\": 90.0,\n"
                        "  \"astar_hesapla\": false,\n"
                        "  \"astar_eni_cm\": 140,\n"
                        "  \"astar_cekme_en_yuzde\": 0.0,\n"
                        "  \"astar_cekme_boy_yuzde\": 0.0,\n"
                        "  \"tul_hesapla\": false,\n"
                        "  \"tul_eni_cm\": 150,\n"
                        "  \"tul_cekme_en_yuzde\": 0.0,\n"
                        "  \"tul_cekme_boy_yuzde\": 0.0,\n"
                        "  \"asorti\": {},\n"
                        "  \"olculer\": {\n"
                        "    \"7-8y\": { \"bel\": 65.0, \"basen\": 77.0, \"yan_boy\": 30.0, \"on_ag\": 21.5, \"paca_eni\": 23.75, \"gogus\": 38.0, \"boy\": 65.0, \"kol_boyu\": 18.0, \"etek_eni\": 51.0, \"astar_etek_eni\": 51.0, \"tul_etek_eni\": 145.4 }\n"
                        "  }\n"
                        "}\n\n"
                        "Kurallar:\n"
                        "1. Model Adı (model_adi): Föyün ilk sayfasında veya başlıklarında yer alan model adını veya stil kodunu çıkarın (örn: '1166750 - TOMIX-6S' veya '1160033 - FOSFOR'). Boş bırakmayın.\n"
                        "2. Ürün Grubu (urun_grubu): Modelin ürün grubunu tespit edip şu 4 değerden biri olarak kaydedin: 'Alt Giyim', 'Üst Giyim', 'Elbise', 'Tulum'.\n"
                        "   - Eğer ölçülerde omuzdan boy (OMUZDAN BOY-HPS / boy / length), göğüs (gogus / chest) ve etek ucu genişliği (etek_eni) varsa: 'Elbise'\n"
                        "   - Eğer ölçülerde omuzdan boy, göğüs ve kol boyu varsa fakat etek ucu genişliği yoksa: 'Üst Giyim'\n"
                        "   - Eğer ölçülerde bel, basen, yan boy, ön ağ, paça eni varsa ve üst gövdeye ait ölçüler yoksa: 'Alt Giyim'\n"
                        "   - Eğer ölçülerde omuzdan boy, göğüs, arka ağ, iç ağ, paça eni varsa: 'Tulum'\n"
                        "3. Kumaş Eni (kumas_eni_cm): Belirtilmişse çıkarın, yoksa 150 varsayın.\n"
                        "4. Çekme Oranları (cekme_en_yuzde, cekme_boy_yuzde): Değerleri doğrudan yüzde olarak yazın (örn: %5 çekme ise 5.0 yazın, 0.05 DEĞİL). Dokümanda yoksa 0.0 varsayın.\n"
                        "5. Verimlilik (verimlilik_yuzde): Föyde veya kullanıcı notlarında pastal yerleşim verimliliği belirtilmişse çıkarın (örn: %92 verimlilik için 92.0 yazın). Belirtilmemişse 90.0 varsayın. Boş bırakmayın.\n"
                        "6. Asorti (asorti): Kullanıcı notlarında / talimatlarında (user_text) belirtilmiş bir asorti oranı veya beden adetleri varsa (örneğin: 'Asorti 1-2-3-3-3-2-3-1' veya '1/3 ay 1, 3/6 ay 2...') KESİNLİKLE öncelikli olarak kullanıcının yazdığı asorti bilgisini alın. Kullanıcı yazmışsa föydeki asorti/adet bilgilerini tamamen yok sayın. Beden isimleri anahtar, adetler/oranlar integer değer olmalıdır.\n"
                        "7. Ölçüler (olculer) - ÇOK ÖNEMLİ, DİKKATLİ OKU:\n"
                        "   a) Dokümanın TÜM sayfalarını tara ve ölçü tablosunu (Measurement Table / Spec Table) bul.\n"
                        "   b) Tablonun SÜTUN BAŞLIKLARINI oku — bunlar beden isimleridir (örn: XS, S, M, L, XL, XXL, 2XL, 3XL veya 9-12m, 1-2y, 2-3y, 3-4y, 4-5y, 5-6y, 6-7y, 7-8y, 8-9y, 9-10y, 10-11y, 11-12y, 12-13y, 13-14y veya 34, 36, 38, 40, 42, 44 vb.).\n"
                        "   c) Tablodaki HER SÜTUN (beden) için HER SATIR (ölçüm) değerini oku. Hiçbir sütunu atlama.\n"
                        "   d) DOĞRULAMA: Okuduğun beden sayısı tablodaki sütun sayısıyla eşleşmeli. Eğer tabloda 8 sütun (beden) varsa, olculer nesnesinde de 8 beden olmalı.\n"
                        "   e) Eğer tablo birden fazla sayfaya bölünmüşse, tüm sayfaları birleştirerek eksiksiz oku.\n"
                        "   f) Tolerans aralığı (tolerance) satırlarını ATLA, sadece nominal (hedef) ölçüleri al.\n"
                        "8. Değer Normalizasyonu (Aşağıdaki POM kodları veya isimleri kullanarak ayıklayın):\n"
                        "   - 'bel' (waist): Bel genişliği (W14 veya W13 veya W222 veya bel). Eğer yarım/düz genişlik (half-width, örn: 25-45 cm arası) olarak verilmişse, bunları mutlaka 2 ile çarparak tam çevre (circumference, örn: 58-90 cm) olarak kaydedin.\n"
                        "   - 'basen' (hip): Basen genişliği (W59 veya basen veya hip). Eğer yarım/düz genişlik (half-width, örn: 30-50 cm arası) olarak verilmişse, bunları mutlaka 2 ile çarparak tam çevre (circumference, örn: 72-100 cm) olarak kaydedin.\n"
                        "   - 'gogus' (chest): Göğüs/beden genişliği (W221 veya chest veya half chest veya gogus). ÇARPMAYIN, olduğu gibi düz yarım genişlik (half-width, örn: 30-60 cm) olarak alın.\n"
                        "   - 'boy' (length): Toplam boy / ürün boyu (L04 veya boy veya length veya HPS). Çarpmayın.\n"
                        "   - 'kol_boyu' (sleeve length): Kol boyu (kol veya kol_boyu veya sleeve length). Çarpmayın. EĞER kol boyu ölçüsü 'ARKA ORTADAN' (center back) olarak verilmişse (örneğin 'KOL BOYU-UZUN-ARKA ORTADAN' veya 'S53'), omuzdan omuza (W01 veya omuzdan_omuza) genişliğinin yarısını (%50'sini) bu kol boyu değerinden ÇIKARIN (kol_boyu = kol_boyu - omuzdan_omuza / 2) ve net kol boyu olarak kaydedin. Bu çok önemlidir, aksi takdirde kol alanı olması gerekenden çok daha büyük hesaplanır.\n"
                        "   - 'etek_eni' (hem width): Etek eni/genişliği (W105 veya etek_eni veya hem width). Çarpmayın. Bu her zaman ana beden/astar için düz/küçük olan genişlik olmalıdır (örn. 51.0 cm). Kloş/tül genişliğini buraya yazmayın.\n"
                        "   - 'tul_etek_eni' (tulle hem width): Eğer tüller/kloş etek ucu genişliği varsa ('W107 ETEK UCU GENİŞLİĞİ-KLOŞ ETEK', 'TÜLLER') bunu 'tul_etek_eni' anahtarı altına yazın (örn. 145.4 cm). Yoksa boş veya 0 bırakın.\n"
                        "   - 'astar_etek_eni' (lining hem width): Eğer astara ait düz etek ucu genişliği varsa ('W32 ETEK UCU GENİŞLİĞİ -DÜZ (ASTAR)') veya astar için ayrı bir etek genişliği belirtilmişse bunu 'astar_etek_eni' anahtarı altına yazın. Yoksa normal 'etek_eni' değerini kullanın.\n"
                        "   - 'on_ag' (front rise): Ön ağ (L19 veya on_ag veya front rise). Çarpmayın.\n"
                        "   - 'ic_ag' (inseam): İç boy/iç ağ (L259 veya ic_ag veya inseam). Çarpmayın.\n"
                        "   - 'paca_eni' (hem width): Paça eni/genişliği (W252 veya paca_eni veya hem width). Çarpmayın.\n"
                        "   - 'yan_boy' (outseam): Eğer yan boy doğrudan belirtilmediyse ve 'on_ag' ile 'ic_ag' mevcutsa, ikisini toplayarak atayın.\n"
                        "9. Fırfır / Büzgü Kısıtlaması: Kol tepesi büzgü genişliği ('BÜZGÜ ENİ-KOL TEPESİ'), kol veya yaka ağzı büzgüleri gibi detayları 'firfir' veya 'firfir_eni' olarak kaydetmeyin. Bunları 'buzgu_eni_kol_tepesi' vb. kendi Türkçe isimleriyle kaydedin. 'firfir' sadece genel gövde/etek fırfırları için kullanılacaktır.\n"
                        "10. Tablodaki Diğer Tüm Ölçüm Başlıklarını (rows) Dahil Edin:\n"
                        "   - Teknik föy ölçü tablosundaki (Measurement Table) diğer tüm satırları da (örneğin: Arka Ağ / Back Rise, Baldır Genişliği / Thigh Width, Kemer Yüksekliği / Belt Height, Yaka Açıklığı, Cep Boyu, Fırfır Eni vb.) Türkçe isimleriyle veya anlaşılır anahtarlarla (örneğin: 'arka_ag', 'baldir_genisligi', 'kemer_yuksekligi') her bir beden için çıkarın. Sadece temel parametreleri değil, tablonun tamamındaki satırların tamamını her beden için çıkarıp olculer nesnesine ekleyin.\n"
                        "SADECE ham JSON döndür."
                    )
                    if user_text:
                        prompt = prompt + f"\n\nKullanıcının ekstra girdiği talimatlar/notlar (Lütfen bunları analiz edip kumas_eni_cm, cekme_en_yuzde, cekme_boy_yuzde, asorti ve olculer alanlarını doldururken öncelikli olarak kullanın):\n{user_text}"
                    
                    # Fetch learning records to avoid past mistakes
                    conn_ogrenme = sqlite3.connect(DB_FILE)
                    cursor_ogrenme = conn_ogrenme.cursor()
                    try:
                        cursor_ogrenme.execute("SELECT Hatalar, Dogrular FROM Ogrenme_Kayitlari ORDER BY Tarih DESC LIMIT 10")
                        ogrenme_kayitlari = cursor_ogrenme.fetchall()
                    except sqlite3.OperationalError:
                        ogrenme_kayitlari = [] # Table might not exist yet if not initialized
                    finally:
                        conn_ogrenme.close()
                        
                    if ogrenme_kayitlari:
                        ogrenme_metni = "\nÖnceki hatalardan öğrenilenler (DİKKAT EDİLECEK HUSUSLAR):\n"
                        for idx, (hata, dogru) in enumerate(ogrenme_kayitlari, 1):
                            ogrenme_metni += f"{idx}. YAPILAN HATA: {hata} -> BEKLENEN DOĞRU: {dogru}\n"
                        ogrenme_metni += "Lütfen bu geçmiş hataları tekrar yapmamaya özen göster.\n\n"
                        prompt = prompt.replace("SADECE ham JSON döndür.", ogrenme_metni + "\nSADECE ham JSON döndür.")
                    
                    response_text = call_gemini_file(file_b64, mime_type, prompt)
                
                parsed_json = {}
                if response_text:
                    try:
                        clean_res = response_text.replace("```json", "").replace("```", "").strip()
                        parsed_json = json.loads(clean_res)
                    except Exception as pe:
                        print(f"Error parsing Gemini file response to JSON: {pe}. Raw output: {response_text}")
                        parsed_json = {"error": "JSON parse hatasi", "raw": response_text}
                else:
                    parsed_json = {"error": "Gemini API rate limit or quota error"}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(parsed_json).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

    def do_DELETE(self):
        if self.path.startswith("/api/ogrenme/"):
            try:
                log_id = int(self.path.split("/")[-1])
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Ogrenme_Kayitlari WHERE Log_ID = ?", (log_id,))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    init_db()
    public_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
    if not os.path.exists(public_path):
        os.makedirs(public_path)
    handler = PastalHTTPHandler
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), handler) as httpd:
        print(f"Server successfully started on port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sys.exit(0)
