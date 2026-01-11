import streamlit as st
import xml.etree.ElementTree as ET
import io
import zipfile

namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def convert_xml(xml_content):
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    
    try:
        tree = ET.parse(io.BytesIO(xml_content))
        root = tree.getroot()
        changed = False

        customer = root.find('.//cac:AccountingCustomerParty', namespaces)
        if customer is not None:
            party = customer.find('cac:Party', namespaces)
            endpoint = customer.find('cbc:EndpointID[@schemeID="9925"]', namespaces)
            
            if endpoint is not None and party is not None:
                original_vat = endpoint.text.strip() if endpoint.text else None
                
                if original_vat:
                    # 1. Zoek of maak PartyTaxScheme aan
                    tax_scheme_elem = party.find('cac:PartyTaxScheme', namespaces)
                    
                    if tax_scheme_elem is None:
                        # Maak nieuwe structuur aan
                        new_tax_scheme = ET.Element('{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme')
                        company_id = ET.SubElement(new_tax_scheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID')
                        company_id.text = original_vat
                        
                        tax_scheme_sub = ET.SubElement(new_tax_scheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme')
                        ts_id = ET.SubElement(tax_scheme_sub, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID')
                        ts_id.text = 'VAT'
                        
                        # Invoegen vóór PartyLegalEntity voor correcte UBL volgorde
                        legal_entity = party.find('cac:PartyLegalEntity', namespaces)
                        if legal_entity is not None:
                            # Zoek index van legal_entity
                            idx = list(party).index(legal_entity)
                            party.insert(idx, new_tax_scheme)
                        else:
                            party.append(new_tax_scheme)
                    else:
                        # Update bestaande
                        company_id = tax_scheme_elem.find('cbc:CompanyID', namespaces)
                        if company_id is not None:
                            company_id.text = original_vat
                    
                    # 2. Zet EndpointID om naar 0208
                    new_val = original_vat.replace('BE', '').replace('.', '').strip()
                    endpoint.text = new_val
                    endpoint.set('schemeID', '0208')
                    changed = True

        output = io.BytesIO()
        tree.write(output, encoding='utf-8', xml_declaration=True)
        return output.getvalue(), changed
    except Exception as e:
        return None, str(e)

# --- Streamlit Interface blijft hetzelfde ---
st.set_page_config(page_title="Peppol Fixer v3", page_icon="⚙️")
st.title("🇧🇪 Peppol XML Buyer Tax Fixer")
st.info('Deze versie creëert automatisch de PartyTaxScheme als deze ontbreekt.')

uploaded_files = st.file_uploader("Upload XML bestanden", type="xml", accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    success_count = 0
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for uploaded_file in uploaded_files:
            content = uploaded_file.read()
            converted_content, result = convert_xml(content)
            if converted_content is not None:
                zip_file.writestr(uploaded_file.name, converted_content)
                if result:
                    st.success(f"✅ Verwerkt (incl. TaxScheme): {uploaded_file.name}")
                    success_count += 1
            else:
                st.error(f"❌ Fout in {uploaded_file.name}: {result}")

    if success_count > 0:
        st.divider()
        st.download_button(label="📥 Download ZIP", data=zip_buffer.getvalue(), file_name="fixed_invoices.zip")
