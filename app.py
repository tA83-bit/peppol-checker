def convert_xml(xml_content):
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    
    tree = ET.parse(io.BytesIO(xml_content))
    root = tree.getroot()
    changed = False

    # We zoeken nu in de hele AccountingCustomerParty sectie naar schemeID 9925
    customer_party = root.find('.//cac:AccountingCustomerParty', namespaces)
    
    if customer_party is not None:
        # Zoek alle elementen met schemeID 9925 binnen de klant-sectie
        targets = customer_party.findall('.//*[@schemeID="9925"]', namespaces)
        
        for elem in targets:
            old_val = elem.text
            # Verwijder BE, punten en spaties
            new_val = old_val.replace('BE', '').replace('.', '').strip()
            
            # Update naar het nieuwe schema
            elem.text = new_val
            elem.set('schemeID', '0208')
            changed = True
            
    output = io.BytesIO()
    tree.write(output, encoding='utf-8', xml_declaration=True)
    return output.getvalue(), changed
