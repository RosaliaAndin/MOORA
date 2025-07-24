import streamlit as st
import numpy as np
import pandas as pd
import sqlite3
import hashlib
import os

USER_DB_FILE = "user.db"
DB_FILE = "alternatif.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alternatif (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    alternatif TEXT,
                    c1 INTEGER, c2 INTEGER, c3 INTEGER, c4 INTEGER, c5 INTEGER,
                    c6 INTEGER, c7 INTEGER, c8 INTEGER, c9 INTEGER
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bobot_kriteria (
                    username TEXT PRIMARY KEY,
                    c1 REAL, c2 REAL, c3 REAL, c4 REAL, c5 REAL,
                    c6 REAL, c7 REAL, c8 REAL, c9 REAL
                )''')
    conn.commit()
    conn.close()

def init_user_db():
    conn = sqlite3.connect(USER_DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

def save_user_to_db(username, password):
    conn = sqlite3.connect(USER_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
    conn.commit()
    conn.close()

def check_user_credentials(username, password):
    conn = sqlite3.connect(USER_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == hash_password(password)

def user_exists(username):
    conn = sqlite3.connect(USER_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def init_bobot_db():
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    #c.execute("DROP TABLE IF EXISTS bobot_kriteria")  # Optional: hapus dulu kalau mau buat ulang
    c.execute("""
        CREATE TABLE IF NOT EXISTS bobot_kriteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            kriteria TEXT,
            keterangan TEXT,
            bobot REAL,
            jenis TEXT,
            UNIQUE(username, kriteria)
        )
    """)
    conn.commit()
    conn.close()

def insert_or_update_weights(username, bobot_data):
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    for row in bobot_data:
        kriteria, keterangan, bobot, jenis = row
        c.execute("""
            INSERT INTO bobot_kriteria (username, kriteria, keterangan, bobot, jenis)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, kriteria) DO UPDATE SET bobot = excluded.bobot
        """, (username, kriteria, keterangan, bobot, jenis))
    conn.commit()
    conn.close()

def save_weights_to_db(username, bobot_data):
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    for kriteria, keterangan, bobot, jenis in bobot_data:
        c.execute("""
            INSERT INTO bobot_kriteria (username, kriteria, keterangan, bobot, jenis)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, kriteria) DO UPDATE SET 
                bobot = excluded.bobot
        """, (username, kriteria, keterangan, bobot, jenis))
    conn.commit()
    conn.close()


def get_user_bobot(username):
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    c.execute("SELECT kriteria, keterangan, bobot, jenis FROM bobot_kriteria WHERE username = ?", (username,))
    result = c.fetchall()
    conn.close()
    return pd.DataFrame(result, columns=["Kriteria", "Keterangan", "Bobot", "Jenis"])


def insert_alternative(username, data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO alternatif (username, alternatif, c1, c2, c3, c4, c5, c6, c7, c8, c9)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    username, data["Alternatif"],
                    data["C1 (Bobot)"], data["C2 (Bobot)"], data["C3 (Bobot)"], data["C4 (Bobot)"],
                    data["C5 (Bobot)"], data["C6 (Bobot)"], data["C7 (Bobot)"], data["C8 (Bobot)"], data["C9 (Bobot)"]
                 ))
    conn.commit()
    conn.close()

def get_user_alternatives(username):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM alternatif WHERE username = ?", conn, params=(username,))
    conn.close()
    return df

def update_alternative(row_id, values):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE alternatif SET
            alternatif = ?, c1 = ?, c2 = ?, c3 = ?, c4 = ?, c5 = ?,
            c6 = ?, c7 = ?, c8 = ?, c9 = ?
        WHERE id = ?
    """, (*values, row_id))  # <-- harusnya values = 10 elemen, row_id ditambahkan di akhir
    conn.commit()
    conn.close()


def delete_alternative(row_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM alternatif WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

def login_ui():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_user_credentials(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah.")

def register_ui():
    st.header("Register")
    new_username = st.text_input("Buat Username")
    new_password = st.text_input("Buat Password", type="password")
    if st.button("Daftar"):
        if new_username and new_password:
            if user_exists(new_username):
                st.error("Username sudah terdaftar.")
            else:
                save_user_to_db(new_username, new_password)
                st.success("Registrasi berhasil! Silakan login.")
                st.rerun()
        else:
            st.warning("Harap isi semua kolom.")

def get_alternatif_user(username):
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    c.execute("SELECT * FROM alternatif WHERE username = ?", (username,))
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]  # INI PENTING!
    conn.close()
    
    if rows:
        return pd.DataFrame(rows, columns=colnames)
    return pd.DataFrame()


def moora_calculation(df_alt, df_bobot):
    df = df_alt.copy()

    # Ambil nama alternatif dan data kriteria
    alt_names = df["Alternatif"]
    data = df.loc[:, "c1":"c9"].astype(float)

    # Normalisasi
    normal = data / np.sqrt((data**2).sum())

    # Bobot dari df_bobot
    bobot = df_bobot["Bobot"].values
    jenis = df_bobot["Jenis"].values

    # Hitung nilai terbobot
    terbobot = normal * bobot

    # Pisahkan benefit dan cost
    benefit_idx = [i for i, j in enumerate(jenis) if j.lower() == "benefit"]
    cost_idx = [i for i, j in enumerate(jenis) if j.lower() == "cost"]

    skor = terbobot.iloc[:, benefit_idx].sum(axis=1) - terbobot.iloc[:, cost_idx].sum(axis=1)

    hasil = pd.DataFrame({
        "Alternatif": alt_names,
        "Skor Akhir": skor
    })

    hasil = hasil.sort_values(by="Skor Akhir", ascending=False).reset_index(drop=True)
    return hasil

def init_laporan_db():
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS laporan_moora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            nama_alternatif TEXT,
            skor REAL
        )
    """)
    conn.commit()
    conn.close()

def save_laporan(username, df_hasil):
    conn = sqlite3.connect("alternatif.db")
    c = conn.cursor()
    c.execute("DELETE FROM laporan_moora WHERE username = ?", (username,))
    for _, row in df_hasil.iterrows():
        c.execute("INSERT INTO laporan_moora (username, nama_alternatif, skor) VALUES (?, ?, ?)",
                  (username, row["nama_alternatif"], row["Skor MOORA"]))
    conn.commit()
    conn.close()

def halaman_menu():
    menu = st.sidebar.selectbox("Pilih Menu", ["Home", "Daftar Konversi Kriteria", "Daftar Kriteria", "Daftar Alternatif", "Perhitungan MOORA", "Laporan", "Tentang"])
  
    if menu == "Home":
        st.header("Selamat Datang di Sistem Pendukung Keputusan Pemilihan Lokasi Peternakan Ayam di Kabupaten Semarang Menggunakan Metode MOORA")

    elif menu == "Daftar Konversi Kriteria":
        st.subheader("Daftar Konversi Kriteria")
        data = {
            "No": [1, 2, 3],
            "Jarak Dari Pemukiman": ["> 1.000 m", "500 m – 1.000 m", "< 500 m"],
            "Bobot": [3, 2, 1],
            "Keterangan": ["Sangat Sesuai", "Sesuai", "Tidak Sesuai"]
        }

        data1 = {
            "No": [1, 2, 3, 4],
            "Luas Lahan": ["> 38750 m²", "27500 m² – 38750 m²", "16250 m² – 27500 m²", "5000 - 16250 m²"], 
            "Bobot": [4, 3, 2, 1],
            "Keterangan": ["Sangat Banyak", "Banyak", "Sedikit", "Sangat Sedikit"]
        }

        data2 = {
            "No": [1, 2, 3, 4],
            "Jarak Sumber Air": ["<10 m", "10 m - 20 m", "20 m - 50 m", ">50 m"], 
            "Bobot": [4, 3, 2, 1],
            "Keterangan": ["Sangat Dekat", "Dekat", "Jauh", "Sangat Jauh"]
        }

        data3 = {
            "No": [1, 2, 3, 4],
            "Jarak Sumber Listrik": ["<10 m", "10 m - 20 m", "20 m - 30 m", ">30 m"], 
            "Bobot": [4, 3, 2, 1],
            "Keterangan": ["Sangat Dekat", "Dekat", "Jauh", "Sangat Jauh"]
        }

        data4 = {
            "No": [1, 2, 3, 4],
            "Jneis Permukaan Akses Jalan": ["Jalan Sudah Bersapal", "Jalan Menggunakan Beton", "Jalan Makadam", "Jalan Masih Berupa Tanah Lempung"], 
            "Bobot": [4, 3, 2, 1],
            "Keterangan": ["Sangat Baik", "Baik", "Tidak Baik", "Sangat Tidak Baik"]
        }

        data5 = {
            "No": [1, 2, 3],
            "Lebar Jalan": [">6 m", "3 m - 6 m", "<3 m"], 
            "Bobot": [3, 2, 1],
            "Keterangan": ["Sangat Disarankan", "Disarankan", "Tidak Disarankan"]
        }

        data6 = {
            "No": [1, 2],
            "Kepemilikan Lahan": ["Lahan Sendiri", "Menyewa Lahan"], 
            "Bobot": [2, 1],
            "Keterangan": ["Lebih Baik", "Kurang Baik"]
        }

        data7 = {
            "No": [1, 2, 3],
            "Jarak Lokasi Dengan Jalan Utama": [">100 m", "25 m - 100 m", "<25 m"], 
            "Bobot": [3, 2, 1],
            "Keterangan": ["Sangat Sesuai", "Sesuai", "Tidak Sesuai"]
        }

        data8 = {
            "No": [1, 2, 3],
            "Jarak Lokasi Dengan Peternakan Lain": [">1.000 m", "500 m - 1.000 m", "<500 m"], 
            "Bobot": [3, 2, 1],
            "Keterangan": ["Sangat Sesuai", "Sesuai", "Tidak Sesuai"]
        }

        #Konversi kedalam DataFrame
        df = pd.DataFrame(data)
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        df3 = pd.DataFrame(data3)
        df4 = pd.DataFrame(data4)
        df5 = pd.DataFrame(data5)
        df6 = pd.DataFrame(data6)
        df7 = pd.DataFrame(data7)
        df8 = pd.DataFrame(data8)

        #Tampilan Tabel
        st.subheader("Tabel Jarak dari Pemukiman")
        st.table(df)
        st.subheader("Tabel Luas Lahan")
        st.table(df1)
        st.subheader("Tabel Jarak Sumber Air")
        st.table(df2)
        st.subheader("Tabel Jarak Sumber Listrik")
        st.table(df3)
        st.subheader("Tabel Jenis Permukaan Akses Jalan")
        st.table(df4)
        st.subheader("Tabel Lebar Jalan")
        st.table(df5)
        st.subheader("Tabel Kepemilikan Lahan")
        st.table(df6)
        st.subheader("Tabel Jarak Lokasi Dengan Jalan Utama")
        st.table(df7)
        st.subheader("Tabel Jarak Lokasi Dengan Peternakan Lain")
        st.table(df8)


    elif menu == "Daftar Kriteria":
        st.subheader("Daftar Kriteria")

        init_bobot_db()

        kriteria_list = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9']
        keterangan_list = ['Jarak Dari Pemukiman', 'Luas Lahan', 'Jarak Sumber Air', 'Jarak Sumber Listrik', 
                        'Jenis Permukaan Akses Jalan', 'Lebar Jalan', 'Kepemilikan Lahan', 
                        'Jarak dengan Jalan Utama', 'Jarak dengan Peterakan Lain']
        jenis_list = ['Benefit', 'Benefit', 'Cost', 'Cost', 'Benefit', 'Benefit', 'Cost', 'Benefit', 'Benefit']

        username = st.session_state["username"]
        
        # Ambil data lama dari database
        df_existing = get_user_bobot(st.session_state["username"])

        bobot_input = []

        with st.form("form_bobot_kriteria"):
            st.write("Masukkan atau ubah nilai bobot untuk masing-masing kriteria:")

            for i in range(len(kriteria_list)):
                # Jika data bobot sudah tersimpan, ambil nilai bobot lama
                if not df_existing.empty and kriteria_list[i] in df_existing["Kriteria"].values:
                    nilai_lama = df_existing.loc[df_existing["Kriteria"] == kriteria_list[i], "Bobot"].values[0]
                    nilai_lama = round(float(nilai_lama), 1)
                else:
                    nilai_lama = 0.0  # default

                val = st.number_input(f"{kriteria_list[i]} - {keterangan_list[i]}", min_value=0.0,max_value=1.0, step=0.1, format="%.1f", value=nilai_lama, key=f"bobot_{i}")
                bobot_input.append(val)

            simpan_bobot = st.form_submit_button("Simpan Bobot")

        if simpan_bobot:
            total = sum(bobot_input)
            if total == 0:
                st.warning("Total bobot tidak boleh 0.")
            else:
                normalized_weights = [round(x / total, 3) for x in bobot_input]

                # Buat list tuple [(kriteria, keterangan, bobot, jenis), ...]
                bobot_data = []
                for i in range(len(kriteria_list)):
                    bobot_data.append((
                    kriteria_list[i],
                    keterangan_list[i],
                    normalized_weights[i],
                    jenis_list[i]
                ))

                save_weights_to_db(st.session_state["username"], bobot_data)
                st.success("Bobot berhasil disimpan.")

        # Tampilkan hasil data setelah disimpan
        df_show = get_user_bobot(st.session_state["username"])
        if not df_show.empty:
            st.write("### Tabel Bobot yang Telah Disimpan:")
            st.dataframe(df_show, use_container_width=True)



    elif menu == "Daftar Alternatif":
        st.subheader ("Input Data Alternatif")
        #Membuat list untuk menyimpan data input
        if "data" not in st.session_state:
            st.session_state.data=[]

        def konversi_C1(nilai):
            if nilai > 1000:
                return 3
            elif 500 <= nilai <= 1000:
                return 2
            else:
                return 1
        
        def konversi_C2(nilai):
            if nilai > 38750:
                return 4
            elif 27500 <= nilai <= 38750:
                return 3
            elif 16250 <= nilai < 27500:
                return 2
            else:
                return 1
        
        def konversi_C3(nilai):
            if nilai < 10:
                return 4
            elif 10 <= nilai <= 20:
                return 3
            elif 20 <= nilai <= 50:
                return 2
            else:
                return 1
            
        def konversi_C4(nilai):
            if nilai < 10:
                return 4
            elif 10 <= nilai <= 20:
                return 3
            elif 20 <= nilai <= 30:
                return 2
            else:
                return 1
            
        def konversi_C5(nilai):
            if nilai == "Aspal":
                return 4
            elif nilai == "Beton":
                return 3
            elif nilai == "Makadam":
                return 2
            elif nilai == "Lempung":
                return 1
            
        def konversi_C6(nilai):
            if nilai > 6:
                return 3
            elif 3 <= nilai <= 6:
                return 2
            else:
                return 1
        
        def konversi_C7(nilai):
            if nilai == "Lahan Sendiri":
                return 2
            elif nilai == "Menyewa Lahan":
                return 1
            
        def konversi_C8(nilai):
            if nilai > 100:
                return 3
            elif 25 <= nilai <= 100:
                return 2
            else:
                return 1
            
        def konversi_C9(nilai):
            if nilai > 1000:
                return 3
            elif 500 <= nilai <= 1000:
                return 2
            else:
                return 1

        with st.form("form_input"):
            alt = st.text_input("Alternatif (Masukkan Nama Daerah Lokasi Berada)")
            c1 = st.number_input("Jarak Dari Pemukiman (m)", min_value=0)
            c2 = st.number_input("Luas Lahan (m2)", min_value=0)
            c3 = st.number_input("Jarak Sumber Air (m)", min_value=0)
            c4 = st.number_input("Jarak Sumber Listrik (m)", min_value=0)
            c5 = st.selectbox("Jenis Permukaan Jalan", ["Aspal", "Beton", "Makadam", "Lempung"])
            c6 = st.number_input("Lebar Jalan (m)", min_value=0.0, step=0.5)
            c7 = st.selectbox("Kepemilikan Lahan", ["Lahan Sendiri", "Menyewa Lahan"])
            c8 = st.number_input("Jarak dengan Jalan Utama (jalan kampung) (m)", min_value=0)
            c9 = st.number_input("Jarak dengan Peternakan Lain (m)", min_value=0)
            
            tambah = st.form_submit_button("Tambahkan Data")
            
        if tambah:
            if not alt.strip():
                st.warning("Harap isi nama lokasi.")
            else:
                try:
                    new_entry = {              
                        "Alternatif": alt,
                        "Jarak Dari Pemukiman (m)": c1, "C1 (Bobot)": konversi_C1(c1),
                        "Luas Lahan (m²)": c2, "C2 (Bobot)": konversi_C2(c2),
                        "Jarak Sumber Air (m)": c3, "C3 (Bobot)": konversi_C3(c3),
                        "Jarak Sumber Listrik (m)": c4, "C4 (Bobot)": konversi_C4(c4), 
                        "Jenis Permukaan Akses Jalan": c5, "C5 (Bobot)": konversi_C5(c5),
                        "Lebar Jalan (m)": c6, "C6 (Bobot)": konversi_C6(c6),
                        "Kepemilikan Lahan": c7, "C7 (Bobot)": konversi_C7(c7),
                        "Jarak Dengan Jalan Utama (m)": c8, "C8 (Bobot)": konversi_C8(c8),
                        "Jarak Dengan Peternakan Lain (m)": c9, "C9 (Bobot)": konversi_C9(c9), 
                    }
            
                    insert_alternative(st.session_state["username"], new_entry)
                    st.session_state["berhasil_tambah"] = True
                    st.rerun()
        
                except Exception as e:
                    st.warning(f"Harap isi semua nilai dengan benar. Error: {e}")

        df_edit = get_user_alternatives(st.session_state["username"])
        if not df_edit.empty:
            st.write("### Data yang telah dimasukkan:")
            st.session_state["edited_ids"] = df_edit["id"].tolist()
            df_display = df_edit[["alternatif", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9"]]
            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True)

            if st.session_state.get("berhasil_simpan"):
                st.success("Perubahan berhasil disimpan.")
                # Hapus flag supaya tidak muncul terus
                del st.session_state["berhasil_simpan"]

            if st.button("Simpan Perubahan"):
                for i, (_, row) in enumerate(edited_df.iterrows()):
                    row_id = st.session_state["edited_ids"][i]
                    values = [
                        row["alternatif"], row["c1"], row["c2"], row["c3"], row["c4"],
                        row["c5"], row["c6"], row["c7"], row["c8"], row["c9"]
                    ]
                    update_alternative(row_id, values)

                st.session_state["berhasil_simpan"] = True
                st.rerun()

            if st.button("Hapus Semua Data"):
                for row_id in st.session_state["edited_ids"]:
                    delete_alternative(row_id)
                st.success("Semua data alternatif telah dihapus.")
                st.rerun()

    elif menu == "Perhitungan MOORA":
        st.header ("Perhitungan MOORA")

        username = st.session_state["username"]
        df_alt = get_alternatif_user(username)
        df_bobot = get_user_bobot(username)

        if df_alt.empty or df_bobot.empty:
            st.warning("Data alternatif atau bobot kriteria belum lengkap.")
        else:
            # Rename kolom untuk kemudahan
            if "alternatif" in df_alt.columns:
                df_alt.rename(columns={"alternatif": "Alternatif"}, inplace=True)

            # Buat salinan dataframe tanpa kolom id dan username
            df_alt_clean = df_alt.drop(columns=["id", "username"])

            st.write("### Data Alternatif")
            st.dataframe(df_alt_clean)

            # Ambil bobot & jenis dari bobot kriteria
            weights = df_bobot["Bobot"].values
            types = np.where(df_bobot["Jenis"] == "Benefit", 1, -1)

            # Ambil matrix dari kolom C1-C9
            matrix = df_alt_clean.iloc[:, 1:].values.tolist()  # kolom ke-1 dst adalah C1–C9
            alternatives = df_alt_clean["Alternatif"].tolist()

            if st.button("Hitung MOORA"):
                results = moora_calculation(df_alt, df_bobot)
                if results is not None:
                    st.write("### Hasil Perhitungan MOORA:")
                    st.dataframe(results)

                    best_alternative = results.iloc[0]["Alternatif"]
                    best_score = results.iloc[0]["Skor Akhir"]

                    st.success(f"Alternatif terbaik adalah **{best_alternative}** dengan skor tertinggi yaitu **{best_score}**")

                    # Simpan hasil ke session_state
                    st.session_state["moora_results"] = results
                    st.session_state["best_alternative"] = best_alternative
                    st.session_state["best_score"] = best_score

       
    elif menu == "Laporan":
        st.header("Hasil Laporan Perhitungan Alternatif Terbaik Menggunakan MOORA")
        
        if "moora_results" in st.session_state:
            st.dataframe(st.session_state["moora_results"])
            
            # Ambil data terbaik dari session_state
            best_alternative = st.session_state["best_alternative"]
            best_score = st.session_state["best_score"]
            
            st.success(f"Berdasarkan analisis yang dilakukan, alternatif terbaik yang diperoleh adalah **{best_alternative}** dengan skor tertinggi yaitu **{best_score}**. Hasil ini menunjukkan bahwa **{best_alternative}** memenuhi beberapa kriteria penting untuk pembangunan peternakan ayam. Dengan analisis berbasis skor ini, keputusan yang diambil lebih objektif dan terukur. Langkah selanjutnya adalah melakukan survei lapangan serta memastikan aspek regulasi dan perizinan agar pembangunan peternakan dapat berjalan lancar sesuai aturan yang berlaku.")
        else:
            st.warning("Belum ada perhitungan yang dilakukan. Silakan hitung MOORA terlebih dahulu.")

    elif menu == "Tentang":
        st.header("Tentang Aplikasi")
        st.write("Aplikasi Sistem Pendukung Keputusan (SPK) adalah aplikasi berbasis komputer yang dirancang untuk membantu proses pengambilan keputusan, terutama dalam situasi yang kompleks atau tidak terstruktur."
        " Sistem Pendukung Keputusan berfungsi sebagai alat bantu yang menyediakan data, analisis, atau rekomendasi untuk mendukung pengambilkan keputusan dalam memilih solusi terbaik. "
        " Aplikasi yang saya buat ini merupakan aplikasi yang yang dibuat untuk para peternak ayam pemula yang ingin mendirikan peternakan ayam, namun bingung dalam menentukan lokasi yang cocok untuk di dirikannya peternakan tersebut."
        " Dengan adanya permasalahan tersebut, saya membuat aplikasi ini untuk menyelesaikan dan memberikan solusi terkait kebingungan yang dialami."
        " Sistem ini menggunakan metode MOORA yang digunakan untuk melakukan analisis multi-kriteria dalam menentukan lokasi yang paling optimal berdasarkan beberapa parameter yang telah saya tentukan."
        " Metode Multi-Objective Optimization on the Basis of Ratio Analysis) bekerja dengan cara membandingkan setiap alternatif berdasarkan kriteria yang relevan dengan pemilihan lokasi peternakan ayam."
        " Hasil dari analisis tersebut akan memberikan peringkat dari setiap alternatif lokasi, sehingga para peternak ayam pemula dapat mengambil keputusan dengan lebih mudah dan didasarkan pada data yang akurat."
        " Dengan aplikasi ini, diharapkan para peternak dapat mengoptimalkan peluang keberhasilan dalam mendirikan peternakan ayam yang produktif dan efisien.")


def main():
    st.set_page_config(page_title="SPK MOORA", layout="wide")
    init_db()
    init_user_db()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        pilihan = st.radio("Silakan Login atau Register", ["Login", "Register"])
        if pilihan == "Login":
            login_ui()
        else:
            register_ui()
        return
    
    halaman_menu()
if __name__ == "__main__":
    main()
