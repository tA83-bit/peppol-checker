import streamlit as st
import xml.etree.ElementTree as ET
import io
import zipfile

# Definieer de namespaces exact zoals in jouw UBL-bestanden
namespaces = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'inv': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def convert_xml(xml_content):
    # Registreer de namespaces voor een schone output zonder 'ns0'
    ET.register_namespace('', "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    ET.register_namespace('cac', "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    ET.register_namespace('cbc', "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    
    try:
        tree = ET.parse(io.BytesIO(xml_content))
        root = tree.getroot()
        changed = False

        # Zoek robuust naar alle elementen die een schemeID="9925" hebben
        for elem in root.iter():
            if elem.get('schemeID') == '9925':
                old_val = elem.text if elem.text else ""
                # Verwijder BE, punten en spaties
                new_val = old_val.replace('BE', '').replace('.', '').strip()
                
                elem.text = new_val
                elem.set('schemeID', '0208')
                changed = True

        output = io.BytesIO()
        tree.write(output, encoding='utf-8', xml_declaration=True)
        return output.getvalue(), changed
    except Exception as e:
        return None, str(e)

# --- Streamlit Interface ---
st.set_page_config(page_title="Peppol Fixer", page_icon="⚙️")

st.title("🇧🇪 Peppol XML Prefix Fixer")

# CORRECTIE: Gebruik enkele aanhalingstekens om de tekst heen om syntax errors te voorkomen
st.info('Deze tool zet alle schemeID="9925" (BTW) om naar schemeID="0208" (KBO) en verwijdert BE.')

uploaded_files = st.file_uploader("Upload je XML bestanden", type="xml", accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    success_count = 0
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for uploaded_file in uploaded_files:
            content = uploaded_file.read()
            converted_content, result = convert_xml(content)
            
            if converted_content is not None:
                zip_file.writestr(uploaded_file.name, converted_content)
                if result is True: # status is 'changed'
                    st.success(f"✅ Gecorrigeerd: {uploaded_file.name}")
                    success_count += 1
                else:
                    st.warning(f"⚠️ Geen 9925 gevonden in: {uploaded_file.name}")
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
