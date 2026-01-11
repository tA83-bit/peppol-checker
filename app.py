import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Peppol Link Generator BE", page_icon="🔗")

def get_peppol_url(raw_nr, scheme="9925"):
    """Genereert de officiële URL voor de Peppol Directory."""
    clean = "".join(filter(str.isdigit, str(raw_nr)))
    
    if len(clean) == 9:
        clean = "0" + clean
    elif len(clean) > 10:
        clean = clean[-10:]
    
    if len(clean) == 10:
        # 9925 gebruikt vaak 'be' prefix, 0208 meestal niet in de zoekopdracht
        prefix = "be" if scheme == "9925" else ""
        query = f"{scheme}:{prefix}{clean}"
        return f"https://directory.peppol.eu/public/locale-en_US/menuitem-search?q={query}"
    return "Ongeldig nummer"

st.title("🔗 Peppol België Link Generator")
st.markdown("""
Dit script maakt direct klikbare links naar de officiële **Peppol Directory**. 
Zo hoef je niet bang te zijn voor IP-blokkades, omdat je de status live in je browser bekijkt.
""")

file = st.file_uploader("Upload je lijst (CSV of Excel)", type=['csv', 'xlsx'])

if file:
    try:
        if file.name.endswith('csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
        
        kolom = st.selectbox("Welke kolom bevat de nummers?", df.columns)
        
        if st.button("Genereer Officiële Links"):
            # Genereer links voor beide schema's
            df['Link_BTW_9925'] = df[kolom].apply(lambda x: get_peppol_url(x, "9925"))
            df['Link_KBO_0208'] = df[kolom].apply(lambda x: get_peppol_url(x, "0208"))
            
            st.success("Links succesvol aangemaakt!")
            st.dataframe(df[[kolom, 'Link_BTW_9925', 'Link_KBO_0208']].head(10))
            
            # Excel export (zonder de noodzaak voor xlsxwriter als je engine='openpyxl' gebruikt)
            output = io.BytesIO()
            df.to_excel(output, index=False) # Gebruikt standaard engine
            
            st.download_button(
                label="Download Resultaten als Excel",
                data=output.getvalue(),
                file_name="peppol_status_links.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Fout: {e}")
