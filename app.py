import streamlit as st
import requests
import pandas as pd
import time
import urllib3

# Schakel waarschuwingen voor onbeveiligde verzoeken uit (nodig voor verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Peppol Validator BE", page_icon="🇧🇪", layout="wide")

def check_single_id(participant_id):
    """
    Controleert een ID met extra robuuste foutafhandeling en 
    negeert SSL-certificaatfouten die vaak 'Netwerk Fout' veroorzaken.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }
    url = f"https://directory.peppol.eu/public/search/1.0/json?participant={participant_id}"
    
    try:
        # verify=False lost vaak de 'Netwerk Fout' op in lokale omgevingen
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("total-result-count", 0)
            return "JA" if count > 0 else "NEE"
        elif response.status_code == 403:
            return "GEBLOKKEERD (403)"
        elif response.status_code == 429:
            return "TE VEEL REQUESTS (429)"
        else:
            return f
