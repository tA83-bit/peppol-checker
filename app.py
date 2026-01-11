import os
import xml.etree.ElementTree as ET

# De namespaces uit jouw voorbeeldbestand
namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def fix_be_peppol_id(file_path, output_path):
    # Registreer namespaces om de 'ns0:' prefix in de output te voorkomen
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")

    tree = ET.parse(file_path)
    root = tree.getroot()

    # 1. Pas het EndpointID van de AccountingCustomerParty aan
    endpoint = root.find('.//cac:AccountingCustomerParty/cbc:EndpointID[@schemeID="9925"]', namespaces)
    if endpoint is not None:
        old_val = endpoint.text
        # Verwijder BE en eventuele punten/spaties
        new_val = old_val.replace('BE', '').replace('.', '').strip()
        endpoint.text = new_val
        endpoint.set('schemeID', '0208')
        print(f"EndpointID aangepast: {old_val} -> 0208:{new_val}")

    # 2. Pas de PartyIdentification van de AccountingCustomerParty aan
    party_id = root.find('.//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID="9925"]', namespaces)
    if party_id is not None:
        old_val = party_id.text
        new_val = old_val.replace('BE', '').replace('.', '').strip()
        party_id.text = new_val
        party_id.set('schemeID', '0208')
        print(f"PartyID aangepast: {old_val} -> 0208:{new_val}")

    # Opslaan met behoud van XML declaratie
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

# Uitvoeren voor jouw map
input_folder = 'jouw_map_met_xmls'
output_folder = 'gecorrigeerde_xmls'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for filename in os.listdir(input_folder):
    if filename.endswith('.xml'):
        fix_be_peppol_id(os.path.join(input_folder, filename), os.path.join(output_folder, filename))
