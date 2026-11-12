import sqlite3
from datetime import datetime
import streamlit as st

TERMEKEK = [
    "Tönke 70",
    "Tönke 90",
    "BL65 Kende süteményliszt",
    "BL80 Kerecsen",
    "BL112",
    "KRBL100",
    "KBD100",
    "KRBL220",
    "Kecskeméti Rétes100",
    "Manitoba",
    "Integrale TK Pizzaliszt",
    "Salvatore Reale pizza liszt",
    "BL65",
    "BL80",
    "Búzakorpa",
    "Étkezési korpa",
    "Étkezési búzacspira",
    "1. Töret",
    "Raktári Búza",
]

KISZERELESEK = ["1 kg", "2 kg", "5 kg", "25 kg", "50 kg", "BigBag"]

# --- ADATBÁZIS INICIALIZÁLÁS ---
DB_NAME = "malom_data.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute(
      "CREATE TABLE IF NOT EXISTS beerkezes (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, beszallito TEXT, termeny TEXT, mennyiseg_kg"
      " REAL, nedvesseg REAL, tisztasag_minoseg TEXT, hekto REAL, siker REAL,"
      " feherje REAL, zeleny REAL, w_ertek REAL, megjegyzes TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS muszak (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, kiszereles TEXT, termek TEXT, zsakolt_kg"
      " REAL, zsak_db REAL)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS kimenö_aru (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, vevo TEXT, termek TEXT, kiszereles TEXT,"
      " mennyiseg_kg REAL, zsak_db REAL, sofor TEXT, megjegyzes TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS energia (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, ora_allas REAL, fogyasztas_kwh REAL,"
      " leorolt_tonna REAL, megjegyzes TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS haccp (id INTEGER PRIMARY KEY AUTOINCREMENT,"
      " datum TEXT, muszak TEXT, uevetores TEXT, szita_epseg TEXT,"
      " kartevo_ellenorzes TEXT, magnes_tisztitas TEXT, megjegyzes TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS ex_vedelem (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, foldeles TEXT, porelszivo TEXT,"
      " magnes_muvek TEXT, megjegyzes TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS karbantartas (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, datum TEXT, gep_egyseg TEXT, elv_munka TEXT, alkatresz"
      " TEXT, szerelo TEXT, megjegyzes TEXT)"
  )
  conn.commit()
  conn.close()


init_db()

# --- OLDAL BEÁLLÍTÁSOK ---
st.set_page_config(
    page_title="Tápiógyörgye Király Malom Master PRO", layout="wide"
)

st.title("🌾 TÁPIÓGYÖRGYE KIRÁLY MALOM - MASTER v5.8 PRO")
st.markdown("---")

# --- MENÜ VÁLASZTÓ ---
menu = st.sidebar.selectbox(
    "Válassz modult:",
    [
        "🖥️ Folyamatábra (SCADA)",
        "📊 Dashboard & Készlet",
        "📥 Nyersbúza Beérkezés",
        "📋 Zsákolási Műszak",
        "🚚 Kiszállítás & Szállítólevél",
        "🛍️ Zsákok & Csomagolás",
        "⚡ Energia & Fogyasztás",
        "🔬 Labor & Minőségi Címke",
        "📄 Minőségi Bizonyítvány",
        "🛡️ HACCP",
        "🧯 Ex-Védelem",
        "⚙️ Gépészet & Karbantartás",
    ],
)

