import streamlit as st
import requests
import pandas as pd
import time

st.title("🔍 Peppol België Validator (v3)")

def check_peppol(nummer):
    # 1. Haal alleen de cijfers eruit
    schoon = "".join(filter(str.isdigit, str(nummer)))
    
    # 2. Fix de 'missing zero': Belgische nrs moeten 10 cijfers zijn
    if len(schoon) == 9:
        schoon = "0" + schoon
    elif len(schoon) > 10:
        schoon = schoon[-10:]

    if len(schoon) != 10:
        return "❌ Ongeldig nr", "❌ Ongeldig nr", "Controleer invoer"

    # 3. API Checks
    # Schema 0208: Ondernemingsnummer (ZONDER BE)
    id_0208 = f"iso6523-actorid-upis::0208:{schoon}"
    # Schema 9925: BTW nummer (MET BE)
    id_9925 = f"iso6523-actorid-upis::9925:BE{schoon}"
    
    res_0208 = False
    res_9925 = False
    
    try:
        r1 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant={id_0208}", timeout=5).json()
        res_0208 = r1.get("total-result-count", 0) > 0
        time.sleep(0.2) # Korte pauze tussen checks
        r2 = requests.get(f"https://directory.peppol.eu/public/search/1.0/json?participant={id_9925}", timeout=5).json()
        res_9925 = r2.get("total-result-count", 0) > 0
    except:
        pass

    advies = "✅ OK (Gebruik 0208)" if res_0208 else "⚠️ Gebruik 0208 (enkel 9925 gevonden)" if res_9925 else "❌ Niet op Peppol"
    return "✅" if res_0208 else "❌", "✅" if res_9925 else "❌", advies

uploaded_file = st.file_uploader("Upload test_BXL_5.csv", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=None, engine='python') # sep=None herkent automatisch , of ;
    kolom = st.selectbox("Kolom met nummers", df.columns)
    
    if st.button("Start Controle"):
        results = []
        for n in df[kolom].dropna():
            v0208, v9925, adv = check_peppol(n)
            results.append({"Invoer": n, "0208 (KBO)": v0208, "9925 (BTW)": v9925, "Advies": adv})
            time.sleep(0.3)
        st.table(pd.DataFrame(results))
