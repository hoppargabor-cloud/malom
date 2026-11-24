
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


def ertekeld_minoseget(nedv, siker, feherje, zeleny, w_ertek):
    """Szakmai laborminősítés összegző."""
    megjegyzesek = []
    hibak = 0

    if nedv > 15.0:
        hibak += 1
        megjegyzesek.append("Magas nedvesség (>15,0%)")
    if siker > 0 and siker < 26.0:
        hibak += 1
        megjegyzesek.append("Alacsony sikér (<26,0%)")
    if feherje > 0 and feherje < 10.5:
        hibak += 1
        megjegyzesek.append("Alacsonyabb fehérje (<10,5%)")
    if zeleny > 0 and zeleny < 25.0:
        hibak += 1
        megjegyzesek.append("Alacsonyabb Zeleny index")
    if w_ertek > 0 and w_ertek < 160.0:
        hibak += 1
        megjegyzesek.append("Alacsonyabb W érték")

    if hibak == 0:
        return "MEGFELELŐ / PRÉMIUM", "Minden vizsgált paraméter a kívánatos tartományban van."
    elif hibak == 1:
        return "FELTÉTELES / ELTÉRÉSSEL", "; ".join(megjegyzesek)
    else:
        return "NEM MEGFELELŐ", "; ".join(megjegyzesek)


