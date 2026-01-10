import streamlit as st
import requests
import pandas as pd
import time

# 1. Pagina instellingen (MOET bovenaan staan)
st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

def call_directory(p_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={p_id}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("total-result-count", 0) > 0
    except:
        pass
    return False

# 2. De Titels
st.title("🔍 Peppol België Validator")
st.write("Controleer of Belgische bedrijven geregistreerd zijn op het 0208 (KBO) of 9925 (BTW) schema.")

# 3. Bestand uploaden (Slechts één keer in de code!)
uploaded_file = st.file_uploader("Stap 1: Upload je bestand (CSV of Excel)", type=['csv', 'xlsx'], key="unique_uploader_1")

if uploaded_file:
    try:
        # Bestand inlezen
        if uploaded_file.name.endswith('csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Kolom selecteren
        kolom = st.selectbox("Stap 2: Kies de kolom met nummers", df.columns)
        
        if st.button("Stap 3: Start Analyse"):
            results = []
            progress = st.progress(0)
            data_rijen = df[kolom].dropna().astype(str).tolist()
            
            for i, raw_nr in enumerate(data_rijen):
                # Opschonen: alleen cijfers
                clean = "".join(filter(str.isdigit, raw_nr))
                if len(clean) == 9: clean = "0" + clean
                elif len(clean) > 10: clean = clean[-10:]
                
                if len(clean) == 10:
                    # Zoek op beide schema's
                    found_0208 = call_directory(f"iso6523-actorid-upis::0208:{clean}")
                    time.sleep(0.5)
                    found_9925 = call_directory(f"iso6523-actorid-upis::9925:BE{clean}")
                    
                    results.append({
                        "Invoer": raw_nr,
                        "KBO_Nummer": clean,
                        "0208 (KBO)": "✅" if found_0208 else "❌",
                        "9925 (BTW)": "✅" if found_9925 else "❌",
                        "Advies": "✅ OK op 0208" if found_0208 else "⚠️ Gebruik 0208 (nu enkel 9925)" if found_9925 else "❌ Niet op Peppol"
                    })
                progress.progress((i + 1) / len(data_rijen))
            
            # Toon tabel
            res_df = pd.DataFrame(results)
            st.table(res_df)
            st.download_button("Download resultaten", res_df.to_csv(index=False), "peppol_resultaat.csv")

    except Exception as e:
        st.error(f"Fout bij verwerking: {e}")
