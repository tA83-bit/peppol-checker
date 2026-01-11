import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Peppol Link Generator", page_icon="🔗")

def generate_peppol_link(raw_nr):
    # 1. Alleen cijfers behouden
    clean = "".join(filter(str.isdigit, str(raw_nr)))
    
    # 2. Formatteren naar 10 cijfers (Belgisch formaat)
    if len(clean) == 9:
        clean = "0" + clean
    elif len(clean) > 10:
        clean = clean[-10:]
    
    if len(clean) == 10:
        # Dit is de officiële URL structuur voor de Peppol Directory
        # We linken direct naar de zoekresultaten voor het 9925 schema
        participant_id = f"9925:be{clean}"
        return f"https://directory.peppol.eu/public/locale-en_US/menuitem-search?q={participant_id}"
    return "Ongeldig nummer"

st.title("🔗 Peppol 9925 Link Generator")
st.markdown("""
Upload een lijst met BTW-nummers. Dit script maakt voor elk nummer een 
**directe officiële link** naar de Peppol Directory, zodat je blokkades omzeilt.
""")

uploaded_file = st.file_uploader("Kies een CSV of Excel bestand", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # Bestand inlezen
        if uploaded_file.name.endswith('csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
        
        kolom = st.selectbox("Welke kolom bevat de BTW-nummers?", df.columns)
        
        if st.button("Genereer Links"):
            # Maak de nieuwe kolom aan
            df['Peppol_9925_Link'] = df[kolom].apply(generate_peppol_link)
            
            st.success("Links gegenereerd!")
            
            # Toon een preview (klikbare links in Streamlit)
            st.subheader("Preview (eerste 10 regels)")
            st.write(df[[kolom, 'Peppol_9925_Link']].head(10))
            
            # Download knop voor het nieuwe bestand
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Peppol Links')
            
            processed_data = output.getvalue()
            
            st.download_button(
                label="Download verrijkte Excel",
                data=processed_data,
                file_name="peppol_links_resultaat.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Er is een fout opgetreden: {e}")

st.info("Tip: In de gedownloade Excel kun je op de link klikken om direct de status te zien zonder IP-blokkade van het script.")
