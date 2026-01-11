import streamlit as st
import xml.etree.ElementTree as ET
import io
import zipfile

# Namespaces uit jouw UBL XML
namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def convert_xml(xml_content):
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    
    tree = ET.parse(io.BytesIO(xml_content))
    root = tree.getroot()
    changed = False

    # 1. Pas EndpointID aan
    endpoint = root.find('.//cac:AccountingCustomerParty/cbc:EndpointID[@schemeID="9925"]', namespaces)
    if endpoint is not None:
        new_val = endpoint.text.replace('BE', '').replace('.', '').strip()
        endpoint.text = new_val
        endpoint.set('schemeID', '0208')
        changed = True

    # 2. Pas PartyIdentification aan
    party_id = root.find('.//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID="9925"]', namespaces)
    if party_id is not None:
        new_val = party_id.text.replace('BE', '').replace('.', '').strip()
        party_id.text = new_val
        party_id.set('schemeID', '0208')
        changed = True

    output = io.BytesIO()
    tree.write(output, encoding='utf-8', xml_declaration=True)
    return output.getvalue(), changed

# --- INTERFACE ---
st.set_page_config(page_title="Peppol Prefix Converter", page_icon="📑")
st.title("🇧🇪 Peppol XML Converter")
st.write("Upload je XML-facturen om de prefix van **9925** naar **0208** om te zetten.")

uploaded_files = st.file_uploader("Selecteer XML bestanden", type="xml", accept_multiple_files=True)

if uploaded_files:
    st.write(f"Aantal bestanden geselecteerd: {len(uploaded_files)}")
    
    # Maak een ZIP bestand aan voor alle verwerkte bestanden
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for uploaded_file in uploaded_files:
            content = uploaded_file.read()
            converted_content, was_changed = convert_xml(content)
            
            # Voeg toe aan ZIP
            zip_file.writestr(uploaded_file.name, converted_content)
            
            if was_changed:
                st.success(f"✅ {uploaded_file.name} is omgezet.")
            else:
                st.info(f"ℹ️ {uploaded_file.name} had geen 9925 prefix.")

    st.divider()
    st.download_button(
        label="📥 Download Alle Gecorrigeerde XML's (.zip)",
        data=zip_buffer.getvalue(),
        file_name="gecorrigeerde_peppol_facturen.zip",
        mime="application/zip"
    )
