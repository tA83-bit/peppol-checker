import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

st.title("🔍 Peppol België Prefix Validator")
st.info("Upload 'test_BXL_5.csv' om de automatische correctie te testen.")

uploaded_file = st.file_uploader("Upload je bestand", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Stap 1: Slim inlezen (probeert komma en puntkomma)
        if uploaded_file.name.endswith('csv'):
            try:
                df = pd.read_csv(uploaded_file, sep=';')
                if len(df.columns) <= 1: # Als alles in 1 kolom bleef plakken, probeer komma
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=',')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        kolom = st.selectbox("Selecteer de kolom met btw-nummers", df.columns)
        
        if st.button("Start Analyse"):
            results = []
            progress_bar = st.progress(0)
            rows = df[kolom].dropna().tolist() # Verwijder lege regels
            
            for i, nummer in enumerate(rows):
                # Stap 2: Extreem grondige reiniging
                raw_str = str(nummer).upper()
                schoon_nr = "".join(filter(str.isdigit, raw_str)) # Alleen cijfers overhouden
                
                # Belgische ondernemingsnummers hebben 10 cijfers
                if len(schoon_nr) > 10: schoon_nr = schoon_nr[-10:]
                
                if len(schoon_nr) == 10:
                    # Check 0208 (Zonder BE)
                    r0208 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::0208:{schoon_nr}", timeout=5).json()
                    is_0208 = r0208.get("total-result-count", 0) > 0
                    
                    # Check 9925 (Met BE prefix)
                    r9925 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant=iso6523-actorid-upis::9925:BE{schoon_nr}", timeout=5).json()
                    is_9925 = r9925.get("total-result-count", 0) > 0
                    
                    results.append({
                        "Origineel": nummer,
                        "Zoeknr": schoon_nr,
                        "0208 (KBO)": "✅" if is_0208 else "❌",
                        "9925 (BTW)": "✅" if is_9925 else "❌",
                        "Advies": "✅ OK op 0208" if is_0208 else "⚠️ Pas aan naar 0208" if is_9925 else "❌ Niet op Peppol"
                    })
                
                progress_bar.progress((i + 1) / len(rows))
                time.sleep(0.05)
            
            st.subheader("Resultaten")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df)
            st.download_button("Download resultaten", res_df.to_csv(index=False), "peppol_audit.csv")

    except Exception as e:
        st.error(f"Er ging iets mis met het bestand: {e}")
