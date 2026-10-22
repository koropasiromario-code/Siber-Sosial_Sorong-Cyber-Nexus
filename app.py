import re
from io import BytesIO
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import networkx as nx

TEAM = "Sorong Cyber Nexus"
st.set_page_config(page_title="Siber Sosial | Sorong Cyber Nexus", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.hero {padding: 1.3rem 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#10253f,#145b67); color: white; margin-bottom: 1rem;}
.hero h1 {margin: 0; font-size: 2rem;}
.hero p {margin: .45rem 0 0 0; color: #d8e7ee;}
.small-muted {color: #6b7280; font-size: .86rem;}
div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.25); padding: 12px; border-radius: 12px;}
</style>
<div class="hero">
  <h1>🛡️ SIBER SOSIAL</h1>
  <p>Pemantauan dan analisis ruang siber sosial · Disinformasi · Sentimen · Koordinasi · Peringatan dini</p>
  <p><b>Tim pengembang: Sorong Cyber Nexus</b></p>
</div>
""", unsafe_allow_html=True)

st.caption("MVP analisis berbasis data yang Anda unggah. Skor adalah indikator awal untuk triase, bukan bukti niat, identitas bot, atau kebenaran sebuah klaim.")

REQUIRED = ["timestamp", "platform", "account", "text"]
OPTIONAL_DEFAULTS = {"likes": 0, "shares": 0, "replies": 0, "reply_to": ""}

POSITIVE = set("bagus baik hebat setuju dukung aman sukses benar terpercaya membantu positif senang bangga damai".split())
NEGATIVE = set("buruk jahat gagal bohong hoaks hoax bahaya rusak kecewa marah benci korup curang ancaman negatif".split())
SENSATIONAL = ["sebarkan", "viralkan", "jangan percaya", "pasti", "100%", "terbukti", "rahasia", "media diam", "bangunkan", "darurat", "konspirasi", "dibungkam", "bagikan sebelum dihapus"]
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
MENTION_RE = re.compile(r"@([A-Za-z0-9_.-]+)")

def sentiment(text):
    words = re.findall(r"\b[\w'-]+\b", str(text).lower())
    pos = sum(w in POSITIVE for w in words)
    neg = sum(w in NEGATIVE for w in words)
    if pos > neg: return "Positif"
    if neg > pos: return "Negatif"
    return "Netral"

def analyze(df):
    out = df.copy()
    out["text"] = out["text"].fillna("").astype(str)
    out["account"] = out["account"].fillna("akun_tidak_diketahui").astype(str)
    out["platform"] = out["platform"].fillna("Tidak diketahui").astype(str)
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out["sentimen"] = out["text"].apply(sentiment)
    out["teks_normal"] = out["text"].str.lower().str.replace(r"https?://\S+|www\.\S+", "", regex=True).str.replace(r"[^a-z0-9\s]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    out["kata_sensasional"] = out["text"].str.lower().apply(lambda t: sum(term in t for term in SENSATIONAL))
    out["ada_url"] = out["text"].apply(lambda t: bool(URL_RE.search(t)))
    out["panjang_teks"] = out["text"].str.len()
    out["indikasi_disinformasi"] = out.apply(lambda r: min(100, r["kata_sensasional"]*18 + (12 if "!!!" in r["text"] else 0) + (8 if r["text"].isupper() and len(r["text"])>12 else 0)), axis=1)
    # coordination indicators: repeated normalized text and account activity volume
    dup_counts = out["teks_normal"].map(out["teks_normal"].value_counts()).fillna(0)
    account_counts = out["account"].map(out["account"].value_counts()).fillna(0)
    out["teks_berulang"] = dup_counts
    out["jumlah_post_akun"] = account_counts
    out["indikasi_koordinasi"] = ((dup_counts >= 2).astype(int)*45 + (account_counts >= 8).astype(int)*30 + (out["kata_sensasional"] >= 2).astype(int)*15).clip(upper=100)
    out["indikasi_bot"] = ((account_counts >= 10).astype(int)*45 + (out["panjang_teks"] < 25).astype(int)*10 + (dup_counts >= 3).astype(int)*35 + (out["timestamp"].isna()).astype(int)*10).clip(upper=100)
    out["level_perhatian"] = out[["indikasi_disinformasi","indikasi_koordinasi","indikasi_bot"]].max(axis=1).apply(lambda n: "Tinggi" if n >= 60 else ("Sedang" if n >= 30 else "Rendah"))
    return out

def demo_data():
    rows = [
    ("2026-10-22 08:02","X","papua_update","Pemerintah daerah mengumumkan layanan kesehatan keliling mulai pekan ini",14,4,2,""),
    ("2026-10-22 08:05","Facebook","warga_sorong","Senang ada layanan kesehatan, semoga membantu warga",22,3,5,"papua_update"),
    ("2026-10-22 08:11","X","info_cepat","SEBARKAN!!! Media diam, ada kabar yang katanya disembunyikan!!!",42,29,8,""),
    ("2026-10-22 08:12","X","info_cepat2","SEBARKAN!!! Media diam, ada kabar yang katanya disembunyikan!!!",8,11,1,"info_cepat"),
    ("2026-10-22 08:13","X","info_cepat3","SEBARKAN!!! Media diam, ada kabar yang katanya disembunyikan!!!",4,9,0,"info_cepat"),
    ("2026-10-22 08:18","Instagram","sorong_kita","Mari cek sumber resmi sebelum membagikan kabar yang belum terbukti",31,8,4,""),
    ("2026-10-22 08:25","Facebook","suara_warga","Jalan rusak dan berbahaya, semoga segera diperbaiki",11,2,7,""),
    ("2026-10-22 08:31","X","akun_aktif","Bagikan sebelum dihapus, ini 100% terbukti, jangan percaya pihak lain",65,38,14,""),
    ("2026-10-22 08:34","X","akun_aktif","Bagikan sebelum dihapus, ini 100% terbukti, jangan percaya pihak lain",19,17,4,"akun_aktif"),
    ("2026-10-22 08:40","TikTok","papua_muda","Bangga dengan komunitas yang membantu lingkungan",88,13,6,""),
    ("2026-10-22 09:02","Facebook","warga_timur","Informasi ini belum jelas sumbernya, mari verifikasi dulu",7,1,2,""),
    ("2026-10-22 09:08","X","pantau_kota","Kabar darurat ini pasti benar, viralkan sekarang!!!",71,44,12,""),
    ("2026-10-22 09:10","X","pantau_kota2","Kabar darurat ini pasti benar, viralkan sekarang!!!",16,21,3,"pantau_kota"),
    ("2026-10-22 09:15","Instagram","komunitas_hijau","Aksi bersih pantai berjalan sukses, terima kasih semua",45,9,5,""),
    ("2026-10-22 09:24","Facebook","kritik_warga","Kecewa karena jalan rusak belum diperbaiki",18,3,8,""),
    ("2026-10-22 09:40","X","cek_fakta_id","Belum ada bukti kuat untuk klaim tersebut. Periksa sumber primer.",56,19,9,""),
    ("2026-10-22 09:52","X","papua_update","Pendaftaran kegiatan komunitas dibuka sampai Jumat",12,2,1,""),
    ("2026-10-22 10:01","TikTok","akun_aktif","Info penting",2,0,0,""),
    ("2026-10-22 10:03","TikTok","akun_aktif","Info penting",3,0,0,""),
    ("2026-10-22 10:04","TikTok","akun_aktif","Info penting",1,0,0,""),
    ]
    return pd.DataFrame(rows, columns=["timestamp","platform","account","text","likes","shares","replies","reply_to"])

with st.sidebar:
    st.header("Sumber data")
    uploaded = st.file_uploader("Unggah CSV", type=["csv"], help="Kolom wajib: timestamp, platform, account, text. Kolom opsional: likes, shares, replies, reply_to.")
    use_demo = st.toggle("Gunakan data demo", value=uploaded is None)
    st.divider()
    st.subheader("Filter")
    st.caption("Filter berlaku pada seluruh dashboard.")
    st.markdown("**Privasi:** gunakan data yang sah untuk Anda proses. MVP ini tidak mengambil data media sosial secara otomatis.")

if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"CSV tidak dapat dibaca: {e}")
        st.stop()
elif use_demo:
    raw = demo_data()
else:
    st.info("Unggah file CSV atau aktifkan data demo untuk mulai.")
    st.stop()

missing = [c for c in REQUIRED if c not in raw.columns]
if missing:
    st.error("Kolom wajib tidak ditemukan: " + ", ".join(missing))
    st.write("Kolom wajib:", ", ".join(REQUIRED))
    st.stop()
for col, default in OPTIONAL_DEFAULTS.items():
    if col not in raw.columns: raw[col] = default
df = analyze(raw)
platforms = sorted(df["platform"].dropna().unique().tolist())
selected_platforms = st.sidebar.multiselect("Platform", platforms, default=platforms)
levels = st.sidebar.multiselect("Level perhatian", ["Tinggi","Sedang","Rendah"], default=["Tinggi","Sedang","Rendah"])
date_min = df["timestamp"].min()
date_max = df["timestamp"].max()
if pd.notna(date_min) and pd.notna(date_max):
    date_range = st.sidebar.date_input("Rentang tanggal", value=(date_min.date(), date_max.date()))
    if isinstance(date_range, tuple) and len(date_range)==2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
        df = df[df["timestamp"].isna() | ((df["timestamp"] >= start) & (df["timestamp"] < end))]
df = df[df["platform"].isin(selected_platforms) & df["level_perhatian"].isin(levels)].copy()

if df.empty:
    st.warning("Tidak ada data yang cocok dengan filter. Ubah filter di panel kiri.")
    st.stop()

# Overview
total = len(df)
high = int((df["level_perhatian"]=="Tinggi").sum())
negative = int((df["sentimen"]=="Negatif").sum())
accounts = df["account"].nunique()
c1,c2,c3,c4 = st.columns(4)
c1.metric("Konten dianalisis", f"{total:,}")
c2.metric("Perlu perhatian tinggi", f"{high:,}", help="Skor heuristik, bukan kepastian hoaks/bot.")
c3.metric("Akun unik", f"{accounts:,}")
c4.metric("Sentimen negatif", f"{negative:,}", f"{negative/max(total,1):.0%} dari konten")
tabs = st.tabs(["Ringkasan", "Disinformasi", "Bot & Koordinasi", "Jaringan Sosial", "Peringatan Dini", "Data & Ekspor"])

with tabs[0]:
    left,right = st.columns(2)
    with left:
        counts = df["sentimen"].value_counts().reindex(["Positif","Netral","Negatif"], fill_value=0).rename_axis("Sentimen").reset_index(name="Jumlah")
        st.subheader("Peta sentimen")
        st.plotly_chart(px.pie(counts, names="Sentimen", values="Jumlah", hole=.55), use_container_width=True)
    with right:
        st.subheader("Aktivitas dari waktu ke waktu")
        timed = df.dropna(subset=["timestamp"]).set_index("timestamp").resample("15min").size().reset_index(name="Jumlah")
        if len(timed):
            st.plotly_chart(px.line(timed, x="timestamp", y="Jumlah", markers=True), use_container_width=True)
        else: st.info("Timestamp tidak dapat dibaca; grafik waktu tidak tersedia.")
    st.subheader("Topik/kata yang sering muncul")
    tokens = []
    stop = set("yang dan di ke dari untuk ini itu ada dengan pada tidak akan atau agar sudah belum kami saya anda mereka kita adalah dalam juga bisa jadi".split())
    for txt in df["text"]:
        tokens += [w for w in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", str(txt).lower()) if w not in stop]
    top = pd.DataFrame(Counter(tokens).most_common(12), columns=["Kata","Frekuensi"])
    if len(top): st.plotly_chart(px.bar(top, x="Frekuensi", y="Kata", orientation="h"), use_container_width=True)

with tabs[1]:
    st.subheader("Prioritas verifikasi klaim")
    st.info("Skor dihitung dari kata sensasional dan pola bahasa tertentu. Ini bukan fact-check otomatis dan tidak menentukan benar/salah.")
    claims = df.sort_values("indikasi_disinformasi", ascending=False).copy()
    claims["indikasi_disinformasi"] = claims["indikasi_disinformasi"].round().astype(int)
    st.dataframe(claims[["timestamp","platform","account","text","indikasi_disinformasi","ada_url","level_perhatian"]], use_container_width=True, hide_index=True)
    st.markdown("**Alur tindak lanjut yang disarankan:** cari sumber primer → cek tanggal/konteks → bandingkan dengan sumber independen → catat keputusan verifikasi.")

with tabs[2]:
    st.subheader("Indikator perilaku akun")
    st.caption("Tidak ada indikator tunggal yang membuktikan akun adalah bot atau buzzer. Akun manusia juga dapat mengunggah berulang.")
    acct = df.groupby("account", as_index=False).agg(
        jumlah_post=("text","size"), teks_unik=("teks_normal","nunique"),
        total_interaksi=("likes","sum"), rata_skor_bot=("indikasi_bot","mean"),
        rata_skor_koordinasi=("indikasi_koordinasi","mean")
    )
    acct["rata_skor_bot"] = acct["rata_skor_bot"].round(1)
    acct["rata_skor_koordinasi"] = acct["rata_skor_koordinasi"].round(1)
    st.dataframe(acct.sort_values(["rata_skor_koordinasi","rata_skor_bot"], ascending=False), use_container_width=True, hide_index=True)
    repeated = df[df["teks_berulang"] >= 2].sort_values("teks_berulang", ascending=False)
    st.markdown("**Konten berulang**")
    if repeated.empty: st.success("Tidak ditemukan teks berulang dalam data terfilter.")
    else: st.dataframe(repeated[["timestamp","account","text","teks_berulang","indikasi_koordinasi"]], use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Grafik hubungan akun")
    G = nx.Graph()
    for _, r in df.iterrows():
        a = str(r["account"])
        G.add_node(a)
        target = str(r.get("reply_to","")).strip()
        if target and target.lower() not in ["nan","none"] and target != a:
            G.add_edge(a, target, relation="reply")
    # Add coordination links for accounts sharing exact normalized text
    groups = df[df["teks_normal"].astype(str).str.len() > 0].groupby("teks_normal")["account"].apply(lambda s: sorted(set(s)))
    for members in groups:
        if len(members) > 1:
            for i in range(len(members)):
                for j in range(i+1, len(members)):
                    G.add_edge(members[i], members[j], relation="teks_serupa")
    if G.number_of_nodes():
        pos = nx.spring_layout(G, seed=17)
        edge_x, edge_y = [], []
        for u,v in G.edges():
            x0,y0=pos[u]; x1,y1=pos[v]
            edge_x += [x0,x1,None]; edge_y += [y0,y1,None]
        node_x=[pos[n][0] for n in G.nodes()]
        node_y=[pos[n][1] for n in G.nodes()]
        sizes = {r["account"]: 12 + min(25, int(r["jumlah_post"])*3) for _,r in acct.iterrows()}
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=edge_x,y=edge_y,mode="lines",line=dict(width=1),hoverinfo="none"))
        fig.add_trace(go.Scatter(x=node_x,y=node_y,mode="markers+text",text=list(G.nodes()),textposition="top center",
            marker=dict(size=[sizes.get(n,12) for n in G.nodes()]),hovertext=list(G.nodes()),hoverinfo="text"))
        fig.update_layout(showlegend=False, height=550, margin=dict(l=10,r=10,t=20,b=10), xaxis=dict(visible=False), yaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{G.number_of_nodes()} simpul · {G.number_of_edges()} hubungan. Hubungan berasal dari reply_to dan kesamaan teks; bukan bukti koordinasi yang disengaja.")
    else: st.info("Belum ada hubungan untuk divisualisasikan.")

with tabs[4]:
    st.subheader("Early Warning Isu Viral")
    if df["timestamp"].notna().sum() >= 2:
        hourly = df.dropna(subset=["timestamp"]).set_index("timestamp").resample("15min").size().reset_index(name="volume")
        hourly["rata_bergerak"] = hourly["volume"].rolling(4, min_periods=1).mean()
        baseline = hourly["volume"].median()
        threshold = max(3, baseline * 2.5)
        hourly["peringatan"] = hourly["volume"] >= threshold
        st.plotly_chart(px.bar(hourly, x="timestamp", y="volume", color="peringatan", title="Volume konten per 15 menit"), use_container_width=True)
        if hourly["peringatan"].any():
            st.warning(f"Ada {int(hourly['peringatan'].sum())} interval dengan volume di atas ambang awal ({threshold:.1f} konten/15 menit). Tinjau konteks sebelum mengambil tindakan.")
        else: st.success("Belum ada lonjakan volume yang melewati ambang awal pada data terfilter.")
    else:
        st.info("Diperlukan minimal dua timestamp valid untuk analisis tren.")
    st.markdown("**Isu prioritas saat ini**")
    priority = df.assign(interaksi=pd.to_numeric(df["likes"],errors="coerce").fillna(0)+pd.to_numeric(df["shares"],errors="coerce").fillna(0)+pd.to_numeric(df["replies"],errors="coerce").fillna(0))
    st.dataframe(priority.sort_values(["level_perhatian","interaksi"], ascending=[True,False])[["timestamp","platform","account","text","level_perhatian","interaksi"]].head(15), use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Data hasil analisis")
    st.write(f"Menampilkan {len(df)} baris setelah filter.")
    visible_cols = ["timestamp","platform","account","text","sentimen","indikasi_disinformasi","indikasi_bot","indikasi_koordinasi","level_perhatian","likes","shares","replies","reply_to"]
    st.dataframe(df[visible_cols], use_container_width=True, hide_index=True)
    csv_bytes = df[visible_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Unduh hasil analisis (CSV)", data=csv_bytes, file_name="siber_sosial_hasil_analisis.csv", mime="text/csv")
    sample = pd.DataFrame(columns=REQUIRED + list(OPTIONAL_DEFAULTS.keys()))
    st.download_button("⬇️ Unduh template CSV", data=sample.to_csv(index=False).encode("utf-8-sig"), file_name="template_siber_sosial.csv", mime="text/csv")

st.divider()
st.markdown(f"<div style='text-align:center;color:#7b8794;font-size:.85rem'>Siber Sosial MVP · Dikembangkan oleh <b>{TEAM}</b> · Analisis berbasis heuristik, gunakan peninjauan manusia.</div>", unsafe_allow_html=True)
