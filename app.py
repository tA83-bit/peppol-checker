import streamlit as st
import requests
import pandas as pd
import time

# Pagina-instellingen
st.set_page_config(page_title="Peppol Validator", page_icon="🇧🇪")

def check_peppol(nummer):
    # Alleen cijfers overhouden
    clean = "".join(filter(str.isdigit, str(nummer)))
    if len(clean) == 9: clean = "0" + clean
    elif len(clean) > 10: clean = clean[-10:]
    
    if len(clean) != 10:
        return "❌ Ongeldig", "❌ Ongeldig", "Check formaat"

    results = {"0208": "❌", "9925": "❌"}
    
    # We proberen de officiële Directory met een browser-identiteit
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}
    
    ids = {
        "0208": f"iso6523-actorid-upis::0208:{clean}",
        "9925": f"iso6523-actorid-upis::9925:BE{clean}"
    }

    for schema, p_id in ids.items():
        try:
            url = f"https://directory.peppol.eu/public/search/1.0/json?participant={p_id}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                if r.json().get("total-result-count", 0) > 0:
                    results[schema] = "✅"
            time.sleep(1) # Essentiële pauze tegen blokkades
        except:
            continue
            
    advies = "✅ OK op 0208" if results["0208"] == "✅" else "⚠️ Gebruik 0208 (enkel 9925 gevonden)" if results["9925"] == "✅" else "❌ Niet gevonden"
    return results["0208"], results["9925"], advies

st.title("🔍 Definitieve Peppol Validator")

file = st.file_uploader("Upload je bestand", type=['csv', 'xlsx'])

if file:
    # Inlezen van het bestand
    if file.name.endswith('csv'):
        df = pd.read_csv(file, sep=None, engine='python')
    else:
        df = pd.read_excel(file)
    
    kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
    
    if st.button("Start de check"):
        output = []
        bar = st.progress(0)
        rijen = df[kolom].dropna().tolist()
        
        for i, nr in enumerate(rijen):
            v0208, v9925, adv = check_peppol(nr)
            output.append({
                "Invoer": nr,
                "0208 (KBO)": v0208,
                "9925 (BTW)": v9925,
                "Actie": adv
            })
            bar.progress((i + 1) / len(rijen))
        
        res_df = pd.DataFrame(output)
        st.table(res_df)
        st.download_button("Download resultaat", res_df.to_csv(index=False), "peppol_check.csv")
