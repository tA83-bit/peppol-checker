import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")
st.title("🔍 Peppol België Validator")

def call_directory_with_retry(p_id, retries=3):
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={p_id}"
    for i in range(retries):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json().get("total-result-count", 0) > 0
            elif r.status_code == 429: # Te veel verzoeken
                time.sleep(2) # Wacht 2 seconden en probeer opnieuw
                continue
        except:
            time.sleep(1)
            continue
    return False

uploaded_file = st.file_uploader("Upload je bestand", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        
        if st.button("Start Analyse"):
            results = []
            progress = st.progress(0)
            data_rijen = df[kolom].dropna().astype(str).tolist()
            
            for i, raw_nr in enumerate(data_rijen):
                # Stap 1: Alleen cijfers overhouden
                clean = "".join(filter(str.isdigit, raw_nr))
                
                # Stap 2: Zorg voor 10 cijfers (Belgische standaard)
                if len(clean) == 9:
                    clean = "0" + clean
                elif len(clean) > 10:
                    clean = clean[-10:]
                
                if len(clean) == 10:
                    # Check 0208 (Zonder BE)
                    found_0208 = call_directory_with_retry(f"iso6523-actorid-upis::0208:{clean}")
                    time.sleep(1) # Extra lange pauze tussen deelnemers
                    
                    # Check 9925 (Met BE)
                    found_9925 = call_directory_with_retry(f"iso6523-actorid-upis::9925:BE{clean}")
                    
                    results.append({
                        "Btw-nummer": raw_nr,
                        "0208 (KBO)": "✅" if found_0208 else "❌",
                        "9925 (BTW)": "✅" if found_9925 else "❌",
                        "Status": "✅ OK op 0208" if found_0208 else "⚠️ Gebruik 0208 (enkel 9925)" if found_9925 else "❌ Niet op Peppol"
                    })
                
                progress.progress((i + 1) / len(data_rijen))
            
            st.subheader("Resultaten")
            res_df = pd.DataFrame(results)
            st.dataframe(res_df)
            st.download_button("Download resultaten", res_df.to_csv(index=False), "peppol_rapport.csv")

    except Exception as e:
        st.error(f"Fout bij inlezen: {e}")