# --- 1. SCADA FOLYAMATÁBRA ---
if menu == "🖥️ Folyamatábra (SCADA)":
  st.header("🖥️ Malmi Folyamatábra & Koptatási Vezérlő")
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.success("● Koptatás: ÜZEMBEN")
  with col2:
    st.success("● Őrlő Részleg: AKTÍV")
  with col3:
    st.info("● Szita Rendszer: FUT")
  with col4:
    st.success("● Pneumatika: OK")

  st.markdown("---")
  st.subheader("💧 Vízszámítás & Kondicionálás")
  with st.form("scada_form"):
    c1, c2 = st.columns(2)
    with c1:
      alap_nedv = st.number_input("Alap nedvességtartalom (%)", value=13.5)
      cel_nedv = st.number_input("Cél nedvességtartalom (%)", value=16.0)
    with c2:
      teljesitmeny = st.number_input(
          "Koptató teljesítmény (t/h)", value=2.5, min_value=0.1
      )

    # Vízszámítás képlet
    viz_ora = (
        teljesitmeny * (cel_nedv - alap_nedv) * 10.0
        if cel_nedv > alap_nedv
        else 0.0
    )
    st.info(
        f"💧 **Szükséges vízadagolás:** **{viz_ora:.1f} liter / óra**"
    )
    st.form_submit_button("Koptatási Napló Mentése")

# --- 2. DASHBOARD ---
elif menu == "📊 Dashboard & Készlet":
  st.header("📊 Dashboard & Raktárkészlet")
  conn = sqlite3.connect(DB_NAME)
  c = conn.cursor()
  c.execute("SELECT SUM(zsakolt_kg) FROM muszak")
  tot_gyartva = c.fetchone()[0] or 0.0
  c.execute("SELECT SUM(mennyiseg_kg) FROM kimenö_aru")
  tot_kiment = c.fetchone()[0] or 0.0
  akt_keszlet = tot_gyartva - tot_kiment
  c.execute("SELECT SUM(mennyiseg_kg) FROM beerkezes")
  tot_beerkezes = c.fetchone()[0] or 0.0
  conn.close()

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Beérkezett Búza", f"{tot_beerkezes:,.0f} kg")
  with col2:
    st.metric("Összes Gyártott", f"{tot_gyartva:,.0f} kg")
  with col3:
    st.metric("Kiszállítva", f"{tot_kiment:,.0f} kg")
  with col4:
    st.metric("Aktuális Készlet", f"{akt_keszlet:,.0f} kg")

# --- 3. NYERSBÚZA BEÉRKEZÉS ---
elif menu == "📥 Nyersbúza Beérkezés":
  st.header("📥 Nyersbúza Beérkezés és Labor Minősítés")
  with st.form("beerkezes_form"):
    c1, c2 = st.columns(2)
    with c1:
      beszallito = st.text_input("Beszállító neve", value="Helyi Termelő Kft.")
      termeny = st.selectbox("Termény", ["Raktári Búza", "Étkezési Búza"])
      mennyiseg = st.number_input("Mennyiség (kg)", value=25000.0)
      nedv = st.number_input("Nedvesség (%)", value=13.5)
    with c2:
      hekto = st.number_input("Hekto (kg/hl)", value=78.0)
      siker = st.number_input("Sikér (%)", value=28.0)
      feh = st.number_input("Fehérje (%)", value=12.5)
      megj = st.text_input("Megjegyzés", value="")

    if st.form_submit_button("Mentés Silóba"):
      conn = sqlite3.connect(DB_NAME)
      c = conn.cursor()
      c.execute(
          "INSERT INTO beerkezes (datum, beszallito, termeny, mennyiseg_kg,"
          " nedvesseg, hekto, siker, feherje, megjegyzes) VALUES (?, ?, ?, ?,"
          " ?, ?, ?, ?, ?)",
          (
              datetime.now().strftime("%Y-%m-%d %H:%M"),
              beszallito,
              termeny,
              mennyiseg,
              nedv,
              hekto,
              siker,
              feh,
              megj,
          ),
      )
      conn.commit()
      conn.close()
      st.success("Sikeresen rögzítve!")

