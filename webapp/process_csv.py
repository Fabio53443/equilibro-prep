import csv
import sys
import os
from collections import defaultdict

def process_csv(input_file, schools=None):
    # Define output file paths
    base_name = os.path.splitext(input_file)[0]
    output_file1 = f"{base_name}_output1.csv"
    output_file2 = f"{base_name}_output2.csv"
    
    # Track seen ISBNs to avoid duplicates
    seen_isbns = set()
    
    # Read the input CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames
    
    # Filter rows by schools if specified, otherwise include all rows
    filtered_rows = []
    for row in rows:
        # If schools is None (not specified) or if the row's school is in the specified schools
        if schools is None or row['CODICESCUOLA'] in schools:
            filtered_rows.append(row)
    
    # Process first output file like main.py
    # Group by CODICEISBN
    isbn_groups = defaultdict(list)
    for row in filtered_rows:
        isbn = row['CODICEISBN']
        isbn_groups[isbn].append({
            'CODICESCUOLA': row['CODICESCUOLA'],
            'ANNOCORSO': row['ANNOCORSO'],
            'SEZIONEANNO': row['SEZIONEANNO']
        })
    
    # Create output data for first file
    output_data1 = []
    for isbn, group in isbn_groups.items():
        # Create the concatenated string
        concat_values = []
        for item in group:
            concat_values.append(f"{item['CODICESCUOLA']}_{item['ANNOCORSO']}{item['SEZIONEANNO']}")
        
        output_data1.append({
            'CODICEISBN': isbn,
            'CODICESCUOLA_ANNOCORSO_SEZIONEANNO': ', '.join(concat_values)
        })
    
    # Write the first output file with the specified format from main.py
    with open(output_file1, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['CODICEISBN', 'CODICESCUOLA_ANNOCORSO_SEZIONEANNO'])
        writer.writeheader()
        writer.writerows(output_data1)
    
    # Prepare data for the second output file
    data2 = []
    for row in filtered_rows:
        isbn = row['CODICEISBN']
        
        # Skip if we've already seen this ISBN
        if isbn in seen_isbns:
            continue
        
        seen_isbns.add(isbn)
        
        # Format price: convert comma to dot
        price = row['PREZZO'].replace('"', '').replace(',', '.')
        
        # Create title - combine TITOLO and SOTTOTITOLO if SOTTOTITOLO is not "ND"
        title = row['TITOLO']
        if row['SOTTOTITOLO'] != 'ND':
            title = f"{row['TITOLO']} - {row['SOTTOTITOLO']}"
        
        # Add to second output with the specified format
        data2.append({
            'ISBN': isbn,
            'Titolo': title,
            'Materia': row['DISCIPLINA'],
            'Listino': price,
            'EDITORE': row['EDITORE'],
            'Qta tot': '',
            'Qta non venduti': ''
        })
    
    # Write the second output file with the specified format
    with open(output_file2, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ISBN', 'Titolo', 'Materia', 'Listino', 'EDITORE', 'Qta tot', 'Qta non venduti'])
        writer.writeheader()
        writer.writerows(data2)
    
    print(f"Generated {output_file1} and {output_file2}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_csv.py input.csv [school1,school2,...]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Parse schools filter if provided
    schools = None
    if len(sys.argv) > 2:
        schools = set(sys.argv[2].split(','))
    
    process_csv(input_file, schools)
