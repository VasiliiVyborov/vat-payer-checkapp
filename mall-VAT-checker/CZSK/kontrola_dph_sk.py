import os
import requests
import zipfile
import pandas as pd
import xml.etree.ElementTree as ET

data_folder = "data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

def download_and_extract(url, filename):
    zip_path = os.path.join(data_folder, filename)
    extract_path = os.path.join(data_folder, filename.replace(".zip", ""))
    
    if not os.path.exists(extract_path):
        response = requests.get(url)
        with open(zip_path, "wb") as file:
            file.write(response.content)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
    
    return extract_path

def find_file(directory, extensions):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                return os.path.join(root, file)
    return None

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    
    for item in root.findall(".//ITEM"):
        row = {child.tag: child.text for child in item}
        data.append(row)
    
    df = pd.DataFrame(data)
    print(f"🟢 XML soubor {file_path} načten. Celkem řádků: {len(df)}")
    return df

def kontrola_dph_sk(vat_id, bank_account):
    print(f"🔍 Spuštěna kontrola pro VAT ID: {vat_id} a Bank Account: {bank_account}")
    
    vat_id = vat_id.strip()
    bank_account = bank_account.strip()

    lists_url = "https://iz.opendata.financnasprava.sk/api/lists"
    api_key = "6sAz5slpNXNueOXEXIcDJNBVzO8tWdBRShKQMGDXP2enoKwZBbaT19fG5cCtgKMbB2p4kxrRpdzk4APZ61EaYPYH5PT7rhBSBX3irZoZ1I7MUtnx7jCAYEzGhVZyXbzqXloUd8BtiFyh6mS5XTSJpNamv2eR4q8J5vtkaUrExlXFvxy6xLU3N2rBFFDl2jnIPqXhJq0cP5J8DcYC0nB7nexjMgQSEU9oVassQ2w9TjPZyAe81FYSZgJRjZ"
    
    headers = {"key": api_key}
    lists_response = requests.get(lists_url, headers=headers)
    lists_data = lists_response.json()
    
    vat_status, bank_match, year_of_cancellation = "Not Found", "Not Found", "N/A"
    
    for item in lists_data:
        if item["slug"] == "ds_dphz":
            vat_dir = download_and_extract(item["url"], "ds_dphz.zip")
            vat_file = find_file(vat_dir, [".xml"])
            if vat_file:
                vat_df = parse_xml(vat_file)
                
                print(f"🔎 Hledáme VAT ID {vat_id} v celém `ds_dphz.xml`")
                if "IC_DPH" in vat_df.columns:
                    vat_df["IC_DPH"] = vat_df["IC_DPH"].astype(str).str.strip()
                    if vat_id in vat_df["IC_DPH"].values:
                        year_of_cancellation = vat_df.loc[vat_df["IC_DPH"] == vat_id, "ROK_PORUSENIA"].values[0]
                        vat_status = "Cancelled"
                        print(f"✅ Nalezeno! Rok porušení: {year_of_cancellation}")
                    else:
                        vat_status = "Active"
                        print("❌ VAT ID nenalezeno v seznamu zrušených.")
                else:
                    print("❌ Chyba: Sloupce IC_DPH nebo ROK_PORUSENIA nenalezeny!")

        if item["slug"] == "ds_dph_iban":
            bank_dir = download_and_extract(item["url"], "ds_dph_iban.zip")
            bank_file = find_file(bank_dir, [".xml"])
            if bank_file:
                bank_df = parse_xml(bank_file)
                
                print(f"🔎 Hledáme IBAN {bank_account} v celém `ds_dph_iban.xml`")
                if "IBAN" in bank_df.columns:
                    bank_df["IBAN"] = bank_df["IBAN"].astype(str).str.strip()
                    bank_match = "Found" if bank_account in bank_df["IBAN"].values else "Not Found"
                    if bank_match == "Found":
                        print(f"✅ Bankovní účet nalezen!")
                    else:
                        print("❌ Bankovní účet nenalezen!")
                else:
                    print("❌ Chyba: Sloupec IBAN nebyl nalezen!")

    print(f"🟢 FINÁLNÍ VÝSLEDEK → VAT ID: {vat_id} | Status: {vat_status} | Year: {year_of_cancellation} | Bank Match: {bank_match}")
    
    return {
        "VAT ID": vat_id,
        "VAT Status": vat_status,
        "Year of Cancellation": year_of_cancellation,
        "Bank Account Matched": bank_match
    }

def zapis_vysledky_do_excelu(results, output_filename="vat_check_results.xlsx"):
    df = pd.DataFrame(results)
    output_path = os.path.join(data_folder, output_filename)
    df.to_excel(output_path, index=False)
    print(f"📁 Výsledky uloženy do {output_path}")

if __name__ == "__main__":
    vat_id = "SK2023716640"
    bank_account = "SK26750000000004026959816"
    result = kontrola_dph_sk(vat_id, bank_account)
    print("Final Result:", result)
    zapis_vysledky_do_excelu([result])

