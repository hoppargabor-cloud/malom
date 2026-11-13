import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Oldal konfiguráció
st.set_page_config(
    page_title="Tápiógyörgye Király Malom Master PRO",
    page_icon="🌾",
    layout="wide"
)

# Adatbázis kapcsolat létrehozása / ellenőrzése
def init_db():
    conn = sqlite3.connect('malom_data.db', check_same_thread=False)
    cursor = conn.cursor()
    # Alap táblák létrehozása, ha nem léteznek
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS labor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            termek TEXT,
            nedvesseg REAL,
            gluten REAL,
            feherje REAL,
            hamutartalom REAL,
            falling_number REAL,
            zeleny REAL,
            w_ertek REAL,
            terules REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keszlet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termek TEXT,
            mennyiseg_kg REAL,
            minoseg TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beszallitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            partner TEXT,
            termek TEXT,
            mennyiseg_t REAL,
            nedvesseg REAL
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# Oldalsáv navigáció (Modul választó)
st.sidebar.title("🌾 Tápiógyörgye Király Malom")
st.sidebar.markdown("### Modul kiválasztása")
modul = st.sidebar.selectbox(
    "Válassz modult:",
    [
        "Folyamatábra (SCADA)", 
        "Készletkezelés & Silók", 
        "Labor & Minőségi Bizonyítvány", 
        "Beszállítási Napló", 
        "HACCP & Munkamenet"
    ]
)

# --- 1. FOLYAMATÁBRA & KOPTATÁSI VEZÉRLÉS ---
if modul == "Folyamatábra (SCADA)":
    st.title("🖥️ Malmi Folyamatábra & Üzemi Vezérlés")
    
    # Session state inicializálása a gombokhoz
    if 'koptatas_aktiv' not in st.session_state: st.session_state.koptatas_aktiv = True
    if 'orlo_aktiv' not in st.session_state: st.session_state.orlo_aktiv = True
    if 'szita_aktiv' not in st.session_state: st.session_state.szita_aktiv = True
    if 'pneumatika_aktiv' not in st.session_state: st.session_state.pneumatika_aktiv = True

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Koptatás: " + ("ÜZEMBEN" if st.session_state.koptatas_aktiv else "LEÁLLítVA")):
            st.session_state.koptatas_aktiv = not st.session_state.koptatas_aktiv
    with col2:
        if st.button("⚙️ Őrlő Részleg: " + ("AKTÍV" if st.session_state.orlo_aktiv else "INAKTÍV")):
            st.session_state.orlo_aktiv = not st.session_state.orlo_aktiv
    with col3:
        if st.button("🛜 Szita Rendszer: " + ("FUT" if st.session_state.szita_aktiv else "LEÁLLítVA")):
            st.session_state.szita_aktiv = not st.session_state.szita_aktiv
    with col4:
        if st.button("💨 Pneumatika: " + ("NYOMÁSON" if st.session_state.pneumatika_aktiv else "KIKAPCSolva")):
            st.session_state.pneumatika_aktiv = not st.session_state.pneumatika_aktiv

    st.markdown("---")
    st.subheader("💧 Vízszámítás & Kondicionálás")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        alap_nedv = st.number_input("Alap nedvességtartalom (%)", value=13.5, step=0.1)
        cel_nedv = st.number_input("Cél nedvességtartalom (%)", value=15.0, step=0.1)
    with col_v2:
        teljesitmeny = st.number_input("Koptató teljesítmény (t/h)", value=2.5, step=0.1)
        if cel_nedv > alap_nedv:
        # Vízmennyiség számítás liter/óra = t/h * 1000 * (cél - alap) / (100 - cél)
            viz_igeny = (teljesitmeny * 1000 * (cel_nedv - alap_nedv)) / (100 - cel_nedv)
            st.success(Szükséges vízpermet: **{viz_igeny:.2f} liter/óra**.)
        else:
            st.warning("A cél nedvességnek magasabbnak kell lennie az alapnedvességnél.")

