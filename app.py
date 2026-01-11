import streamlit as st
import xml.etree.ElementTree as ET
import io
import zipfile

# Namespaces voor UBL Invoice conform jouw bestanden
namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def convert_xml(xml_content):
    # Registreer namespaces voor schone XML output
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    
    try:
        tree = ET.parse(io.BytesIO(xml_content))
        root = tree.getroot()
        changed = False

        # 1. Focus op de AccountingCustomerParty (Buyer)
        customer = root.find('.//cac:AccountingCustomerParty', namespaces)
        
        if customer is not None:
            # Zoek het EndpointID met scheme 9925 om het originele BTW-nummer te pakken
            endpoint = customer.find('.//cbc:EndpointID[@schemeID="9925"]', namespaces)
            
            if endpoint is not None:
                original_vat = endpoint.text.strip() if endpoint.text else None
                
                if original_vat:
                    # STAP A: Voeg BTW-nummer toe aan CompanyID binnen PartyTaxScheme
                    tax_id = customer.find('.//cac:PartyTaxScheme/cbc:CompanyID', namespaces)
                    if tax_id is not None:
                        tax_id.text = original_vat
                        changed = True
                    
                    # STAP B: Zet het EndpointID om naar 0208 (zonder BE)
                    new_val = original_vat.replace('BE', '').replace('.', '').strip()
                    endpoint.text = new_val
                    endpoint.set('schemeID', '0208')
                    changed = True

            # Extra check: ook andere ID's binnen de Buyer-sectie met 9925 omzetten naar 0208
            for other_id in customer.findall('.//*[@schemeID="9925"]', namespaces):
                old_val = other_id.text if other_id.text else ""
                other_id.text = old_val.replace('BE', '').replace('.', '').strip()
                other_id.set('schemeID', '0208')
                changed = True

        output = io.BytesIO()
        tree.write(output, encoding='utf-8', xml_declaration=True)
        return output.getvalue(), changed
    except Exception as e:
        return None, str(e)

# --- Streamlit Interface ---
st.set_page_config(page_title="Peppol Buyer Fixer", page_icon="⚙️")
st.title("🇧🇪 Peppol XML Buyer Data Fixer")

st.info('Deze versie kopieert het BTW-nummer van het Endpoint (9925) naar de PartyTaxScheme van de Buyer, en zet daarna het Endpoint om naar 0208.')

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
                    st.success(f"✅ Succesvol verwerkt: {uploaded_file.name}")
                    success_count += 1
            else:
                st.error(f"❌ Fout in {uploaded_file.name}: {result}")

    if success_count > 0:
        st.divider()
        st.download_button(
            label=f"📥 Download {success_count} gecorrigeerde bestanden (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="gecorrigeerde_facturen.zip",
            mime="application/zip"
        )
