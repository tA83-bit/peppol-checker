import streamlit as st
import io
import zipfile
import re

def fix_xml_minimal_changes(xml_text):
    changed = False
    
    # 1. Zoek het BTW-nummer in de AccountingCustomerParty (EndpointID met schemeID="9925")
    # We zoeken specifiek binnen de CustomerParty sectie om fouten te voorkomen
    customer_match = re.search(r'<cac:AccountingCustomerParty>.*?</cac:AccountingCustomerParty>', xml_text, re.DOTALL)
    if not customer_match:
        return xml_text, False
    
    customer_section = customer_match.group(0)
    
    # Zoek het 9925 BTW nummer
    vat_match = re.search(r'<cbc:EndpointID[^>]*schemeID="9925"[^>]*>(.*?)</cbc:EndpointID>', customer_section)
    
    if vat_match:
        original_vat = vat_match.group(1).strip()
        # Maak de 0208 versie (zonder BE, zonder punten)
        clean_vat = original_vat.replace('BE', '').replace('.', '').strip()
        
        # STAP A: Voeg PartyTaxScheme toe voor de PartyLegalEntity als deze nog niet bestaat
        if '<cac:PartyTaxScheme>' not in customer_section:
            tax_scheme_xml = f'''<cac:PartyTaxScheme>
        <cbc:CompanyID>{original_vat}</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>\n      '''
            # Voeg in vlak voor PartyLegalEntity om de structuur te behouden
            if '<cac:PartyLegalEntity>' in customer_section:
                new_customer_section = customer_section.replace('<cac:PartyLegalEntity>', tax_scheme_xml + '<cac:PartyLegalEntity>')
                xml_text = xml_text.replace(customer_section, new_customer_section)
                customer_section = new_customer_section
                changed = True

        # STAP B: Vervang alleen in de customer_section de 9925 door 0208
        # We doen dit heel specifiek om de rest van het document niet te raken
        old_endpoint = vat_match.group(0)
        # Behoud eventuele extra spaties in de tag, maar verander schemeID en de waarde
        new_endpoint = re.sub(r'schemeID="9925"', 'schemeID="0208"', old_endpoint)
        new_endpoint = new_endpoint.replace(original_vat, clean_vat)
        
        new_customer_section = customer_section.replace(old_endpoint, new_endpoint)
        xml_text = xml_text.replace(customer_section, new_customer_section)
        changed = True

    return xml_text, changed

# --- Streamlit Interface ---
st.set_page_config(page_title="Peppol Minimal Fixer", page_icon="🇧🇪")
st.title("🇧🇪 Peppol XML Fixer (Raw Text Mode)")
st.info("Deze versie past alleen de noodzakelijke regels aan. De rest van het bestand (namespaces, witregels, declaratie) blijft 1:1 gelijk aan het origineel.")

uploaded_files = st.file_uploader("Upload XML bestanden", type="xml", accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    success_count = 0
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in uploaded_files:
            # Lees als tekst om witregels te bewaren
            raw_content = uploaded_file.read().decode('utf-8')
            
            fixed_content, was_changed = fix_xml_minimal_changes(raw_content)
            
            # Opslaan in ZIP (als UTF-8 tekst)
            zip_file.writestr(uploaded_file.name, fixed_content.encode('utf-8'))
            if was_changed:
                st.success(f"✅ Gecorrigeerd: {uploaded_file.name}")
                success_count += 1
            else:
                st.warning(f"⚠️ Geen wijzigingen nodig: {uploaded_file.name}")

    if success_count > 0:
        zip_buffer.seek(0)
        st.divider()
        st.download_button(
            label=f"📥 Download {success_count} bestanden (ZIP)",
            data=zip_buffer,
            file_name="peppol_minimal_changes.zip",
            mime="application/zip"
        )