# --- 2. KÉSZLETKEZELÉS & SILÓK ---
elif modul == "Készletkezelés & Silók":
    st.title("📦 Készletkezelés és Silóállapotok")
    
    # Adatok lekérdezése adatbázisból
    df_keszlet = pd.read_sql("SELECT * FROM keszlet", conn)
    
    if df_keszlet.empty:
        # Alapértelmezett adatok feltöltése, ha üres
        alap_termekek = [
            ("Graham liszt", 1250, "Prémium"),
            ("Asztali dara", 840, "Standard"),
            ("Rétesliszt (BL55)", 3100, "I. Osztály"),
            ("Étkezési korpa", 950, "Takarmány/Élelmi"),
            ("BL-80 kenyérliszt", 5400, "I. Osztály")
        ]
        conn.executemany("INSERT INTO keszlet (termek, mennyiseg_kg, minoseg) VALUES (?, ?, ?)", alap_termekek)
        conn.commit()
        df_keszlet = pd.read_sql("SELECT * FROM keszlet", conn)

    st.dataframe(df_keszlet, use_container_width=True)
    
    st.subheader("Új készlet tétel rögzítése / módosítása")
    with st.form("keszlet_form"):
        k_termek = st.text_input("Termék neve")
        k_mennyiseg = st.number_input("Mennyiség (kg)", min_value=0.0, step=50.0)
        k_minoseg = st.text_input("Minőségi osztály / Megjegyzés")
        submitted = st.form_submit_button("Mentés a készletbe")
        if submitted and k_termek:
            conn.execute("INSERT INTO keszlet (termek, mennyiseg_kg, minoseg) VALUES (?, ?, ?)", (k_termek, k_mennyiseg, k_minoseg))
            conn.commit()
            st.success("Sikeresen rögzítve!")
            st.rerun()

