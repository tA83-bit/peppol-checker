import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

def check_single_id(participant_id):
    # Een meer realistische browser header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://directory.peppol.eu/'
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 403:
            return "GEBLOKKEERD (403)"
        elif response.status_code == 429:
            return "RATE LIMIT (429)"
        elif response.status_code == 200:
            count = response.json().get("total-result-count", 0)
            return "JA" if count > 0 else "NEE"
        else:
            return f"FOUT ({response.status_code})"
    except Exception as e:
        return f"NETWERK FOUT"

st.title("🔍 Peppol België Validator (Debug Versie)")
st.info("Deze versie laat zien waarom een nummer eventueel niet gevonden wordt.")

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
            nummers = df[kolom].dropna().astype(str).tolist()
            progress_bar = st.progress(0)
            
            for i, raw_nr in enumerate(nummers):
                # Opschonen
                clean = "".join(filter(str.isdigit, raw_nr))
                if len(clean) == 9: clean = "0" + clean
                if len(clean) > 10: clean = clean[-10:]
                
                if len(clean) == 10:
                    # Check beide schemas
                    res_0208 = check_single_id(f"iso6523-actorid-upis::0208:{clean}")
                    time.sleep(1.2) # Iets langere pauze voor veiligheid
                    
                    res_9925 = check_single_id(f"iso6523-actorid-upis::9925:BE{clean}")
                    
                    # Logica voor advies
                    if res_0208 == "JA":
                        advies = "✅ Gebruik 0208"
                    elif res_9925 == "JA":
                        advies = "⚠️ Enkel 9925 actief"
                    elif "GEBLOKKEERD" in str(res_0208) or "RATE" in str(res_0208):
                        advies = "🛑 Server blokkeert aanvraag"
                    else:
                        advies = "❌ Niet gevonden"

                    results.append({
                        "Invoer": raw_nr,
                        "KBO (0208)": res_0208,
                        "BTW (9925)": res_9925,
                        "Advies": advies
                    })
                
                progress_bar.progress((i + 1) / len(nummers))
                time.sleep(0.5)

            res_df = pd.DataFrame(results)
            st.table(res_df)
            
    except Exception as e:
        st.error(f"Fout: {e}")
