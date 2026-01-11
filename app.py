import streamlit as st
import requests
import pandas as pd
import time
import urllib3

# Onderdruk SSL-waarschuwingen
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Peppol 9925 Checker", page_icon="🇧🇪")

def check_9925_registration(session, vat_number):
    """
    Controleert specifiek op het 9925 (BTW) schema.
    """
    # Opschonen: enkel cijfers overhouden
    clean_nr = "".join(filter(str.isdigit, str(vat_number)))
    if len(clean_nr) == 9:
        clean_nr = "0" + clean_nr
    elif len(clean_nr) > 10:
        clean_nr = clean_nr[-10:]

    if len(clean_nr) != 10:
        return "ONGELDIG FORMAAT"

    # Het volledige Peppol Participant ID voor 9925
    participant_id = f"iso6523-actorid-upis::9925:BE{clean_nr}"
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://directory.peppol.eu/',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # Stap 1: Bezoek eerst de hoofdpagina (indien nieuwe sessie) voor cookies
        if not session.cookies:
            session.get("https://directory.peppol.eu/", timeout=10, verify=False)
            time.sleep(1)

        # Stap 2: De eigenlijke API call
        response = session.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            return "✅ Geregistreerd (9925)" if data.get("total-result-count", 0) > 0 else "❌ Niet gevonden"
        elif response.status_code == 403:
            return "🛑 IP Geblokkeerd (403)"
        else:
            return f"FOUT ({response.status_code})"
    except Exception:
        return "⚠️ Verbindingsfout"

st.title("🇧🇪 Peppol 9925 BTW Checker")
st.markdown("Controleer of Belgische BTW-nummers geregistreerd zijn op het **9925** schema.")

# Upload sectie
uploaded_file = st.file_uploader("Upload CSV of Excel", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python') if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        kolom = st.selectbox("Selecteer de kolom met BTW-nummers", df.columns)
        
        if st.button("Start 9925 Controle"):
            results = []
            nummers = df[kolom].dropna().unique().tolist()
            progress_bar = st.progress(0)
            
            with requests.Session() as session:
                for i, nr in enumerate(nummers):
                    status = check_9925_registration(session, nr)
                    results.append({"Invoer": nr, "9925 Status": status})
                    
                    # Update UI
                    progress_bar.progress((i + 1) / len(nummers))
                    # PAUZE: Zeer belangrijk om blokkades te voorkomen
                    time.sleep(3.0) 

            res_df = pd.DataFrame(results)
            st.subheader("Resultaten")
            st.dataframe(res_df, use_container_width=True)
            
            # Download
            st.download_button("Download Resultaten", res_df.to_csv(index=False).encode('utf-8'), "peppol_9925_check.csv")

    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