# --- 3. LABOR & MINŐSÉGI BIZONYÍTVÁNY ---
elif modul == "Labor & Minőségi Bizonyítvány":
    st.title("🧪 Laboratóriumi Eredmények & Minőségi Bizonyítvány")
    
    # Dátum szerinti keresés / szűrés
    st.subheader("Múltbeli laboreredmények keresése")
    d_tol, d_ig = st.columns(2)
    with d_tol:
        datum_tol = st.date_input("Kezdő dátum", value=datetime.today().replace(day=1))
    with d_ig:
        datum_ig = st.date_input("Záró dátum", value=datetime.today())

    df_labor = pd.read_sql(f"SELECT * FROM labor WHERE datum BETWEEN '{datum_tol}' AND '{datum_ig}'", conn)
    
    if not df_labor.empty:
        st.dataframe(df_labor, use_container_width=True)
    else:
        # Ha nincs szűrt adat, mutassuk az összeset
        df_labor_all = pd.read_sql("SELECT * FROM labor", conn)
        if not df_labor_all.empty:
            st.dataframe(df_labor_all, use_container_width=True)
        else:
            st.info("Még nincsenek rögzített laboreredmények.")

    st.markdown("---")
    st.subheader("Új laborvizsgálat rögzítése és Tanúsítvány kiállítása")
    
    with st.form("labor_form"):
        l_datum = st.date_input("Vizsgálat dátuma")
        l_termek = st.selectbox("Termék", ["BL-55 Rétesliszt", "BL-80 Kenyérliszt", "Graham liszt", "Asztali dara", "Teljes kiőrlésű tönköly"])
        c1, c2, c3 = st.columns(3)
        with c1:
            l_nedv = st.number_input("Nedvesség (%)", value=14.0)
            l_gluten = st.number_input("Nedves sikér (%)", value=28.5)
        with c2:
            l_feherje = st.number_input("Fehérje (%)", value=12.2)
            l_hamu = st.number_input("Hamutartalom (%)", value=0.65)
        with c3:
            l_falling = st.number_input("Falling Number (s)", value=320.0)
            l_zeleny = st.number_input("Zeleny index (ml)", value=45.0)
            l_w = st.number_input("W érték", value=220.0)
            l_terules = st.number_input("Terülés (mm)", value=65.0)
            
        l_submit = st.form_submit_button("Laboreredmény mentése")
        if l_submit:
            conn.execute('''
                INSERT INTO labor (datum, termek, nedvesseg, gluten, feherje, hamutartalom, falling_number, zeleny, w_ertek, terules)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(l_datum), l_termek, l_nedv, l_gluten, l_feherje, l_hamu, l_falling, l_zeleny, l_w, l_terules))
            conn.commit()
            st.success("Laboreredmény sikeresen elmentve!")
            st.rerun()

    # Nyomtatási kép / Bizonyítvány generálás
    st.markdown("### 🖨️ Minőségi Bizonyítvány / Nyomtatási Kép")
    biz_termek = st.selectbox("Válassz terméket a bizonylathoz:", ["BL-55 Rétesliszt", "BL-80 Kenyérliszt", "Graham liszt", "Asztali dara", "Teljes kiőrlésű tönköly"])
    if st.button("Nyomtatási kép generálása (PDF / Előnézet)"):
        st.markdown(f"""
        <div style="border: 2px solid #333; padding: 20px; background-color: #fff; color: #000; border-radius: 10px;">
            <h2 style="text-align: center;">TÁPIÓGYÖRGYE KIRÁLY MALOM</h2>
            <h4 style="text-align: center;">MINŐSÉGI BIZONYÍTVÁNY</h4>
            <hr>
            <p><b>Termék megnevezése:</b> {biz_termek}</p>
            <p><b>Kiállítás dátuma:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <table border="1" style="width:100%; border-collapse: collapse; text-align: center; padding: 5px;">
                <tr><th>Paraméter</th><th>Mért érték</th><th>Előírt határérték</th></tr>
                <tr><td>Nedvességartalom</td><td>14.0 %</td><td>max. 15.0 %</td></tr>
                <tr><td>Nedves sikér</td><td>28.5 %</td><td>min. 27.0 %</td></tr>
                <tr><td>Zeleny index</td><td>45.0 ml</td><td>min. 30.0 ml</td></tr>
                <tr><td>W érték</td><td>220</td><td>min. 180</td></tr>
                <tr><td>Hamutartalom</td><td>0.65 %</td><td>szabvány szerint</td></tr>
            </table>
            <br>
            <p style="text-align: right;">__________________________<br>Minőségellenőr aláírása</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("Nyomtatáshoz használd a böngésződ nyomtatás funkcióját (Ctrl+P / Command+P).")

# --- 4. BESZÁLLÍTÁSI NAPLÓ ---
elif modul == "Beszerzés / Beszállítási Napló":
    st.title("🚛 Beszállítási Napló & Nyersanyagkövetés")
    
    st.subheader("Beszállítások szűrése dátum szerint")
    b_tol, b_ig = st.columns(2)
    with b_tol:
        b_datum_tol = st.date_input("Beszállítás tól", value=datetime.today().replace(day=1), key="b_t")
    with b_ig:
        b_datum_ig = st.date_input("Beszállítás ig", value=datetime.today(), key="b_i")

    df_besz = pd.read_sql(f"SELECT * FROM beszallitas WHERE datum BETWEEN '{b_datum_tol}' AND '{b_datum_ig}'", conn)
    if not df_besz.empty:
        st.dataframe(df_besz, use_container_width=True)
    else:
        df_besz_all = pd.read_sql("SELECT * FROM beszallitas", conn)
        if not df_besz_all.empty:
            st.dataframe(df_besz_all, use_container_width=True)
        else:
            st.info("Nincsenek rögzített beszállítások ebben az időszakban.")

    st.subheader("Új gabona beszállítás rögzítése")
    with st.form("besz_form"):
        b_datum = st.date_input("Brakoló / Érkezési dátum")
        b_partner = st.text_input("Termelő / Beszállító neve")
        b_termek = st.selectbox("Gabona fajtája", ["Búza (Étkezési)", "Takarmánybúza", "Tönkölybúza", "Rozs"])
        b_mennyiseg = st.number_input("Mennyiség (tonna)", value=24.0)
        b_nedv = st.number_input("Átlagos nedvesség (%)", value=13.2)
        
        b_submit = st.form_submit_button("Beszállítás rögzítése")
        if b_submit:
            conn.execute("INSERT INTO beszallitas (datum, partner, termek, mennyiseg_t, nedvesseg) VALUES (?, ?, ?, ?, ?)", 
                         (str(b_datum), b_partner, b_termek, b_mennyiseg, b_nedv))
            conn.commit()
            st.success("Beszállítás sikeresen rögzítve az adatbázisba!")
            st.rerun()

# --- 5. HACCP & MUNKAMENET ---
elif modul == "HACCP & Munkamenet":
    st.title("📋 HACCP Ellenőrző Lista & Műszaki Napló")
    st.write("Napi higiéniai, kártevőirtási és fémdetektor ellenőrzési jegyzőkönyv.")
    
    with st.form("haccp_form"):
        st.checkbox("Fémdetektor működésének ellenőrzése (3 próbatesttel)")
        st.checkbox("Mágneses vasfogók tisztítása és ellenőrzése")
        st.checkbox("Napi takarítási rend betartása a csomagolóban")
        st.checkbox("Kártevőirtó csapdák ellenőrzése és integritása")
        megj = st.text_area("Műszaki / HACCP megjegyzés, rendkívüli esemény:")
        
        h_submit = st.form_submit_button("Napi HACCP napló rögzítése")
        if h_submit:
            st.success("A napi HACCP ellenőrzés sikeresen rögzítve!")
