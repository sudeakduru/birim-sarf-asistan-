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
