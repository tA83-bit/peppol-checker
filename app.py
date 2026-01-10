import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")
st.title("🔍 Peppol België Validator")

# Functie met 'User-Agent' om blokkades te voorkomen
def call_directory(p_id):
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={p_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("total-result-count", 0) > 0
    except:
        pass
    return False

uploaded_file = st.file_uploader("Upload je bestand", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # Extra robuust inlezen voor afgekapte titels
        if uploaded_file.name.endswith('csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        
        if st.button("Start Analyse"):
            results = []
            progress = st.progress(0)
            data_rijen = df[kolom].dropna().astype(str).tolist()
            
            for i, raw_nr in enumerate(data_rijen):
                # Alleen cijfers overhouden
                clean = "".join(filter(str.isdigit, raw_nr))
                if len(clean) == 9: clean = "0" + clean
                elif len(clean) > 10: clean = clean[-10:]
                
                if len(clean) == 10:
                    # Zoek op beide schema's
                    found_0208 = call_directory(f"iso6523-actorid-upis::0208:{clean}")
                    time.sleep(1) # Veiligheidsmarge
                    found_9925 = call_directory(f"iso6523-actorid-upis::9925:BE{clean}")
                    
                    results.append({
                        "Invoer": raw_nr,
                        "Zoeknr": clean,
                        "0208 (KBO)": "✅" if found_0208 else "❌",
                        "9925 (BTW)": "✅" if found_9925 else "❌",
                        "Advies": "✅ Gebruik 0208" if found_0208 else "⚠️ Enkel 9925" if found_9925 else "❌ Niet gevonden"
                    })
                progress.progress((i + 1) / len(data_rijen))
            
            st.table(pd.DataFrame(results))
    except Exception as e:
        st.error(f"Fout: {e}")
