import requests
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import time

# Function to get company details from ARES REST API
def get_company_details(ico):
    url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}"
    
    # Sending request to the ARES API
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            
            # Extract the necessary fields
            name = data.get('obchodniJmeno', 'N/A')
            address = data.get('sidlo', {}).get('textovaAdresa', 'N/A')
            
            return name, address
        
        except Exception as e:
            print(f"Error parsing JSON for IČO: {ico}")
            print(f"Response text: {response.text}")
            return None, None
    elif response.status_code == 403:
        print(f"Error: Unable to fetch data for IČO {ico}. Status code: 403 (Forbidden)")
    elif response.status_code == 404:
        print(f"Error: Unable to fetch data for IČO {ico}. Status code: 404 (Not Found)")
    else:
        print(f"Error: Unable to fetch data for IČO {ico}. Status code: {response.status_code}")
    
    return None, None

# Main function to process input and output files
def process_excel(input_file, output_file):
    # Read the input Excel file, ensuring ICO is read as a string
    df = pd.read_excel(input_file, dtype={'ICO': str})

    # Initialize empty lists to store results
    names = []
    addresses = []

    # Loop through each ICO and fetch data from ARES
    for ico in df['ICO']:
        name, address = get_company_details(ico)
        names.append(name)
        addresses.append(address)
        
        # Add a delay between requests to avoid being blocked by the server
        time.sleep(0.5)  # 500ms delay

    # Add the results to the DataFrame
    df['Název'] = names
    df['Adresa'] = addresses

    # Save the updated DataFrame to a new Excel file
    df.to_excel(output_file, index=False)

    print(f"Data successfully saved to {output_file}")

# Function to select input and output files
def select_files():
    # Hide the main window
    Tk().withdraw()

    # Select input file (Excel file)
    input_file = askopenfilename(
        title="Select the input Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")],
    )

    # Select output file (where to save the new Excel file)
    output_file = asksaveasfilename(
        title="Save the output Excel file",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
    )

    return input_file, output_file

# Main execution
if __name__ == "__main__":
    input_file, output_file = select_files()
    process_excel(input_file, output_file)
