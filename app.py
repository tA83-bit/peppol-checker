import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

st.title("🔍 Peppol België Prefix Validator")
st.markdown("Deze tool stript automatisch 'BE', punten en spaties voor een correcte controle.")

uploaded_file = st.file_uploader("Upload je Excel of CSV", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
    kolom = st.selectbox("In welke kolom staan de nummers?", df.columns)
    
    if st.button("Start Controle"):
        results = []
        progress = st.progress(0)
        
        for i, nummer in enumerate(df[kolom]):
            # STAP 1: Schoon het nummer op (verwijder BE, punten, spaties)
            schoon_nr = str(nummer).upper().replace('BE', '').replace('.', '').replace(' ', '').strip()
            
            # Zorg dat we exact 10 cijfers hebben (voor Belgische ondernemingsnummers)
            if len(schoon_nr) > 10: schoon_nr = schoon_nr[-10:]
            
            if len(schoon_nr) == 10:
                # Check 0208 (ZONDER BE)
                url_0208 = f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::0208:{schoon_nr}"
                is_0208 = requests.get(url_0208).json().get("total-result-count", 0) > 0
                
                # Check 9925 (MET BE - dit schema vereist de landcode vaak wel)
                url_9925 = f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::9925:BE{schoon_nr}"
                is_9925 = requests.get(url_9925).json().get("total-result-count", 0) > 0
                
                status = "✅ Gebruik 0208" if is_0208 else "⚠️ Enkel 9925 actief" if is_9925 else "❌ Niet gevonden"
                
                results.append({
                    "Invoer": nummer,
                    "Gecheckt als": schoon_nr,
                    "0208 (KBO)": "✅" if is_0208 else "❌",
                    "9925 (BTW)": "✅" if is_9925 else "❌",
                    "Advies": status
                })
            progress.progress((i + 1) / len(df))
            time.sleep(0.1)
            
        st.dataframe(pd.DataFrame(results))
