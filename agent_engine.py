import sqlite3
import json

class PastalAgent:
    def __init__(self, db_file, api_key, model, call_gemini_json_fn):
        self.db_file = db_file
        self.api_key = api_key
        self.model = model
        self.call_gemini_json_fn = call_gemini_json_fn

    def analyze_feedback(self, calisma_id, gerceklesen_tuketim, gerceklesen_astar_tuketim, gerceklesen_tul_tuketim,
                         gerceklesen_asorti, gerceklesen_kumas_eni, gerceklesen_cekme_en, gerceklesen_cekme_boy):
        """
        Analyzes the realized production feedback using Gemini, detects outliers,
        logs the decision, and updates Maliyet_Calismalari accordingly.
        """
        print(f"[AGENT] Analyzing feedback for Calisma_ID: {calisma_id}...")

        # 1. Fetch planned values from database
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, m.Model_Adi, m.Urun_Grubu
            FROM Maliyet_Calismalari c
            LEFT JOIN Model_Tanimlari m ON c.Model_ID = m.Model_ID
            WHERE c.Calisma_ID = ?
        """, (int(calisma_id),))
        study = cursor.fetchone()
        
        if not study:
            conn.close()
            raise ValueError(f"Study with ID {calisma_id} not found.")

        # Prepare parameters for analysis
        model_name = study["Model_Adi"] or "Bilinmeyen"
        urun_grubu = study["Urun_Grubu"] or "Bilinmeyen"
        
        planned_kumas_eni = study["Kumas_Eni_cm"]
        planned_cekme_en = study["Cekme_En_Yuzde"]
        planned_cekme_boy = study["Cekme_Boy_Yuzde"]
        planned_verimlilik = study["Verimlilik_Yuzde"] or 90.0
        planned_birim = study["Hesaplanan_Birim_Metraj_M"]
        planned_asorti_str = study["Asorti_JSON"]
        olculer_str = study["Olculer_JSON"]

        planned_astar_birim = study["Hesaplanan_Astar_Birim_M"] or 0.0
        planned_tul_birim = study["Hesaplanan_Tul_Birim_M"] or 0.0

        # Set fallback values if realized parameters are not provided
        real_kumas_eni = int(gerceklesen_kumas_eni) if gerceklesen_kumas_eni is not None and str(gerceklesen_kumas_eni).strip() != "" else planned_kumas_eni
        real_cekme_en = float(gerceklesen_cekme_en) if gerceklesen_cekme_en is not None and str(gerceklesen_cekme_en).strip() != "" else planned_cekme_en
        real_cekme_boy = float(gerceklesen_cekme_boy) if gerceklesen_cekme_boy is not None and str(gerceklesen_cekme_boy).strip() != "" else planned_cekme_boy

        real_birim_val = float(gerceklesen_tuketim) if gerceklesen_tuketim is not None and str(gerceklesen_tuketim).strip() != "" else None
        real_astar_val = float(gerceklesen_astar_tuketim) if gerceklesen_astar_tuketim is not None and str(gerceklesen_astar_tuketim).strip() != "" else None
        real_tul_val = float(gerceklesen_tul_tuketim) if gerceklesen_tul_tuketim is not None and str(gerceklesen_tul_tuketim).strip() != "" else None
        real_asorti_str = json.dumps(gerceklesen_asorti) if gerceklesen_asorti is not None else planned_asorti_str

        # Fetch Custom Analysis Rules
        try:
            cursor.execute("SELECT Dogrular FROM Ogrenme_Kayitlari WHERE Tip = 'analiz_kurali' ORDER BY Tarih DESC")
            custom_rules = cursor.fetchall()
            custom_rules_text = ""
            if custom_rules:
                custom_rules_text = "\n\nKullanıcının Belirlediği Özel Analiz ve Hesaplama Kuralları:\n"
                for rule in custom_rules:
                    if rule[0]:
                        custom_rules_text += f"- {rule[0]}\n"
        except sqlite3.OperationalError:
            custom_rules_text = ""


        # 2. Build prompt for structured outlier detection and analysis
        prompt = f"""
        Kullanıcı gerçekleşen üretim verilerini girdi. Girdileri analiz ederek bir veri kalitesi/aykırı değer (outlier) denetimi gerçekleştir ve ardından kök neden analizi raporu hazırla.

        MODEL DETAYLARI:
        - Model: {model_name} ({urun_grubu})
        - Beden Ölçüleri (Kalıp Alanları): {olculer_str}

        ANA KUMAŞ HESAPLAMALARI:
        - Planlanan Kumaş Eni: {planned_kumas_eni} cm | Gerçekleşen: {real_kumas_eni} cm
        - Planlanan Çekme (En/Boy): %{planned_cekme_en} / %{planned_cekme_boy} | Gerçekleşen: %{real_cekme_en} / %{real_cekme_boy}
        - Hesaplanan (Planlanan) Birim Sarfiyat: {planned_birim} m
        - Gerçekleşen Birim Sarfiyat: {real_birim_val if real_birim_val is not None else 'Girilmedi'} m

        ASTAR VE TÜL HESAPLAMALARI:
        - Planlanan Astar Sarfiyatı: {planned_astar_birim} m | Gerçekleşen: {real_astar_val if real_astar_val is not None else 'Girilmedi'} m
        - Planlanan Tül Sarfiyatı: {planned_tul_birim} m | Gerçekleşen: {real_tul_val if real_tul_val is not None else 'Girilmedi'} m

        ASORTİ DAĞILIMI:
        - Planlanan Asorti: {planned_asorti_str}
        - Gerçekleşen Asorti: {real_asorti_str}{custom_rules_text}

        GÖREVLER:
        1. **Veri Doğrulama ve Aykırı Değer Kontrolü (Validation & Outlier Detection):**
           - Girilen gerçekleşen metrajlar sıfır veya negatif olmamalıdır.
           - Planlanan metraj ile gerçekleşen metraj arasında aşırı veya mantıksız bir fark olmamalıdır (örneğin planlanan 1.35m iken gerçekleşen 13.5m girilmişse bu büyük ihtimalle bir yazım hatası veya sistem dışı olağanüstü bir hatadır. Aynı şekilde planlanan 1.35m iken gerçekleşenin 0.1m girilmesi mantıksızdır).
           - Sapma oranı ±%50'den büyük ise bunu 'outlier' olarak işaretle.
           - Eğer veri geçersiz veya aykırı ise 'use_in_calibration' değerini false yap.
        2. **Kök Neden Analizi (Root Cause Analysis):**
           - Sapma oranını ve yönünü (fazla/eksik hesaplama) yüzde olarak hesapla.
           - Asorti dağılımı değişmişse, bunun tüketim üzerindeki etkisini değerlendir.
           - Sapmanın tekstil kesim geometrisi ve çekme payı açısından nedenlerini açıkla.
        3. **Çıktı Biçimi:**
           - Aşağıdaki JSON yapısında bir çıktı üret. JSON dışı hiçbir metin yazma.
           - 'analysis_html' alanı içinde listeler (<ul><li>), kalın yazılar (<strong>), başlıklar (<h4>) içeren temiz bir HTML formatında, doğrudan, samimi ve Türkçe yazılmış bir analiz raporu sun.

        GEREKLİ JSON YANIT YAPISI:
        {{
            "is_valid": true_or_false,
            "is_outlier": true_or_false,
            "use_in_calibration": true_or_false,
            "reasoning": "Ajanın veriyi kabul/ret etme gerekçesi (Örn: Veri normal aralıkta, kalibrasyona dahil edildi.)",
            "analysis_html": "<p>Detaylı analiz raporu buraya gelecek...</p>"
        }}
        """

        system_prompt = "Sen Birim Sarf Asistanı uygulamasının akıllı tekstil mühendisliği ve yapay zeka kalibrasyon motorusun. Girdi denetimi, aykırı değer tespiti ve kök neden analizi yaparsın."

        try:
            # Call Gemini
            response_str = self.call_gemini_json_fn(prompt, system_prompt)
            agent_res = json.loads(response_str)
        except Exception as e:
            print(f"[AGENT] Error calling Gemini: {e}")
            agent_res = {
                "is_valid": True,
                "is_outlier": False,
                "use_in_calibration": True,
                "reasoning": f"Gemini bağlantı hatası sebebiyle varsayılan olarak kabul edildi: {e}",
                "analysis_html": f"<p>Gerçekleşen üretim verileri kaydedildi fakat yapay zeka analizine ulaşılamadı. Hata: {e}</p>"
            }

        is_valid = 1 if agent_res.get("is_valid", True) else 0
        is_outlier = 1 if agent_res.get("is_outlier", False) else 0
        use_in_calibration = 1 if agent_res.get("use_in_calibration", True) else 0
        reasoning = agent_res.get("reasoning", "")
        analysis_html = agent_res.get("analysis_html", "")

        # 3. Log agent's decision to Agent_Decision_Logs
        cursor.execute("""
            INSERT INTO Agent_Decision_Logs (Calisma_ID, Decision_Type, Is_Valid, Is_Outlier, Use_In_Calibration, Reasoning)
            VALUES (?, 'Feedback_Analysis', ?, ?, ?, ?)
        """, (int(calisma_id), is_valid, is_outlier, use_in_calibration, reasoning))

        # 4. Update Maliyet_Calismalari with calibration flag and analysis HTML
        cursor.execute("""
            UPDATE Maliyet_Calismalari
            SET Use_In_Calibration = ?,
                Agent_Analysis_HTML = ?,
                Gerceklesen_Birim_Metraj_M = ?,
                Gerceklesen_Astar_Birim_M = ?,
                Gerceklesen_Tul_Birim_M = ?,
                Gerceklesen_Asorti_JSON = ?,
                Gerceklesen_Kumas_Eni_cm = ?,
                Gerceklesen_Cekme_En_Yuzde = ?,
                Gerceklesen_Cekme_Boy_Yuzde = ?
            WHERE Calisma_ID = ?
        """, (use_in_calibration, analysis_html, real_birim_val, real_astar_val, real_tul_val, real_asorti_str,
              real_kumas_eni, real_cekme_en, real_cekme_boy, int(calisma_id)))

        conn.commit()
        conn.close()

        print(f"[AGENT] Feedback analysis complete. Use_In_Calibration: {use_in_calibration}, Outlier: {is_outlier}")
        return {
            "success": True,
            "is_outlier": bool(is_outlier),
            "use_in_calibration": bool(use_in_calibration),
            "reasoning": reasoning,
            "analysis": analysis_html
        }
