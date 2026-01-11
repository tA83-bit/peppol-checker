import os
import xml.etree.ElementTree as ET

# De namespaces specifiek voor jouw UBL Invoice
namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def fix_be_peppol_id(file_path, output_path):
    # Registreer namespaces voor een schone output
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Wijziging 1: EndpointID (van 9925 naar 0208)
        endpoint = root.find('.//cac:AccountingCustomerParty/cbc:EndpointID[@schemeID="9925"]', namespaces)
        if endpoint is not None:
            new_val = endpoint.text.replace('BE', '').replace('.', '').strip()
            endpoint.text = new_val
            endpoint.set('schemeID', '0208')

        # Wijziging 2: PartyIdentification
        party_id = root.find('.//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID="9925"]', namespaces)
        if party_id is not None:
            new_val = party_id.text.replace('BE', '').replace('.', '').strip()
            party_id.text = new_val
            party_id.set('schemeID', '0208')

        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"Fout bij verwerken van {file_path}: {e}")
        return False

# --- CONFIGURATIE ---
# Gebruik '.' voor de huidige map waar het script staat
input_folder = '.' 
output_folder = 'gecorrigeerde_xmls'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Lus door de bestanden
found_files = False
for filename in os.listdir(input_folder):
    if filename.endswith('.xml'):
        found_files = True
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        if fix_be_peppol_id(input_path, output_path):
            print(f"Succes: {filename} omgezet naar schema 0208.")

if not found_files:
    print(f"Geen XML-bestanden gevonden in map: {os.path.abspath(input_folder)}")
