import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪")

st.title("🔍 Peppol België Prefix Validator")
st.info("Deze versie is extra beveiligd tegen API-fouten.")

uploaded_file = st.file_uploader("Upload je bestand (CSV of Excel)", type=['xlsx', 'csv'])

def call_peppol_api(participant_id):
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    try:
        response = requests.get(url, timeout=10)
        # Controleer of de statuscode 200 (OK) is
        if response.status_code == 200:
            data = response.json()
            return data.get("total-result-count", 0) > 0
        return False
    except:
        return False

if uploaded_file:
    try:
        if uploaded_file.name.endswith('csv'):
            # Probeer verschillende scheidingstekens voor CSV
            try:
                df = pd.read_csv(uploaded_file, sep=';')
                if len(df.columns) <= 1:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=',')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        kolom = st.selectbox("Welke kolom bevat de btw-nummers?", df.columns)
        
        if st.button("Start Analyse"):
            results = []
            progress_bar = st.progress(0)
            # Haal nummers op en verwijder lege cellen
            rows = df[kolom].dropna().astype(str).tolist()
            
            for i, nummer in enumerate(rows):
                # Reinig het nummer: hou alleen cijfers over
                schoon_nr = "".join(filter(str.isdigit, nummer))
                if len(schoon_nr) > 10: schoon_nr = schoon_nr[-10:]
                
                if len(schoon_nr) == 10:
                    # Check 0208 (Standaard ondernemingsnummer)
                    is_0208 = call_peppol_api(f"iso6523-actorid-upis::0208:{schoon_nr}")
                    
                    # Check 9925 (Btw-nummer)
                    is_9925 = call_peppol_api(f"iso6523-actorid-upis::9925:BE{schoon_nr}")
                    
                    advies = "✅ OK op 0208" if is_0208 else "⚠️ Gebruik 0208 (enkel 9925 gevonden)" if is_9925 else "❌ Niet op Peppol"
                    
                    results.append({
                        "Invoer": nummer,
                        "Nummer_Puur": schoon_nr,
                        "0208 (KBO)": "✅" if is_0208 else "❌",
                        "9925 (BTW)": "✅" if is_9925 else "❌",
                        "Actie": advies
                    })
                
                progress_bar.progress((i + 1) / len(rows))
                time.sleep(0.2) # Iets langere pauze om de API niet te overbelasten
            
            if results:
                st.subheader("Resultaten")
                res_df = pd.DataFrame(results)
                st.dataframe(res_df)
                st.download_button("Download Excel Resultaat", res_df.to_csv(index=False), "peppol_controle.csv")
            else:
                st.warning("Geen geldige 10-cijferige nummers gevonden in de geselecteerde kolom.")

    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
