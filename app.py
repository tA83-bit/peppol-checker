import streamlit as st
import requests
import pandas as pd
import time
import urllib3

# Onderdruk SSL waarschuwingen voor stabiliteit
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪", layout="wide")

def check_single_id(session, participant_id):
    """
    Gebruikt een requests.Session voor betere stabiliteit en 
    foutafhandeling voor niet-JSON antwoorden.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://directory.peppol.eu/'
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    
    try:
        # We gebruiken de sessie in plaats van losse requests
        response = session.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            try:
                data = response.json()
                count = data.get("total-result-count", 0)
                return "JA" if count > 0 else "NEE"
            except ValueError:
                return "BLOKKADE (Geen JSON)"
        elif response.status_code == 403:
            return "GEBLOKKEERD (403)"
        elif response.status_code == 429:
            return "RATE LIMIT (429)"
        else:
            return f"FOUT ({response.status_code})"
            
    except Exception as e:
        return f"VERBINDING FOUT"

st.title("🔍 Peppol België Validator (Anti-Blokkeer Modus)")
st.markdown("Deze versie gebruikt sessies en langere pauzes om de `JSONDecodeError` te vermijden.")

file = st.file_uploader("Upload je CSV of Excel", type=['csv', 'xlsx'])

if file:
    try:
        if file.name.endswith('csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        
        if st.button("Start de veilige controle"):
            results = []
            nummers = df[kolom].dropna().unique().tolist()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Maak één sessie aan voor de hele loop
            with requests.Session() as session:
                for i, raw_nr in enumerate(nummers):
                    # Opschonen en formatteren
                    clean = "".join(filter(str.isdigit, str(raw_nr)))
                    if len(clean) == 9: clean = "0" + clean
                    elif len(clean) > 10: clean = clean[-10:]
                    
                    if len(clean) == 10:
                        status_text.text(f"Verwerken ({i+1}/{len(nummers)}): {clean}...")
                        
                        # Check KBO (0208)
                        res_0208 = check_single_id(session, f"iso6523-actorid-upis::0208:{clean}")
                        
                        # Extra lange pauze tussen de twee checks voor hetzelfde bedrijf
                        time.sleep(1.5) 
                        
                        # Check BTW (9925)
                        res_9925 = check_single_id(session, f"iso6523-actorid-upis::9925:BE{clean}")
                        
                        # Advies bepalen
                        if res_0208 == "JA":
                            advies = "✅ Gebruik 0208"
                        elif res_9925 == "JA":
                            advies = "⚠️ Enkel 9925 actief"
                        elif "BLOKKADE" in str(res_0208) or "403" in str(res_0208):
                            advies = "🛑 Server blokkeert je IP"
                        else:
                            advies = "❌ Niet gevonden"

                        results.append({
                            "Invoer": raw_nr,
                            "KBO (0208)": res_0208,
                            "BTW (9925)": res_9925,
                            "Advies": advies
                        })
                    
                    # Update voortgang
                    progress_bar.progress((i + 1) / len(nummers))
                    
                    # Belangrijk: Pauze tussen verschillende bedrijven
                    time.sleep(2.0)

            # Resultaten tonen
            res_df = pd.DataFrame(results)
            st.subheader("Resultaten")
            st.dataframe(res_df, use_container_width=True)
            
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download resultaten", csv, "peppol_veilig.csv", "text/csv")
            
    except Exception as e:
        st.error(f"Fout: {e}")
