import os
import pandas as pd
from zeep import Client, Settings
from zeep.exceptions import Fault

# Funkce pro výpočet kontrolních číslic IBANu
def calculate_iban_check_digits(iban):
    iban_rearranged = iban[4:] + iban[:4]
    iban_numeric = ''.join(str(int(c, 36)) if c.isalpha() else c for c in iban_rearranged)
    remainder = int(iban_numeric) % 97
    check_digits = 98 - remainder
    return f"{check_digits:02}"

# Převod českého formátu na IBAN
def convert_to_iban(account_number, bank_code):
    country_code = 'CZ'
    if '-' in account_number:
        prefix, main_account = account_number.split('-')
    else:
        prefix = ''
        main_account = account_number

    # Doplnění předčíslí, pokud chybí
    full_account_number = prefix.zfill(6) + main_account.zfill(10)
    iban = f"{country_code}00{bank_code}{full_account_number}"
    check_digits = calculate_iban_check_digits(iban)
    iban = f"{country_code}{check_digits}{bank_code}{full_account_number}"
    return iban

# Převod IBANu na český lokální formát
def iban_to_local(iban):
    try:
        bank_code = iban[4:8]  # Kód banky (např. 0300)
        account_details = iban[8:]
        prefix = account_details[:6]  # Předčíslí účtu (např. 000022)
        account_number = account_details[6:]  # Hlavní číslo účtu (např. 12345678)

        if int(prefix) == 0:
            local_format = f"{int(account_number)}/{bank_code}"
        else:
            local_format = f"{int(prefix)}-{int(account_number)}/{bank_code}"
        
        return local_format
    except ValueError:
        return None

# Kontrola, zda účet existuje v registru
def is_account_in_registry(account, registry_accounts):
    if account in registry_accounts:
        return True

    for reg_account in registry_accounts:
        if reg_account:
            converted_account = iban_to_local(reg_account)
            if converted_account and account == converted_account:
                return True
    return False

# Definice názvu WSDL souboru a jeho kontrola
wsdl_filename = "rozhraniCRPDPHSOAP.wsdl"
wsdl_path = os.path.abspath(wsdl_filename)

if not os.path.isfile(wsdl_path):
    raise FileNotFoundError(f"WSDL soubor '{wsdl_filename}' nebyl nalezen v cestě: {wsdl_path}")

# Převedení cesty na formát pro Zeep klient
wsdl = "file:///" + wsdl_path.replace("\\", "/")

# Nastavení klienta
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(wsdl=wsdl, settings=settings)

# Hlavní funkce pro kontrolu DPH
def kontrola_dph(merged_filepath, output_filepath):
    try:
        # Načítání dat s explicitním typem pro sloupce "IČO" a "Bankovní účet" jako text
        data = pd.read_excel(merged_filepath, dtype={'IČO': str, 'Bankovní účet': str})
        
        ico_list = data['IČO'].tolist()
        ucty_list = data['Bankovní účet'].tolist()

        # Nastavení velikosti dávky
        batch_size = 100
        status_list = []
        registry_ucty_list = []

        # Zpracování po dávkách
        for i in range(0, len(ico_list), batch_size):
            batch_ico_list = ico_list[i:i + batch_size]
            batch_ucty_list = ucty_list[i:i + batch_size]

            response = client.service.getStatusNespolehlivyPlatce(dic=batch_ico_list)

            for index, item in enumerate(response.statusPlatceDPH):
                dic = item.dic
                nespolehlivy = item.nespolehlivyPlatce
                status_list.append("ANO" if nespolehlivy == "ANO" else "NE")

                hledany_ucet = batch_ucty_list[index]
                registry_ucty = []

                if hasattr(item, 'zverejneneUcty') and item.zverejneneUcty:
                    for ucet in item.zverejneneUcty.ucet:
                        if hasattr(ucet, 'standardniUcet') and ucet.standardniUcet:
                            predcisli = ucet.standardniUcet.predcisli if ucet.standardniUcet.predcisli else ''
                            cislo = ucet.standardniUcet.cislo
                            kodBanky = ucet.standardniUcet.kodBanky
                            if predcisli == '':
                                registry_ucty.append(f"{cislo}/{kodBanky}")
                            else:
                                registry_ucty.append(f"{predcisli}-{cislo}/{kodBanky}")
                        elif hasattr(ucet, 'nestandardniUcet') and ucet.nestandardniUcet:
                            registry_ucty.append(f"{ucet.nestandardniUcet.cislo}")

                hledany_iban = ''
                hledany_local = ''
                if hledany_ucet.startswith('CZ'):
                    hledany_local = iban_to_local(hledany_ucet)
                    hledane_variants = [hledany_ucet, hledany_local]
                else:
                    try:
                        bank_code = hledany_ucet.split('/')[1]
                        hledany_iban = convert_to_iban(hledany_ucet.split('/')[0], bank_code)
                        hledane_variants = [hledany_ucet, hledany_iban]
                    except IndexError:
                        hledane_variants = [hledany_ucet]

                if any(is_account_in_registry(ucet, registry_ucty) for ucet in hledane_variants):
                    registry_ucty_list.append(hledany_ucet)
                else:
                    registry_ucty_list.append("Nenašel jsem účet")

        data['Nespolehlivý plátce DPH'] = status_list
        data['Bankovní účet z registru DPH'] = registry_ucty_list
        data.to_excel(output_filepath, index=False)

    except Fault as fault:
        raise Exception(f"Chyba při odesílání dotazu na API: {fault}")
    except FileNotFoundError:
        raise Exception("Soubor nebyl nalezen. Zkontrolujte cesty k souborům.")
    except Exception as e:
        raise Exception(f"Neočekávaná chyba: {str(e)}")

if __name__ == '__main__':
    # Testovací volání s použitím lokálního WSDL souboru
    kontrola_dph(merged_filepath='merged_supp_bnk.xlsx', output_filepath='kontrola_uctu_s_nerozpdp.xlsx')