def render_nyomtatasi_kep(cim_alcim, termek, minta, lot, datum, nedv, siker, feherje, zeleny, w_ertek, minosites, indoklas, key_prefix):
    """Nyomtatható minősítési jegyzőkönyv / nyomtatási kép."""
    if st.button("🖨️ Nyomtatási kép megjelenítése", key=f"print_btn_{key_prefix}"):
        st.markdown(f"""
        <div style="border: 2px solid #222; padding: 22px; background-color: #ffffff; color: #000000; border-radius: 8px; max-width: 780px; margin: 10px 0;">
            <h2 style="text-align: center; margin: 0 0 4px 0; color: #000000;">TÁPIÓGYÖRGYE KIRÁLY MALOM</h2>
            <h4 style="text-align: center; margin: 0 0 12px 0; color: #000000;">{cim_alcim}</h4>
            <hr style="border: 1px solid #222;">
            <p style="margin: 4px 0; color: #000000;"><b>Termék / Gabona:</b> {termek} &nbsp;|&nbsp; <b>Minta / Partner:</b> {minta} &nbsp;|&nbsp; <b>Tétel/LOT:</b> {lot}</p>
            <p style="margin: 4px 0 12px 0; color: #000000;"><b>Dátum:</b> {datum} &nbsp;|&nbsp; <b>Nyomtatva:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <table border="1" style="width:100%; border-collapse: collapse; text-align: center; color: #000000; background-color: #ffffff;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th style="padding: 8px;">Vizsgált paraméter</th>
                        <th style="padding: 8px;">Mért érték</th>
                        <th style="padding: 8px;">Tájékoztató elvárás</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 7px;"><b>Nedvesség</b></td>
                        <td style="padding: 7px;">{nedv:.2f} %</td>
                        <td style="padding: 7px;">max. 15,0 %</td>
                    </tr>
                    <tr>
                        <td style="padding: 7px;"><b>Sikér</b></td>
                        <td style="padding: 7px;">{siker:.1f} %</td>
                        <td style="padding: 7px;">min. 26,0–27,0 %</td>
                    </tr>
                    <tr>
                        <td style="padding: 7px;"><b>Fehérje</b></td>
                        <td style="padding: 7px;">{feherje:.2f} %</td>
                        <td style="padding: 7px;">min. 10,5–12,0 %</td>
                    </tr>
                    <tr>
                        <td style="padding: 7px;"><b>Zeleny index</b></td>
                        <td style="padding: 7px;">{zeleny:.1f} ml</td>
                        <td style="padding: 7px;">min. 25,0–30,0 ml</td>
                    </tr>
                    <tr>
                        <td style="padding: 7px;"><b>W érték</b></td>
                        <td style="padding: 7px;">{w_ertek:.0f}</td>
                        <td style="padding: 7px;">min. 160–220</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin: 14px 0 6px 0; color: #000000;"><b>Laborminősítés:</b> <u>{minosites}</u> — {indoklas}</p>
            <br>
            <p style="text-align: right; margin: 16px 0 0 0; color: #000000;">______________________________<br>Laboratórium / Minőségellenőr</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Nyomtatáshoz vagy PDF-be mentéshez használd a böngésző nyomtatás funkcióját (**Ctrl + P** / **Command + P**).")


# Adatbázis kapcsolat létrehozása / ellenőrzése és migráció
def init_db():
    conn = sqlite3.connect('malom_data.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS labor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mintakod TEXT,
            datum TEXT,
            termek TEXT,
            lot TEXT,
            kiszereles TEXT,
            nedvesseg REAL,
            siker REAL,
            sikerterules REAL,
            hamu REAL,
            feherje REAL,
            esesszam REAL,
            zeleny REAL,
            w_ertek REAL,
            sutoipari TEXT
        )
    ''')

    cursor.execute("PRAGMA table_info(labor)")
    labor_oszlopok = [row[1] for row in cursor.fetchall()]

    hianyzo_labor_oszlopok = {
        "mintakod": "TEXT",
        "lot": "TEXT",
        "kiszereles": "TEXT",
        "siker": "REAL",
        "sikerterules": "REAL",
        "esesszam": "REAL",
        "zeleny": "REAL",
        "w_ertek": "REAL",
        "sutoipari": "TEXT"
    }
    for oszlop, tipus in hianyzo_labor_oszlopok.items():
        if oszlop not in labor_oszlopok:
            cursor.execute(f"ALTER TABLE labor ADD COLUMN {oszlop} {tipus}")

    cursor.execute("PRAGMA table_info(labor)")
    labor_oszlopok = [row[1] for row in cursor.fetchall()]
    if "gluten" in labor_oszlopok and "siker" in labor_oszlopok:
        cursor.execute("UPDATE labor SET siker = gluten WHERE siker IS NULL AND gluten IS NOT NULL")
    if "terules" in labor_oszlopok and "sikerterules" in labor_oszlopok:
        cursor.execute("UPDATE labor SET sikerterules = terules WHERE sikerterules IS NULL AND terules IS NOT NULL")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keszlet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termek TEXT,
            mennyiseg_kg REAL,
            minoseg TEXT,
            modositas_datum TEXT
        )
    ''')
    cursor.execute("PRAGMA table_info(keszlet)")
    keszlet_oszlopok = [row[1] for row in cursor.fetchall()]
    if "modositas_datum" not in keszlet_oszlopok:
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
            ("Rétesliszt (BFF55)", 3100.0, "I. Osztály", most_str),
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

    if not df_keszlet.empty:
        with st.expander("🗑️ Készlet tétel törlése"):
            k_torol_opciok = [f"#{r['id']} | {r['termek']} ({r['mennyiseg_kg']} kg)" for _, r in df_keszlet.iterrows()]
            k_torol_val = st.selectbox("Törlendő készlet sor:", k_torol_opciok, key="k_torol_sel")
            k_torol_id = int(k_torol_val.split("|")[0].replace("#", "").strip())
            if st.button("Kiválasztott készlet sor törlése", key="k_torol_btn"):
                conn.execute("DELETE FROM keszlet WHERE id = ?", (k_torol_id,))
                conn.commit()
                st.success("Készlet tétel törölve!")
                st.rerun()

    st.subheader("Új készlet tétel rögzítése / módosítása")
    with st.form("keszlet_form"):
        valaszthato_nevek = sorted(list(set(
            TERMEKEK_LISTA + [
                "Graham liszt",
                "Asztali dara",
                "Rétesliszt (BFF55)",
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

    df_osszes_labor_torleshez = pd.read_sql("SELECT * FROM labor ORDER BY id DESC", conn)
    if not df_osszes_labor_torleshez.empty:
        with st.expander("🗑️ Laboreredmény törlése"):
            l_torol_opciok = [
                f"#{r['id']} | {r['datum']} | {r['termek']} | Minta: {r.get('mintakod') or '-'}"
                for _, r in df_osszes_labor_torleshez.iterrows()
            ]
            l_torol_val = st.selectbox("Törlendő laborvizsgálat:", l_torol_opciok, key="l_torol_sel")
            l_torol_id = int(l_torol_val.split("|")[0].replace("#", "").strip())
            if st.button("Kiválasztott laborvizsgálat törlése", key="l_torol_btn"):
                conn.execute("DELETE FROM labor WHERE id = ?", (l_torol_id,))
                conn.commit()
                st.success("Laborvizsgálat törölve!")
                st.rerun()

    st.markdown("---")
    st.subheader("Új laborvizsgálat rögzítése és Tanúsítvány kiállítása")

    with st.form("labor_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            l_datum = st.date_input("Vizsgálat dátuma", value=datetime.today())
            l_mintakod = st.text_input("Mintakód", value=f"M-{datetime.now().strftime('%Y%m%d-%H%M')}")
        with f_col2:
            l_termek = st.selectbox("Termék", TERMEKEK_LISTA)
            l_lot = st.text_input("Tétel / LOT", value="")
        with f_col3:
            l_kiszereles = st.text_input("Kiszerelés", value="25 kg")
            l_sutoipari = st.text_input("Sütőipari / Minőségi besorolás", value="Prémium / Kiváló")

        st.markdown("**Laborminősítés paraméterei (Nedvesség, Sikér, Fehérje, Zeleny index, W érték):**")
        c1, c2, c3 = st.columns(3)
        with c1:
            l_nedv = st.number_input("Nedvesség (%)", value=14.0, step=0.1)
            l_siker = st.number_input("Sikér (%)", value=28.5, step=0.1)
        with c2:
            l_feherje = st.number_input("Fehérje (%)", value=12.2, step=0.1)
            l_hamu = st.number_input("Hamutartalom (%)", value=0.65, step=0.01)
        with c3:
            l_zeleny = st.number_input("Zeleny index (ml)", value=45.0, step=1.0)
            l_w = st.number_input("W érték", value=220.0, step=5.0)
            l_sikerterules = st.number_input("Sikérterülés (mm)", value=4.0, step=0.5)
            l_esesszam = st.number_input("Esésszám (s)", value=320.0, step=5.0)

        l_submit = st.form_submit_button("Laboreredmény és minősítés mentése")
        if l_submit:
            conn.execute('''
                INSERT INTO labor (
                    mintakod, datum, termek, lot, kiszereles,
                    nedvesseg, siker, sikerterules, hamu, feherje,
                    esesszam, zeleny, w_ertek, sutoipari
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                l_mintakod, str(l_datum), l_termek, l_lot, l_kiszereles,
                l_nedv, l_siker, l_sikerterules, l_hamu, l_feherje,
                l_esesszam, l_zeleny, l_w, l_sutoipari
            ))
            conn.commit()
            st.success("Laboreredmény sikeresen elmentve!")
            st.rerun()

    st.markdown("---")
    st.subheader("🏅 Laborminősítés & Nyomtatható Nyomtatási Kép")

    df_osszes_labor = pd.read_sql("SELECT * FROM labor ORDER BY id DESC", conn)

    if not df_osszes_labor.empty:
        valaszthato_sorok = [
            f"#{row['id']} | {row['datum']} | {row['termek']} | Minta: {row.get('mintakod') or '-'}"
            for _, row in df_osszes_labor.iterrows()
        ]
        kivalasztott_cimke = st.selectbox("Válassz laborvizsgálatot a minősítéshez és nyomtatáshoz:", valaszthato_sorok)
        kivalasztott_index = valaszthato_sorok.index(kivalasztott_cimke)
        sor = df_osszes_labor.iloc[kivalasztott_index]

        m_nedv = float(sor["nedvesseg"]) if pd.notna(sor.get("nedvesseg")) else 0.0
        m_siker = float(sor["siker"]) if pd.notna(sor.get("siker")) else 0.0
        m_feherje = float(sor["feherje"]) if pd.notna(sor.get("feherje")) else 0.0
        m_zeleny = float(sor["zeleny"]) if pd.notna(sor.get("zeleny")) else 0.0
        m_w = float(sor["w_ertek"]) if pd.notna(sor.get("w_ertek")) else 0.0
        m_termek = sor.get("termek") or "-"
        m_datum = sor.get("datum") or "-"
        m_minta = sor.get("mintakod") or "-"
        m_lot = sor.get("lot") or "-"
    else:
        m_nedv, m_siker, m_feherje, m_zeleny, m_w = 14.0, 28.5, 12.2, 45.0, 220.0
        m_termek = st.selectbox("Termék:", TERMEKEK_LISTA, key="minosites_ures_termek")
        m_datum = datetime.today().strftime("%Y-%m-%d")
        m_minta = "MINTA-01"
        m_lot = "-"

    minosites_eredmeny, minosites_indoklas = ertekeld_minoseget(m_nedv, m_siker, m_feherje, m_zeleny, m_w)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Nedvesség", f"{m_nedv:.1f} %")
    k2.metric("Sikér", f"{m_siker:.1f} %")
    k3.metric("Fehérje", f"{m_feherje:.1f} %")
    k4.metric("Zeleny index", f"{m_zeleny:.1f} ml")
    k5.metric("W érték", f"{m_w:.0f}")

    st.info(f"**Laborminősítés:** {minosites_eredmeny} — {minosites_indoklas}")

    render_nyomtatasi_kep(
        "LABORMİNŐSÍTÉSI JEGYZŐKÖNYV / NYOMTATÁSI KÉP",
        m_termek, m_minta, m_lot, m_datum,
        m_nedv, m_siker, m_feherje, m_zeleny, m_w,
        minosites_eredmeny, minosites_indoklas,
        key_prefix="labor_oldal"
    )

    st.markdown("---")
    st.subheader("🏷️ Nyomtatható Címke a Laborzacskókra")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        cimke_termek = st.selectbox("Zacskó terméke:", TERMEKEK_LISTA, key="cimke_termek_sel")
        cimke_minta = st.text_input("Minta / Sarzs / Siló azonosító", value=str(m_minta))
    with c_col2:
        cimke_datum = st.text_input("Dátum", value=str(m_datum))
        cimke_megj = st.text_input("Megjegyzés", value=minosites_eredmeny)

    if st.button("Laborzacskó címke előnézet"):
        st.markdown(f"""
        <div style="width: 350px; border: 2px dashed #222; padding: 12px; background-color: #fffef5; color: #000; border-radius: 6px; font-family: monospace;">
            <div style="font-weight: bold; font-size: 13px; border-bottom: 1px solid #222; padding-bottom: 4px; margin-bottom: 6px;">
                TÁPIÓGYÖRGYE KIRÁLY MALOM - LABOR
            </div>
            <div><b>Minta:</b> {cimke_minta} | <b>Dátum:</b> {cimke_datum}</div>
            <div><b>Termék:</b> {cimke_termek}</div>
            <div><b>Nedv:</b> {m_nedv:.1f}% | <b>Sikér:</b> {m_siker:.1f}% | <b>Feh:</b> {m_feherje:.1f}%</div>
            <div><b>Zeleny:</b> {m_zeleny:.0f} ml | <b>W:</b> {m_w:.0f}</div>
            <div style="margin-top: 4px; font-size: 12px;"><i>{cimke_megj}</i></div>
        </div>
        """, unsafe_allow_html=True)

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

    df_osszes_besz_torleshez = pd.read_sql("SELECT * FROM beszallitas ORDER BY id DESC", conn)
    if not df_osszes_besz_torleshez.empty:
        with st.expander("🗑️ Beszállítás tétel törlése"):
            b_torol_opciok = [
                f"#{r['id']} | {r['datum']} | {r['termek']} | {r['mennyiseg_t']} t ({r.get('partner') or '-'})"
                for _, r in df_osszes_besz_torleshez.iterrows()
            ]
            b_torol_val = st.selectbox("Törlendő beszállítás:", b_torol_opciok, key="b_torol_sel")
            b_torol_id = int(b_torol_val.split("|")[0].replace("#", "").strip())
            if st.button("Kiválasztott beszállítás törlése", key="b_torol_btn"):
                conn.execute("DELETE FROM beszallitas WHERE id = ?", (b_torol_id,))
                conn.commit()
                st.success("Beszállítás törölve!")
                st.rerun()

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

    # --- KÖZVETLEN LABORATÓRIUMI MINŐSÍTÉS A BESZÁLLÍTÁSI NAPLÓ OLDALON ---
    st.markdown("---")
    st.subheader("🏅 Laboratóriumi Minősítés & Nyomtatható Kép")

    bn_c1, bn_c2, bn_c3, bn_c4, bn_c5 = st.columns(5)
    with bn_c1:
        bn_nedv = st.number_input("Nedvesség (%)", value=13.2, step=0.1, key="bn_nedv")
    with bn_c2:
        bn_siker = st.number_input("Sikér (%)", value=28.5, step=0.1, key="bn_siker")
    with bn_c3:
        bn_feherje = st.number_input("Fehérje (%)", value=12.2, step=0.1, key="bn_feherje")
    with bn_c4:
        bn_zeleny = st.number_input("Zeleny index (ml)", value=45.0, step=1.0, key="bn_zeleny")
    with bn_c5:
        bn_w = st.number_input("W érték", value=220.0, step=5.0, key="bn_w")

    bn_minosites, bn_indoklas = ertekeld_minoseget(bn_nedv, bn_siker, bn_feherje, bn_zeleny, bn_w)
    st.info(f"**Minősítés:** {bn_minosites} — {bn_indoklas}")

    bn_minta = st.text_input("Minta / Partner azonosító a nyomtatáshoz", value="BESZÁLLÍTÁS-MINTA", key="bn_minta")
    render_nyomtatasi_kep(
        "BESZÁLLÍTÁSI LABORMİNŐSÍTÉS / NYOMTATÁSI KÉP",
        "Gabona / Búza",
        bn_minta,
        "-",
        datetime.today().strftime("%Y-%m-%d"),
        bn_nedv, bn_siker, bn_feherje, bn_zeleny, bn_w,
        bn_minosites, bn_indoklas,
        key_prefix="beszallitas_oldal"
    )

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
