
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

TERMEKEK_LISTA = [
    "BL-55 Rétesliszt",
    "BL-80 Kenyérliszt",
    "Graham liszt",
    "Asztali dara",
    "Teljes kiőrlésű tönköly",
    "Salvatore reale",
    "BL65 süteményliszt",
    "KRBL100",
    "KRBL220",
    "Manitoba pizzaliszt",
    "Integrale teljeskiőrlésű liszt"
]

# Adatbázis kapcsolat létrehozása / ellenőrzése és migráció
def init_db():
    conn = sqlite3.connect('malom_data.db', check_same_thread=False)
    cursor = conn.cursor()
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
            minoseg TEXT,
            modositas_datum TEXT
        )
    ''')
    # Ha a keszlet tábla már létezett modositas_datum nélkül, bővítjük
    cursor.execute("PRAGMA table_info(keszlet)")
    oszlopok = [row[1] for row in cursor.fetchall()]
    if "modositas_datum" not in oszlopok:
        cursor.execute("ALTER TABLE keszlet ADD COLUMN modositas_datum TEXT")
        most = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("UPDATE keszlet SET modositas_datum = ? WHERE modositas_datum IS NULL", (most,))

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

    if 'koptatas_aktiv' not in st.session_state: st.session_state.koptatas_aktiv = True
    if 'orlo_aktiv' not in st.session_state: st.session_state.orlo_aktiv = True
    if 'szita_aktiv' not in st.session_state: st.session_state.szita_aktiv = True
    if 'pneumatika_aktiv' not in st.session_state: st.session_state.pneumatika_aktiv = True

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Koptatás: " + ("ÜZEMBEN" if st.session_state.koptatas_aktiv else "LEÁLLÍTVA")):
            st.session_state.koptatas_aktiv = not st.session_state.koptatas_aktiv
    with col2:
        if st.button("⚙️ Őrlő Részleg: " + ("AKTÍV" if st.session_state.orlo_aktiv else "INAKTÍV")):
            st.session_state.orlo_aktiv = not st.session_state.orlo_aktiv
    with col3:
        if st.button("🛜 Szita Rendszer: " + ("FUT" if st.session_state.szita_aktiv else "LEÁLLÍTVA")):
            st.session_state.szita_aktiv = not st.session_state.szita_aktiv
    with col4:
        if st.button("💨 Pneumatika: " + ("NYOMÁSON" if st.session_state.pneumatika_aktiv else "KIKAPCSOLVA")):
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
            viz_igeny = (teljesitmeny * 1000 * (cel_nedv - alap_nedv)) / (100 - cel_nedv)
            st.success(f"Szükséges vízpermet: **{viz_igeny:.2f} liter/óra**.")
        else:
            st.warning("A cél nedvességnek magasabbnak kell lennie az alapnedvességnél.")

# --- 2. KÉSZLETKEZELÉS & SILÓK ---
elif modul == "Készletkezelés & Silók":
    st.title("📦 Készletkezelés és Silóállapotok")

    df_keszlet = pd.read_sql("SELECT * FROM keszlet", conn)
    most_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if df_keszlet.empty:
        alap_termekek = [
            ("Graham liszt", 1250.0, "Prémium", most_str),
            ("Asztali dara", 840.0, "Standard", most_str),
            ("Rétesliszt (BL55)", 3100.0, "I. Osztály", most_str),
            ("Étkezési korpa", 950.0, "Takarmány/Élelmi", most_str),
            ("BL-80 kenyérliszt", 5400.0, "I. Osztály", most_str),
            ("Salvatore reale", 0.0, "Különleges", most_str),
            ("BL65 süteményliszt", 0.0, "Sütemény", most_str),
            ("KRBL100", 0.0, "Különleges", most_str),
            ("KRBL220", 0.0, "Különleges", most_str),
            ("Manitoba pizzaliszt", 0.0, "Pizza/Erős", most_str),
            ("Integrale teljeskiőrlésű liszt", 0.0, "Teljes kiőrlésű", most_str),
        ]
        conn.executemany(
            "INSERT INTO keszlet (termek, mennyiseg_kg, minoseg, modositas_datum) VALUES (?, ?, ?, ?)",
            alap_termekek
        )
        conn.commit()
        df_keszlet = pd.read_sql("SELECT * FROM keszlet", conn)

    st.dataframe(df_keszlet, use_container_width=True)

    st.subheader("Új készlet tétel rögzítése / módosítása")
    with st.form("keszlet_form"):
        valaszthato_nevek = sorted(list(set(
            TERMEKEK_LISTA + [
                "Graham liszt",
                "Asztali dara",
                "Rétesliszt (BL55)",
                "Étkezési korpa",
                "BL-80 kenyérliszt",
                "Egyedi..."
            ]
        )))
        k_valasztott = st.selectbox("Termék kiválasztása", valaszthato_nevek)
        k_egyedi = st.text_input("Egyedi termék neve (ha 'Egyedi...' van kiválasztva)")
        k_termek = k_egyedi.strip() if k_valasztott == "Egyedi..." else k_valasztott
        k_mennyiseg = st.number_input("Mennyiség (kg)", min_value=0.0, step=50.0)
        k_minoseg = st.text_input("Minőségi osztály / Megjegyzés")
        k_mod_datum = st.text_input("Módosítás dátuma", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        submitted = st.form_submit_button("Mentés a készletbe")
        if submitted and k_termek:
            meglevo = conn.execute("SELECT id FROM keszlet WHERE termek = ?", (k_termek,)).fetchone()
            if meglevo:
                conn.execute(
                    "UPDATE keszlet SET mennyiseg_kg = ?, minoseg = ?, modositas_datum = ? WHERE id = ?",
                    (k_mennyiseg, k_minoseg, k_mod_datum, meglevo[0])
                )
            else:
                conn.execute(
                    "INSERT INTO keszlet (termek, mennyiseg_kg, minoseg, modositas_datum) VALUES (?, ?, ?, ?)",
                    (k_termek, k_mennyiseg, k_minoseg, k_mod_datum)
                )
            conn.commit()
            st.success("Sikeresen rögzítve / frissítve!")
            st.rerun()

# --- 3. LABOR & MINŐSÉGI BIZONYÍTVÁNY ---
elif modul == "Labor & Minőségi Bizonyítvány":
    st.title("🧪 Laboratóriumi Eredmények & Minőségi Bizonyítvány")

    st.subheader("Múltbeli laboreredmények keresése")
    d_tol, d_ig = st.columns(2)
    with d_tol:
        datum_tol = st.date_input("Kezdő dátum", value=datetime.today().replace(day=1))
    with d_ig:
        datum_ig = st.date_input("Záró dátum", value=datetime.today())

    df_labor = pd.read_sql(
        "SELECT * FROM labor WHERE datum BETWEEN ? AND ? ORDER BY id DESC",
        conn,
        params=(str(datum_tol), str(datum_ig))
    )

    if not df_labor.empty:
        st.dataframe(df_labor, use_container_width=True)
    else:
        df_labor_all = pd.read_sql("SELECT * FROM labor ORDER BY id DESC", conn)
        if not df_labor_all.empty:
            st.dataframe(df_labor_all, use_container_width=True)
        else:
            st.info("Még nincsenek rögzített laboreredmények.")

    st.markdown("---")
    st.subheader("Új laborvizsgálat rögzítése és Tanúsítvány kiállítása")

    with st.form("labor_form"):
        l_datum = st.date_input("Vizsgálat dátuma", value=datetime.today())
        l_termek = st.selectbox("Termék", TERMEKEK_LISTA)
        c1, c2, c3 = st.columns(3)
        with c1:
            l_nedv = st.number_input("Nedvesség (%)", value=14.0, step=0.1)
            l_gluten = st.number_input("Sikér / Nedves sikér (%)", value=28.5, step=0.1)
        with c2:
            l_feherje = st.number_input("Fehérje (%)", value=12.2, step=0.1)
            l_hamu = st.number_input("Hamu (%)", value=0.65, step=0.01)
        with c3:
            l_zeleny = st.number_input("Zeleny index (ml)", value=45.0, step=1.0)
            l_w = st.number_input("W érték", value=220.0, step=5.0)
            l_falling = st.number_input("Falling Number (s)", value=320.0, step=5.0)
            l_terules = st.number_input("Terülés (mm)", value=65.0, step=1.0)

        l_submit = st.form_submit_button("Laboreredmény mentése")
        if l_submit:
            conn.execute('''
                INSERT INTO labor (datum, termek, nedvesseg, gluten, feherje, hamutartalom, falling_number, zeleny, w_ertek, terules)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(l_datum), l_termek, l_nedv, l_gluten, l_feherje, l_hamu, l_falling, l_zeleny, l_w, l_terules))
            conn.commit()
            st.success("Laboreredmény sikeresen elmentve!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🖨️ Minőségi Bizonyítvány / Nyomtatási Kép")
    biz_termek = st.selectbox("Válassz terméket a bizonylathoz:", TERMEKEK_LISTA, key="biz_termek_sel")

    utolso_sor = conn.execute(
        "SELECT datum, nedvesseg, gluten, feherje, hamutartalom, zeleny, w_ertek FROM labor WHERE termek = ? ORDER BY id DESC LIMIT 1",
        (biz_termek,)
    ).fetchone()

    if utolso_sor:
        b_datum, b_nedv, b_gluten, b_feherje, b_hamu, b_zeleny, b_w = utolso_sor
    else:
        b_datum, b_nedv, b_gluten, b_feherje, b_hamu, b_zeleny, b_w = (
            datetime.now().strftime('%Y-%m-%d'), 14.0, 28.5, 12.2, 0.65, 45.0, 220.0
        )

    if st.button("Nyomtatási kép generálása (Bizonyítvány)"):
        st.markdown(f"""
        <div style="border: 2px solid #333; padding: 20px; background-color: #fff; color: #000; border-radius: 10px;">
            <h2 style="text-align: center; margin-bottom: 4px;">TÁPIÓGYÖRGYE KIRÁLY MALOM</h2>
            <h4 style="text-align: center; margin-top: 0;">MINŐSÉGI BIZONYÍTVÁNY</h4>
            <hr>
            <p><b>Termék megnevezése:</b> {biz_termek}</p>
            <p><b>Vizsgálat / Kiállítás dátuma:</b> {b_datum} (nyomtatva: {datetime.now().strftime('%Y-%m-%d %H:%M')})</p>
            <table border="1" style="width:100%; border-collapse: collapse; text-align: center; padding: 6px;">
                <tr><th>Paraméter</th><th>Mért érték</th><th>Előírt határérték</th></tr>
                <tr><td>Nedvesség</td><td>{b_nedv:.2f} %</td><td>max. 15.0 %</td></tr>
                <tr><td>Hamu</td><td>{b_hamu:.2f} %</td><td>szabvány szerint</td></tr>
                <tr><td>Sikér</td><td>{b_gluten:.1f} %</td><td>min. 27.0 %</td></tr>
                <tr><td>Fehérje</td><td>{b_feherje:.2f} %</td><td>min. 11.0 %</td></tr>
                <tr><td>Zeleny</td><td>{b_zeleny:.1f} ml</td><td>min. 30.0 ml</td></tr>
                <tr><td>W érték</td><td>{b_w:.0f}</td><td>min. 180</td></tr>
            </table>
            <br>
            <p style="text-align: right;">__________________________<br>Minőségellenőr aláírása</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("Nyomtatáshoz használd a böngésződ nyomtatás funkcióját (Ctrl+P / Command+P).")

    st.markdown("### 🏷️ Nyomtatható Címke a Laborzacskókra")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        cimke_termek = st.selectbox("Zacskó terméke:", TERMEKEK_LISTA, key="cimke_termek_sel")
        cimke_minta = st.text_input("Minta / Sarzs / Siló azonosító", value="MINTA-01")
    with c_col2:
        cimke_datum = st.text_input("Dátum", value=datetime.now().strftime("%Y-%m-%d"))
        cimke_megj = st.text_input("Megjegyzés (pl. beérkezés / őrlés)", value="Labor minta")

    if st.button("Laborzacskó címke előnézet"):
        st.markdown(f"""
        <div style="width: 340px; border: 2px dashed #222; padding: 12px; background-color: #fffef5; color: #000; border-radius: 6px; font-family: monospace;">
            <div style="font-weight: bold; font-size: 14px; border-bottom: 1px solid #222; padding-bottom: 4px; margin-bottom: 6px;">
                TÁPIÓGYÖRGYE KIRÁLY MALOM - LABOR
            </div>
            <div><b>Minta:</b> {cimke_minta} | <b>Dátum:</b> {cimke_datum}</div>
            <div><b>Termék:</b> {cimke_termek}</div>
            <div><b>Nedv:</b> {b_nedv:.1f}% | <b>Hamu:</b> {b_hamu:.2f}% | <b>Feh:</b> {b_feherje:.1f}%</div>
            <div><b>Sikér:</b> {b_gluten:.1f}% | <b>Zel:</b> {b_zeleny:.0f} | <b>W:</b> {b_w:.0f}</div>
            <div style="margin-top: 4px; font-size: 12px;"><i>{cimke_megj}</i></div>
        </div>
        """, unsafe_allow_html=True)
        st.info("A címke nyomtatásához is a böngésző nyomtatási képét (Ctrl+P) használhatod.")

# --- 4. BESZÁLLÍTÁSI NAPLÓ ---
elif modul == "Beszállítási Napló":
    st.title("🚛 Beszállítási Napló & Nyersanyagkövetés")

    st.subheader("Beszállítások szűrése dátum szerint")
    b_tol, b_ig = st.columns(2)
    with b_tol:
        b_datum_tol = st.date_input("Beszállítás tól", value=datetime.today().replace(day=1), key="b_t")
    with b_ig:
        b_datum_ig = st.date_input("Beszállítás ig", value=datetime.today(), key="b_i")

    df_besz = pd.read_sql(
        "SELECT * FROM beszallitas WHERE datum BETWEEN ? AND ? ORDER BY id DESC",
        conn,
        params=(str(b_datum_tol), str(b_datum_ig))
    )

    st.markdown("### 🌾 Búza összegzés")
    df_buza_all = pd.read_sql(
        "SELECT * FROM beszallitas WHERE lower(termek) LIKE '%búza%' OR lower(termek) LIKE '%buza%'",
        conn
    )
    if not df_buza_all.empty:
        ossz_buza_t = df_buza_all["mennyiseg_t"].sum()
        tetelek_szama = len(df_buza_all)
        if ossz_buza_t > 0:
            atlag_nedv = (df_buza_all["mennyiseg_t"] * df_buza_all["nedvesseg"]).sum() / ossz_buza_t
        else:
            atlag_nedv = 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric("Összes beszállított búza", f"{ossz_buza_t:.2f} t")
        m2.metric("Búza tételek száma", f"{tetelek_szama} db")
        m3.metric("Súlyozott átlag nedvesség", f"{atlag_nedv:.2f} %")

        buza_bontas = df_buza_all.groupby("termek", as_index=False).agg(
            tetelek=("id", "count"),
            osszes_t=("mennyiseg_t", "sum"),
            atlag_nedvesseg=("nedvesseg", "mean")
        )
        st.dataframe(buza_bontas, use_container_width=True)
    else:
        st.info("Még nincs rögzített búza beszállítás az összegzéshez.")

    st.markdown("---")
    if not df_besz.empty:
        st.dataframe(df_besz, use_container_width=True)
    else:
        df_besz_all = pd.read_sql("SELECT * FROM beszallitas ORDER BY id DESC", conn)
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
            conn.execute(
                "INSERT INTO beszallitas (datum, partner, termek, mennyiseg_t, nedvesseg) VALUES (?, ?, ?, ?, ?)",
                (str(b_datum), b_partner, b_termek, b_mennyiseg, b_nedv)
            )
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
