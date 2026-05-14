import pandas as pd

def sloucit_data(zsupplier_path, bnk_path, output_path="merged_supp_bnk.xlsx"):
    """
    Sloučí data ze ZSUPPLIER a BNK souborů a vytvoří merged_supp_bnk.xlsx
    :param zsupplier_path: Cesta k ZSUPPLIER souboru
    :param bnk_path: Cesta k BNK souboru
    :param output_path: Výstupní cesta pro sloučený soubor
    """
    # Načtení dat ze souborů
    supp_df = pd.read_excel(zsupplier_path)
    bnk_df = pd.read_excel(bnk_path)

    # Úprava DIČ: Tahání dat ze sloupce 'DIČ', odstranění 'CZ' a převod na text
    supp_df['IČO'] = supp_df['DIČ'].apply(
        lambda x: x[2:] if pd.notna(x) and x.startswith('CZ') else "Není plátce DPH" if pd.isna(x) else x
    )

    # Zajistíme, že kód banky je uložen jako text, aby se zachoval správný formát (např. 0100 místo 100)
    bnk_df['Kód banky'] = bnk_df['Kód banky'].apply(lambda x: str(x).zfill(4) if pd.notna(x) else '')

    # Sloučení na základě názvu firmy
    merged_df = pd.merge(supp_df, bnk_df[['Název 1', 'IBAN', 'Bank.účet', 'Kód banky']], 
                         left_on='Jméno 1', right_on='Název 1', how='left')

    # Přidání informace o chybějícím účtu
    merged_df['Bankovní účet'] = merged_df.apply(
        lambda row: f"{row['Bank.účet']}/{row['Kód banky']}" if pd.notna(row['Bank.účet']) and pd.isna(row['IBAN']) else row['IBAN'],
        axis=1
    )

    merged_df['Bankovní účet'] = merged_df['Bankovní účet'].fillna('Bankovní účet chybí v SAP')

    # Výběr potřebných sloupců a přejmenování
    result_df = merged_df[['Bankovní účet', 'IČO', 'Jméno 1', 'Dodavatel']]
    result_df.columns = ['Bankovní účet', 'IČO', 'Název firmy', 'SAP ID']

    # Uložení výsledku do souboru
    result_df.to_excel(output_path, index=False)
    print(f"Data byla úspěšně sloučena a uložena do souboru: {output_path}")