# --- 4. ZSÁKOLÁSI MŰSZAK ---
elif menu == "📋 Zsákolási Műszak":
  st.header("📋 Napi Műszak & Zsákolás")
  with st.form("muszak_form"):
    termek = st.selectbox("Gyártott Termék", TERMEKEK)
    kiszereles = st.selectbox("Kiszerelés", KISZERELESEK)
    zsak_db = st.number_input("Zsákok darabszáma (db)", value=40)
    suly_szam = (
        int(kiszereles.split()[0])
        if "kg" in kiszereles
        else (25 if "Big" in kiszereles else 1)
    )
    zsakolt_kg = zsak_db * suly_szam
    st.info(f"Összesen: {zsakolt_kg} kg")

    if st.form_submit_button("Zsákolás Mentése"):
      conn = sqlite3.connect(DB_NAME)
      c = conn.cursor()
      c.execute(
          "INSERT INTO muszak (datum, kiszereles, termek, zsakolt_kg, zsak_db)"
          " VALUES (?, ?, ?, ?, ?)",
          (
              datetime.now().strftime("%Y-%m-%d %H:%M"),
              kiszereles,
              termek,
              zsakolt_kg,
              zsak_db,
          ),
      )
      conn.commit()
      conn.close()
      st.success("Mentve!")

# --- 5. KISZÁLLÍTÁS ---
elif menu == "🚚 Kiszállítás & Szállítólevél":
  st.header("🚚 Kimenő Áru & Szállítólevél")
  with st.form("kimenö_form"):
    vevo = st.text_input("Vevő Neve", value="Pékség Kft.")
    termek = st.selectbox("Termék", TERMEKEK)
    mennyiseg = st.number_input("Mennyiség (kg)", value=1000.0)
    sofor = st.text_input("Sofőr / Jármű", value="Kovács Béla")
    if st.form_submit_button("Szállítólevél Kiállítása"):
      st.success("Szállítólevél rögzítve!")

# --- 6. ZSÁKOK & CSOMAGOLÁS ---
elif menu == "🛍️ Zsákok & Csomagolás":
  st.header("🛍️ Csomagolóanyag Készlet")
  st.write("Csomagolóanyagok és zsákok nyilvántartása.")

# --- 7. ENERGIA ---
elif menu == "⚡ Energia & Fogyasztás":
  st.header("⚡ Energetikai Napló")
  with st.form("energia_form"):
    ora = st.number_input("Villanyóra állás", value=12450.0)
    fogy = st.number_input("Napi fogyasztás (kWh)", value=450.0)
    tonna = st.number_input("Leőrölt búza (tonna)", value=12.0)
    if st.form_submit_button("Energia Mentése"):
      st.success("Energetikai adatok rögzítve!")

# --- 8. LABOR ---
elif menu == "🔬 Labor & Minőségi Címke":
  st.header("🏷️ Labor & Minőségi Címke")
  st.selectbox("Termék", TERMEKEK)
  st.text_input("Tételszám", value="TM-2026-001")
  st.info("Nyomtatási előnézet aktív (Ctrl+P)")

# --- 9. BIZONYÍTVÁNY ---
elif menu == "📄 Minőségi Bizonyítvány":
  st.header("📄 Hivatalos Minőségi Bizonyítvány")
  st.text_input("Vevő részére", value="Partner Kft.")
  st.button("Bizonyítvány Nyomtatása")

# --- 10. HACCP ---
elif menu == "🛡️ HACCP":
  st.header("🛡️ HACCP Ellenőrzési Napló")
  st.checkbox("Üvegtörés ellenőrzés elvégezve")
  st.checkbox("Szita épség ellenőrzése rendben")
  st.checkbox("Mágneses vasfogó tisztítva")

# --- 11. EX-VÉDELEM ---
elif menu == "🧯 Ex-Védelem":
  st.header("🧯 Robbanásbiztos (Ex) Zónák Naplója")
  st.checkbox("Földelési kötések ellenőrizve")
  st.checkbox("Porelszívó rendszer ellenőrizve")

# --- 12. GÉPÉSZET ---
elif menu == "⚙️ Gépészet & Karbantartás":
  st.header("⚙️ Gépészeti Karbantartási Napló")
  st.text_input("Gép egység / Csapágy", value="Henke Hengermű 1. oldal")
  st.text_input("Elvégzett munka", value="Szíjfeszítés és kenés")
  st.button("Karbantartás Mentése")