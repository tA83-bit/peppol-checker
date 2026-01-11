import streamlit as st
import requests
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪", layout="wide")

# Gebruik caching om dubbele API-calls voor hetzelfde nummer te voorkomen
@st.cache_data(ttl=3600)
def check_single_id(participant_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("total-result-count", 0) > 0
    except requests.exceptions.RequestException:
        return None # Geeft aan dat er een netwerkfout was
    return False

def process_row(raw_nr):
    """Verwerkt een enkel nummer en geeft de resultaten terug."""
    # 1. Opschonen
    clean = "".join(filter(str.isdigit, str(raw_nr)))
    
    # 2. Fix lengte
    if len(clean) == 9:
        clean = "0" + clean
    elif len(clean) > 10:
        clean = clean[-10:]
    
    if len(clean) != 10:
        return {"Invoer": raw_nr, "Zoeknummer": clean, "Status": "Ongeldig formaat", "Advies": "❌ Ongeldig nummer"}

    # 3. Checks (0208 en 9925)
    is_0208 = check_single_id(f"iso6523-actorid-upis::0208:{clean}")
    # Kleine delay om de server te ontzien bij parallelle taken
    time.sleep(0.2) 
    is_9925 = check_single_id(f"iso6523-actorid-upis::9925:BE{clean}")
    
    status_text = "✅ Gebruik 0208" if is_0208 else "⚠️ Enkel 9925 actief" if is_9925 else "❌ Niet gevonden"
    
    return {
        "Invoer": raw_nr,
        "Zoeknummer": clean,
        "0208 (KBO)": "✅" if is_0208 else "❌",
        "9925 (BTW)": "✅" if is_9925 else "❌",
        "Advies": status_text
    }

st.title("🔍 Peppol België Validator")
st.info("Deze tool controleert of nummers geregistreerd zijn via het KBO (0208) of BTW (9925) schema.")

file = st.file_uploader("Upload je CSV of Excel", type=['csv', 'xlsx'])

if file:
    try:
        if file.name.endswith('csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        nummers = df[kolom].dropna().unique().tolist() # Unieke nummers bespaart tijd
        
        if st.button(f"Start controle voor {len(nummers)} unieke nummers"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Gebruik ThreadPoolExecutor voor snellere verwerking (max 3 workers om blokkade te vermijden)
            with ThreadPoolExecutor(max_workers=3) as executor:
                for i, result in enumerate(executor.map(process_row, nummers)):
                    results.append(result)
                    progress = (i + 1) / len(nummers)
                    progress_bar.progress(progress)
                    status_text.text(f"Verwerkt: {i+1}/{len(nummers)}")

            # Resultaten tonen
            res_df = pd.DataFrame(results)
            st.subheader("Resultaten")
            
            # Styling voor de tabel
            st.dataframe(res_df.style.applymap(
                lambda x: 'color: green' if '✅' in str(x) else ('color: red' if '❌' in str(x) else ''),
                subset=['Advies']
            ))
            
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download resultaten als CSV", csv, "peppol_resultaten.csv", "text/csv")
            
    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
