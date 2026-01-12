import streamlit as st
import io
import zipfile
import re
import pandas as pd

def fix_xml_inclusive_0088(xml_text, lookup_data=None):
    changed = False
    log_messages = []
    
    # 1. Zoek de Customer sectie
    customer_match = re.search(r'<cac:AccountingCustomerParty>.*?</cac:AccountingCustomerParty>', xml_text, re.DOTALL)
    if not customer_match:
        return xml_text, False, ["❌ FOUT: <cac:AccountingCustomerParty> niet gevonden."]
    
    customer_section = customer_match.group(0)
    
    # 2. Zoek de EndpointID (9925 of 0088)
    endpoint_match = re.search(r'<cbc:EndpointID[^>]*schemeID="(9925|0088)"[^>]*>(.*?)</cbc:EndpointID>', customer_section)
    
    if endpoint_match:
        scheme_id = endpoint_match.group(1)
        original_id = endpoint_match.group(2).strip()
        target_vat = None
        
        if scheme_id == "9925":
            target_vat = original_id
            log_messages.append(f"🔍 9925 gevonden: {original_id}")
        
        elif scheme_id == "0088":
            log_messages.append(f"🔍 0088 (GLN) gevonden: {original_id}")
            if lookup_data is not None and original_id in lookup_data:
                target_vat = lookup_data[original_id]
                log_messages.append(f"✅ BTW gevonden via lookup: {target_vat}")
            else:
                log_messages.append(f"⚠️ GLN {original_id} niet in lijst. BTW-blok kan niet worden gemaakt.")

        if target_vat:
            clean_vat = target_vat.replace('BE', '').replace('.', '').replace(' ', '').strip()
            formatted_vat = "BE" + clean_vat if not clean_vat.startswith("BE") else clean_vat
            
            # STAP A: PartyTaxScheme toevoegen
            if '<cac:PartyTaxScheme>' not in customer_section:
                tax_scheme_xml = f'''<cac:PartyTaxScheme>
        <cbc:CompanyID>{formatted_vat}</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>\n      '''
                if '<cac:PartyLegalEntity>' in customer_section:
                    new_section = customer_section.replace('<cac:PartyLegalEntity>', tax_scheme_xml + '<cac:PartyLegalEntity>')
                    xml_text = xml_text.replace(customer_section, new_section)
                    customer_section = new_section
                    changed = True
                    log_messages.append(f"✨ PartyTaxScheme toegevoegd: {formatted_vat}")

            # STAP B: 9925 naar 0208
            if scheme_id == "9925":
                old_tag = endpoint_match.group(0)
                new_tag = old_tag.replace('schemeID="9925"', 'schemeID="0208"').replace(original_id, clean_vat)
                xml_text = xml_text.replace(old_tag, new_tag)
                changed = True
                log_messages.append(f"✅ EndpointID aangepast naar 0208 ({clean_vat})")
    
    return xml_text, changed, log_messages

# --- Streamlit Interface ---
st.set_page_config(page_title="Peppol XML Fixer incl 0088", page_icon="🇧🇪", layout="wide")

st.title("🇧🇪 Peppol XML Fixer incl 0088")

# Zijbalk voor Lookup Data
st.sidebar.header("Lookup Instellingen")
lookup_file = st.sidebar.file_uploader("Upload GLN-BTW lijst (Excel of CSV)", type=["csv", "xlsx"])
lookup_dict = None

if lookup_file:
    try:
        if lookup_file.name.endswith('.csv'):
            df = pd.read_csv(lookup_file, dtype=str)
        else:
            df = pd.read_excel(lookup_file, dtype=str)
        
        if 'GLN' in df.columns and 'VAT' in df.columns:
            lookup_dict = pd.Series(df.VAT.values, index=df.GLN.values).to_dict()
            st.sidebar.success(f"✅ {len(lookup_dict)} matches geladen.")
        else:
            st.sidebar.error("Kolommen 'GLN' en 'VAT' ontbreken!")
    except Exception as e:
        st.sidebar.error(f"Fout: {e}")

# XML Upload
uploaded_files = st.file_uploader("Upload XML bestanden", type="xml", accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    success_count = 0
    all_logs = []
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in uploaded_files:
            try:
                content_bytes = uploaded_file.read()
                raw_content = content_bytes.decode('utf-8', errors='ignore')
                
                fixed_content, was_changed, logs = fix_xml_inclusive_0088(raw_content, lookup_dict)
                
                zip_file.writestr(uploaded_file.name, fixed_content.encode('utf-8'))
                if was_changed: success_count += 1
                all_logs.append({"file": uploaded_file.name, "changed": was_changed, "details": logs})
            except Exception as e:
                all_logs.append({"file": uploaded_file.name, "changed": False, "details": [f"❌ Systeemfout: {e}"]})

    # Download & Logs
    st.divider()
    if success_count > 0:
        zip_buffer.seek(0)
        st.download_button("📥 Download ZIP", zip_buffer, "peppol_fixed.zip", "application/zip")

    st.subheader("📋 Verwerkingslogboek")
    for entry in all_logs:
        with st.expander(f"{'✅' if entry['changed'] else 'ℹ️'} {entry['file']}"):
            for d in entry["details"]:
                st.write(d)
