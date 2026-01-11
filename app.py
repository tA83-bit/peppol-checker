import streamlit as st
import requests
import pandas as pd
import time
import urllib3

# Schakel SSL-waarschuwingen uit voor de verify=False optie
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪", layout="wide")

def check_single_id(participant_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    
    try:
        # verify=False helpt bij netwerkblokkades/certificaatfouten
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("total-result-count", 0)
            return "JA" if count > 0 else "NEE"
        elif response.status_code == 403:
            return "GEBLOKKEERD (403)"
        else:
            return f"FOUT ({response.status_code})"
            
    except requests.exceptions.SSLError:
        return "SSL FOUT"
    except requests.exceptions.ConnectionError:
        return "GEEN VERBINDING"
    except Exception as e:
        return f"ERROR: {type(e).__name__}"

st.title("🔍 Peppol België Validator")

file = st.file_uploader("Upload je CSV of Excel", type=['csv', 'xlsx'])

if file:
    try:
        if file.name.endswith('csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        
        if st.button("Start de controle"):
            results = []
            nummers = df[kolom].dropna().unique().tolist()
            progress_bar = st.progress(0)
            
            for i, raw_nr in enumerate(nummers):
                # Nummer opschonen (alleen cijfers overhouden)
                clean = "".join(filter(str.isdigit, str(raw_nr)))
                
                # Formatteren naar 10 cijfers (bijv. 0879641233)
                if len(clean) == 9:
                    clean = "0" + clean
                elif len(clean) > 10:
                    clean = clean[-10:]
                
                if len(clean) == 10:
                    # Controleer beide Belgische schema's
                    res_0208 = check_single_id(f"iso6523-actorid-upis::0208:{clean}")
                    time.sleep(0.5)
                    res_9925 = check_single_id(f"iso6523-actorid-upis::9925:BE{clean}")
                    
                    # Bepaal het advies op basis van de resultaten
                    if res_0208 == "JA":
                        advies = "✅ Gebruik 0208"
                    elif res_9925 == "JA":
                        advies = "⚠️ Enkel 9925 actief"
                    else:
                        advies = "❌ Niet gevonden"

                    results.append({
                        "Invoer": raw_nr,
                        "Zoeknummer": clean,
                        "KBO (0208)": res_0208,
                        "BTW (9925)": res_9925,
                        "Advies": advies
                    })
                
                progress_bar.progress((i + 1) / len(nummers))
                time.sleep(0.5)

            # Toon de tabel met resultaten
            res_df = pd.DataFrame(results)
            st.subheader("Resultaten")
            st.dataframe(res_df, use_container_width=True)
            
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download resultaten als CSV", csv, "peppol_check.csv", "text/csv")
            
    except Exception as e:
        st.error(f"Fout bij verwerken bestand: {e}")
