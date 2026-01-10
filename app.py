import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

st.title("🔍 Peppol België Prefix Validator")
st.markdown("""
Deze tool controleert of Belgische klanten geregistreerd zijn op het **0208-schema** (ondernemingsnummer) 
of het **9925-schema** (btw-nummer). Volgens het KB van juli 2025 is 0208 de verplichte standaard.
""")

uploaded_file = st.file_uploader("Upload je Excel of CSV met btw-nummers", type=['xlsx', 'csv'])

if uploaded_file:
    # Inlezen van het bestand
    if uploaded_file.name.endswith('xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
        
    kolom = st.selectbox("In welke kolom staan de btw-nummers?", df.columns)
    
    if st.button("Start Controle"):
        results = []
        progress = st.progress(0)
        n_rows = len(df)
        
        for i, nummer in enumerate(df[kolom]):
            # Schoon het nummer op: alleen de 10 cijfers
            schoon_nr = ''.join(filter(str.isdigit, str(nummer)))
            if len(schoon_nr) > 10: schoon_nr = schoon_nr[-10:]
            
            if len(schoon_nr) == 10:
                # Check 0208 via Peppol Directory API
                try:
                    r0208 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::0208:{schoon_nr}", timeout=5).json()
                    is_0208 = r0208.get("total-result-count", 0) > 0
                    
                    r9925 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::9925:BE{schoon_nr}", timeout=5).json()
                    is_9925 = r9925.get("total-result-count", 0) > 0
                    
                    advies = "✅ OK (Gebruik 0208)" if is_0208 else "⚠️ Gebruik 0208 (enkel 9925 gevonden)" if is_9925 else "❌ Niet op Peppol"
                    
                    results.append({
                        "Invoer": nummer,
                        "0208 (KBO)": "✅" if is_0208 else "❌",
                        "9925 (BTW)": "✅" if is_9925 else "❌",
                        "Status": advies
                    })
                except:
                    results.append({"Invoer": nummer, "Status": "Fout bij check"})
            
            progress.progress((i + 1) / n_rows)
            time.sleep(0.1) # Netjes blijven tegenover de API
            
        st.subheader("Resultaten")
        res_df = pd.DataFrame(results)
        st.dataframe(res_df)
        st.download_button("Download resultaten", res_df.to_csv(index=False), "peppol_check.csv")
