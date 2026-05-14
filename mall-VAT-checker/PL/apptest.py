import customtkinter as ctk
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NIPKombajn(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GUS & VIES Vysavač")
        self.geometry("500x550")

        self.api_label = ctk.CTkLabel(self, text="GUS API Klíč:")
        self.api_label.pack(pady=(20, 5))
        self.api_entry = ctk.CTkEntry(self, width=300, show="*")
        self.api_entry.pack()

        self.test_var = ctk.BooleanVar(value=False)
        self.test_checkbox = ctk.CTkCheckBox(self, text="Použít TESTOVACÍ server (natvrdo použije test klíč)", variable=self.test_var)
        self.test_checkbox.pack(pady=10)

        self.nip_label = ctk.CTkLabel(self, text="Syp sem NIPy (každej na novej řádek):")
        self.nip_label.pack(pady=(10, 5))
        self.nip_box = ctk.CTkTextbox(self, width=300, height=150)
        self.nip_box.pack()

        self.run_btn = ctk.CTkButton(self, text="Spustit těžbu", command=self.makej)
        self.run_btn.pack(pady=20)
        
        self.status_label = ctk.CTkLabel(self, text="Status: Čekám na povel...", text_color="gray")
        self.status_label.pack(pady=(5, 10))

    def check_vies(self, nip):
        url = f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/PL/vat/{nip}"
        try:
            resp = requests.get(url, timeout=5).json()
            return "Active" if resp.get("isValid") else "Inactive/Invalid"
        except:
            return "Error/Timeout"

    def vykuchej_xml(self, text):
        match = re.search(r'(<[a-zA-Z0-9:]*Envelope.*</[a-zA-Z0-9:]*Envelope>)', text, re.DOTALL)
        return match.group(1) if match else text

    def uloz_error(self, text):
        with open("GUS_ERROR.txt", "w", encoding="utf-8") as f:
            f.write(text)

    def makej(self):
        nipy_raw = self.nip_box.get("1.0", "end-1c").strip()
        
        # Tvrdej override - pokud je test, sereme na to, co user napsal do políčka
        if self.test_var.get():
            url_gus = "https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
            api_klic = "abcde12345abcde12345"
        else:
            url_gus = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
            api_klic = self.api_entry.get().strip()

        if not api_klic or not nipy_raw:
            self.status_label.configure(text="Hovno zle, chybí klíč nebo NIPy!", text_color="red")
            return

        nipy = [n.strip() for n in nipy_raw.split('\n') if n.strip()]
        self.status_label.configure(text=f"Makám na tom... {len(nipy)} kousků.", text_color="yellow")
        self.update() 

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        zaloguj_xml = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:ns="http://CIS/BIR/PUBL/2014/07">
            <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                <wsa:To>{url_gus}</wsa:To>
                <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj</wsa:Action>
            </soap:Header>
            <soap:Body>
                <ns:Zaloguj><ns:pKluczUzytkownika>{api_klic}</ns:pKluczUzytkownika></ns:Zaloguj>
            </soap:Body>
        </soap:Envelope>"""

        try:
            res_login = requests.post(url_gus, data=zaloguj_xml.encode('utf-8'), headers=headers)
            cisty_xml = self.vykuchej_xml(res_login.text)

            try:
                root_login = ET.fromstring(cisty_xml)
            except ET.ParseError:
                self.uloz_error(res_login.text)
                self.status_label.configure(text="Kiks! Otevři GUS_ERROR.txt a pošli mi to.", text_color="red")
                return

            sid_element = root_login.find('.//{http://CIS/BIR/PUBL/2014/07}ZalogujResult')
            
            if sid_element is None or not sid_element.text:
                self.status_label.configure(text="Zamítnuto! GUS tenhle klíč prostě nezná.", text_color="red")
                return
                
            sid = sid_element.text
            headers['sid'] = sid
            vysledky = []

            for nip in nipy:
                vies_status = self.check_vies(nip)
                
                szukaj_xml = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:ns="http://CIS/BIR/PUBL/2014/07" xmlns:dat="http://CIS/BIR/PUBL/2014/07/DataContract">
                    <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                        <wsa:To>{url_gus}</wsa:To>
                        <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty</wsa:Action>
                    </soap:Header>
                    <soap:Body>
                        <ns:DaneSzukajPodmioty>
                            <ns:pParametryWyszukiwania><dat:Nip>{nip}</dat:Nip></ns:pParametryWyszukiwania>
                        </ns:DaneSzukajPodmioty>
                    </soap:Body>
                </soap:Envelope>"""

                try:
                    res_szukaj = requests.post(url_gus, data=szukaj_xml.encode('utf-8'), headers=headers)
                    cisty_xml_szukaj = self.vykuchej_xml(res_szukaj.text)
                    
                    try:
                        root_szukaj = ET.fromstring(cisty_xml_szukaj)
                    except ET.ParseError:
                        self.uloz_error(res_szukaj.text)
                        raise Exception("Kiks! Otevři GUS_ERROR.txt a mrdni to sem.")

                    wynik = root_szukaj.find('.//{http://CIS/BIR/PUBL/2014/07}DaneSzukajPodmiotyResult')
                    
                    if wynik is not None and wynik.text:
                        dane_root = ET.fromstring(wynik.text)
                        dane = dane_root.find('dane')
                        if dane is not None:
                            regon = dane.findtext('Regon', 'Nenalezeno')
                            nazwa = dane.findtext('Nazwa', 'Nenalezeno')
                            ulica = dane.findtext('Ulica', '')
                            nr = dane.findtext('NrNieruchomosci', '')
                            kod = dane.findtext('KodPocztowy', '')
                            miejscowosc = dane.findtext('Miejscowosc', '')
                            adresa = f"{ulica} {nr}, {kod} {miejscowosc}".strip()
                            status_gus = "Ukončená" if dane.findtext('DataZakonczeniaDzialalnosci') else "Aktivní"
                        else:
                            regon, nazwa, adresa, status_gus = "Nenalezeno", "Nenalezeno", "Nenalezeno", "Nenalezeno"
                    else:
                        regon, nazwa, adresa, status_gus = "Nenalezeno", "Nenalezeno", "Nenalezeno", "Nenalezeno"
                except Exception as e:
                    regon, nazwa, adresa, status_gus = "Error", f"Chyba GUSu", str(e), "Error"

                vysledky.append({
                    "NIP": nip,
                    "REGON": regon,
                    "Název firmy": nazwa,
                    "Adresa": adresa,
                    "GUS Status": status_gus,
                    "VIES Status": vies_status
                })

            wyloguj_xml = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:ns="http://CIS/BIR/PUBL/2014/07">
                <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                    <wsa:To>{url_gus}</wsa:To>
                    <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj</wsa:Action>
                </soap:Header>
                <soap:Body>
                    <ns:Wyloguj><ns:pIdentyfikatorSesji>{sid}</ns:pIdentyfikatorSesji></ns:Wyloguj>
                </soap:Body>
            </soap:Envelope>"""
            requests.post(url_gus, data=wyloguj_xml.encode('utf-8'), headers=headers)

            df = pd.DataFrame(vysledky)
            df.to_excel("GUS_VIES_vysledky.xlsx", index=False)
            
            self.status_label.configure(text="Hotovo bejku! Soubor GUS_VIES_vysledky.xlsx je na světě.", text_color="green")

        except Exception as e:
            self.status_label.configure(text=f"{str(e)}", text_color="red")

if __name__ == "__main__":
    app = NIPKombajn()
    app.mainloop()