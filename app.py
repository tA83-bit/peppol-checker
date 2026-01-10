import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

def check_single_id(participant_id):
    # Deze headers zijn essentieel om niet geblokkeerd te worden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("total-result-count", 0) > 0
    except:
        pass
    return False

st.title("🔍 Peppol België Validator")
st.markdown("Deze tool is geoptimaliseerd voor Belgische KBO- en BTW-prefixen.")

file = st.file_uploader("Upload je CSV of Excel", type=['csv', 'xlsx'])

if file:
    # Bestand inlezen (herkent automatisch scheidingstekens)
    if file.name.endswith('csv'):
        df = pd.read_csv(file, sep=None, engine='python')
    else:
        df = pd.read_excel(file)
    
    # Gebruiker kiest de kolom (bijv. 'btw-nummer' of 'btw-nu')
    kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
    
    if st.button("Start de controle"):
        results = []
        progress_bar = st.progress(0)
        nummers = df[kolom].dropna().astype(str).tolist()
        
        for i, raw_nr in enumerate(nummers):
            # 1. Opschonen naar pure cijfers
            clean = "".join(filter(str.isdigit, raw_nr))
            
            # 2. Fix 9-cijferige nummers (voeg 0 toe)
            if len(clean) == 9:
                clean = "0" + clean
            elif len(clean) > 10:
                clean = clean[-10:]
            
            if len(clean) == 10:
                # 3. Voer de checks uit
                # Schema 0208 (KBO) = ZONDER BE
                is_0208 = check_single_id(f"iso6523-actorid-upis::0208:{clean}")
                time.sleep(0.7) # Essentieel: voorkom blokkade
                
                # Schema 9925 (BTW) = MET BE
                is_9925 = check_single_id(f"iso6523-actorid-upis::9925:BE{clean}")
                
                results.append({
                    "Origineel": raw_nr,
                    "Gezien als": clean,
                    "0208 (KBO)": "✅" if is_0208 else "❌",
                    "9925 (BTW)": "✅" if is_9925 else "❌",
                    "Status": "✅ OK op 0208" if is_0208 else "⚠️ Enkel 9925" if is_9925 else "❌ Niet gevonden"
                })
            
            progress_bar.progress((i + 1) / len(nummers))
            time.sleep(0.3)
        
        # Toon resultaat
        res_df = pd.DataFrame(results)
        st.subheader("Resultaten")
        st.table(res_df)
        st.download_button("Download als CSV", res_df.to_csv(index=False), "peppol_rapport.csv")
