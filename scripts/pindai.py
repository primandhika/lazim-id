#!/usr/bin/env python3
"""Pemindai kalke dan kohesi untuk naskah berbahasa Indonesia (skill lazim-id).

Hasilnya kandidat, bukan putusan. Setiap temuan perlu ditimbang dalam konteksnya, dan
pemindai pasti melewatkan sebagian kalke. Baca ulang naskah tetap wajib.

Pemakaian:
    python3 pindai.py naskah.md [bab2.md berkas.docx ...]   # pindai berkas (.md, .txt, .docx)
    python3 pindai.py -                                      # baca dari stdin
    python3 pindai.py --ringkas folder/*.md                  # jumlah temuan per kode per berkas
    python3 pindai.py --kode LZ-01,LZ-03 naskah.md           # hanya kode tertentu
    python3 pindai.py --konteks naskah.md                    # tampilkan juga kalimat utuhnya
    python3 pindai.py --banding asli.md hasil.md             # sitasi, angka, kutipan yang berubah
    python3 pindai.py --tes                                  # uji mandiri

Kode temuan:
    LZ-01 pelaku   benda mati, dokumen, atau gagasan sebagai pelaku verba tindakan manusia
    LZ-02 gerund   kegiatan (verba me-/ber-) sebagai subjek verba aktif lain
    LZ-03 kabur    subjek tanpa nomina: sebagian lain, ada pula yang, yang lain lagi
    LZ-04 sanding  sanding kata atau istilah terjemahan
    LZ-05 kohesi   tiga kalimat atau lebih berturut-turut tanpa perangkai atau kata rujuk
    LZ-06 monoton  kalimat-kalimat dalam satu paragraf dibuka dengan kata yang sama
    LZ-07 serapan  serapan Inggris yang punya padanan Indonesia yang lebih akrab

Teks yang dilewati: blok kode, kode sebaris, URL, bagian Daftar Pustaka/Rujukan/Referensi,
baris yang diawali "Sebelum:" atau "Kalke", dan wilayah antara <!-- lazim:abaikan --> dan
<!-- lazim:lanjut -->. Pada .docx, nomor baris adalah nomor paragraf.

Kode keluar: 1 bila ada temuan (atau, pada --banding, ada sitasi/angka yang berubah), 0 bila tidak.
"""
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

# ----------------------------------------------------------------------------- kosakata

SUBJEK = set("""
tabel gambar foto diagram grafik bagan peta kotak bab buku bagian subbab artikel makalah laporan
judul data hasil temuan kajian penelitian studi tinjauan survei analisis rekaman video tayangan
salindia aplikasi teknologi media platform laman situs ponsel perangkat alat fitur sistem program
kebijakan kurikulum model teknik metode strategi pendekatan kerangka teori konsep prinsip gagasan
rumusan definisi uraian penjelasan contoh ilustrasi kegiatan latihan tugas pembelajaran siklus
langkah tahap proses rubrik instrumen pengalaman situasi kondisi kenyataan fakta pertanyaan
pembedaan perbandingan kebiasaan pola struktur penanda kalimat istilah pesan suara jeda intonasi
gestur postur ekspresi unit modul materi sesi pujian refleksi evaluasi pemantauan penilaian
topik isi ringkasan rangkuman kutipan cerita narasi argumen bukti diskusi debat wawancara
presentasi pidato percakapan obrolan dialog umpan kesadaran pemahaman sintesis ejaan kbbi kamus
pedoman aturan undang-undang peraturan
""".split())
SUBJEK_FRASA = ["hal ini", "hal itu", "hal tersebut"]

VERBA_PELAKU = set("""
memperlihatkan menunjukkan menggambarkan merangkum merinci menyandingkan menghimpun menyajikan
menjelaskan mengingatkan menyoroti menekankan menegaskan menawarkan mengajak mengundang membantu
memaksa mendorong memungkinkan membuka membawa memberi memberikan menyediakan menemukan
membuktikan mengungkapkan mengungkap menyimpan memperkuat menambahkan menangkap melatih mengajarkan
berusaha menyatakan mencatat menetapkan menempatkan memadukan merangkai menyarankan menganjurkan
memperkenalkan mempertemukan menghubungkan mengaktifkan memisahkan menolong menyulitkan memudahkan
mengalihkan membangkitkan menggeser mencoba ingin
""".split())

# verba yang wajar untuk benda (dibiarkan, hanya untuk dokumentasi dan uji)
VERBA_LAZIM = set("""
menentukan membuat memengaruhi menuntut membutuhkan memuat berisi menghasilkan meliputi mencakup
mengandung terdiri menjadi bertujuan berfungsi berlaku berlangsung bergantung berkaitan memiliki
""".split())

PREPOSISI = set("""
pada dalam di ke dari untuk bagi oleh dengan melalui lewat tentang terhadap menurut seperti
sebagai atas antara tanpa sejak hingga sampai mengenai per
""".split())
KONJ_KLAUSA = set("""
dan tetapi sedangkan karena sehingga bahwa sebab padahal namun serta atau meskipun walaupun bila
jika ketika saat agar supaya sementara lalu kemudian
""".split())
BANTU = set("""
itu ini tersebut tidak juga pun dapat bisa akan sudah telah justru sering selalu hanya masih lebih
sekaligus kemudian lalu memang biasanya cenderung mampu kerap jarang turut ikut pula
""".split())
GERUND_NP = set("""
berbicara belajar bermain menyimak membaca menulis mendengarkan berpikir berargumen berlatih
bercerita berdiskusi berdebat berpidato mengajar
""".split())

VERBA_GERUND = set("""
memaksa membantu mendorong memungkinkan memberi memberikan menjadikan melatih mengajarkan menolong
memperkuat memudahkan menyulitkan mencegah menjamin membuka membawa mengancam
""".split())

PERANGKAI = [
    "selain itu", "di samping itu", "begitu pula", "demikian juga", "demikian pula", "namun",
    "akan tetapi", "sebaliknya", "meskipun begitu", "meskipun demikian", "meski demikian", "sebab",
    "akibatnya", "karena itu", "oleh karena itu", "oleh sebab itu", "dengan demikian", "misalnya",
    "sebagai contoh", "contohnya", "pertama", "kedua", "ketiga", "keempat", "kelima", "selanjutnya",
    "kemudian", "terakhir", "lalu", "bahkan", "justru", "memang", "sementara itu", "adapun",
    "serupa dengan itu", "jadi", "singkatnya", "sesudah itu", "setelah itu", "sebelumnya",
    "sejak itu", "padahal", "untuk itu", "hasilnya", "artinya", "maka", "sayangnya", "untungnya",
    "di sisi lain", "berbeda dengan", "seperti", "hal yang sama", "dari situ", "dari sana",
]
RUJUK = re.compile(r"\b(?:itu|ini|tersebut|demikian|begitu|keduanya|ketiganya|keempatnya|kelimanya|"
                   r"semuanya|sekaligus|pun|inilah|itulah)\b", re.I)

SANDING = [
    (r"\bmemainkan peran\b", "berperan"),
    (r"\bmemegang peran(?:an)?\b", "berperan"),
    (r"\bmembangun hubungan\b", "menjalin hubungan"),
    (r"\bmembangun kepercayaan\b", "menumbuhkan kepercayaan"),
    (r"\bmembangun pemahaman\b", "memperoleh/menumbuhkan pemahaman"),
    (r"\bmembangun (?:kesiapan|kesadaran|kebiasaan)\b", "menumbuhkan ..."),
    (r"\bmembuat keputusan\b", "mengambil keputusan"),
    (r"\bmembuat perbedaan\b", "berpengaruh, membawa perubahan"),
    (r"\bmengambil tempat\b", "berlangsung"),
    (r"\bmenggeser (?:perhatian|fokus)\b", "lebih menekankan, memusatkan perhatian pada"),
    (r"\bmembuka lapisan\b", "membahas ... yang lebih mendasar"),
    (r"\bmenutup (?:jarak|kesenjangan|celah)\b", "mempersempit kesenjangan"),
    (r"\bmenegosiasikan makna\b", "merundingkan makna"),
    (r"\bkerja berpikir\b", "proses berpikir"),
    (r"\b(?:suara|ucapan) batin\b", "ucapan dalam hati"),
    (r"\bberpikir bersuara\b", "berpikir lantang (think-aloud)"),
    (r"\bpesannya jelas\b", "Jadi, ..."),
    (r"\bberakibat praktis\b|\bimplikasi praktis\b", "dapat langsung diterapkan"),
    (r"\bbergerak ke arah yang sama\b", "sejalan dengan"),
    (r"\bmenyapu (?:seluruh )?ruang(?:an)?\b", "beredar ke seluruh ruangan"),
    (r"\bbank contoh\b", "himpunan contoh"),
    (r"\bpada gilirannya\b", "selanjutnya, akibatnya"),
    (r"\bterlepas dari\b", "meskipun, tanpa memandang"),
    (r"\bpenting untuk dicatat\b", "perlu dicatat"),
    (r"\bmemberikan kontribusi\b", "berkontribusi"),
    (r"\bberbicara publik\b", "berbicara di depan umum"),
    (r"\bpratinjau internal\b", "gambaran bagian berikut"),
    (r"\bringkasan internal\b", "rangkuman sementara"),
    (r"\baprehensi komunikasi\b", "kecemasan berkomunikasi"),
    (r"\bpengalaman vikarius\b", "pengalaman tidak langsung"),
    (r"\bpenjelasan diri\b", "menjelaskan kepada diri sendiri"),
    (r"\btulis(?:lah)? untuk telinga\b|\bmenulis untuk telinga\b", "menulis catatan untuk didengar"),
    (r"\bke mana saya menuju\b", "apa tujuan saya"),
    (r"\bdilarang dari\b", "dilarang masuk/ikut"),
    (r"\bwatak (?:bahasa|lisan)\b|\bmemiliki watak\b", "ciri, sifat"),
    (r"\bmenyimpan (?:pelajaran|pesan)\b", "dapat dipetik pelajaran"),
    (r"\bmembawa kabar baik\b", "merupakan kabar baik"),
    (r"\bmembuka peluang\b", "berpeluang; dengan ..., terbuka peluang"),
    (r"\bmembeku\b", "terdiam, mematung (kecuali benda yang benar-benar beku)"),
    (r"\byang mana\b", "yang"),
    (r"\bdi sisi lain\b", "sementara itu, sebaliknya (boleh sesekali)"),
    (r"\bpada akhirnya\b", "akhirnya, jadi (boleh sesekali)"),
]
SANDING = [(re.compile(p, re.I), s) for p, s in SANDING]

KABUR = [
    (re.compile(r"\bsebagian (?:lain|lagi)\b", re.I), "sebut pelakunya (nama ahli atau nomina)"),
    (re.compile(r"\b(?:yang|ahli|pakar|peneliti) (?:yang )?lain lagi\b", re.I), "sebut pelakunya"),
    (re.compile(r"(?:^|(?<=[.!?]\s))Ada (?:pula |juga )?yang\b"), "beri nomina: Ada pembicara yang ..."),
    (re.compile(r"(?:^|(?<=[.!?]\s))Sebagian (?:ahli|rumusan|pakar|peneliti|pendapat)\b"),
     "sebut nama ahlinya"),
    (re.compile(r"(?:^|(?<=[.!?]\s))Yang lain\b"), "sebut pelakunya"),
]

# (pola, saran, pengecualian: regex konteks yang membuat temuan diabaikan)
SERAPAN = [
    (r"\bholisti(?:k|s)\b", "menyeluruh, utuh", None),
    (r"\bkomprehensif\b", "menyeluruh, lengkap", None),
    (r"\bsignifikan\b", "berarti, penting, nyata (kecuali arti statistik)", r"\bp\s*[<=>]|\buji\b|statisti"),
    (r"\b(?:meng)?implementasi(?:kan|kannya)?\b", "penerapan, pelaksanaan; menerapkan", None),
    (r"\b(?:meng)?optimal(?:kan)?\b", "sebaik-baiknya; memanfaatkan sebaik-baiknya", None),
    (r"\bfundamental\b", "mendasar", None),
    (r"\besensial\b", "pokok, hakiki, inti", None),
    (r"\bkrusial\b", "sangat penting, menentukan", None),
    (r"\burgen(?:si)?\b", "mendesak; kepentingan", None),
    (r"\belemen\b", "unsur", None),
    (r"\b(?:ber)?kontribusi\b", "sumbangan; menyumbang, berperan", None),
    (r"\b(?:ber)?partisipasi\b", "keikutsertaan, peran serta; ikut serta", None),
    (r"\binisiatif\b", "prakarsa", None),
    (r"\b(?:ber)?kolabora(?:si|tif)\b", "kerja sama, bekerja sama", None),
    (r"\beksplisit\b", "tersurat, terang, secara langsung", None),
    (r"\bimplisit\b", "tersirat", None),
    (r"\bparadigma\b", "cara pandang", None),
    (r"\bperspektif\b", "sudut pandang", None),
    (r"\bmekanisme\b", "cara kerja, tata cara", None),
    (r"\bsubstansial\b", "berarti, mendasar", None),
    (r"\bspesifik\b", "khusus, rinci, tertentu", None),
    (r"\b(?:men)?detail\b", "rincian, rinci", None),
    (r"\bakurat\b", "tepat, cermat", None),
    (r"\bvariasi\b", "ragam, keragaman", r"variasi vokal|variasi bahasa"),
    (r"\balternatif\b", "pilihan, pilihan lain", None),
    (r"\b(?:mem)?prioritas(?:kan)?\b", "hal utama; mengutamakan", None),
    (r"\btransformasi\b", "perubahan", None),
    (r"\b(?:ber)?adaptasi\b", "penyesuaian; menyesuaikan diri", None),
    (r"\b(?:meng)?integrasi(?:kan)?\b", "keterpaduan; memadukan", None),
    (r"\b(?:meng)?elaborasi(?:kan)?\b", "penjabaran; menjabarkan", None),
    (r"\binovatif\b", "baru, segar", None),
    (r"\befisien\b", "hemat, tepat guna", None),
    (r"\b(?:mayoritas|minoritas)\b", "sebagian besar / sebagian kecil", None),
    (r"\bredundansi\b", "pengulangan yang berlebihan", None),
    (r"\b(?:feedback|skill|mindset|insight|output|input|sharing|review|deadline|workshop|"
     r"online|offline|slide|audiens|audience|engagement|mentoring|coaching)\b",
     "pakai padanan: umpan balik, keterampilan, pola pikir, wawasan, keluaran, masukan, berbagi, "
     "tinjauan, tenggat, lokakarya, daring, luring, salindia, pendengar, keterlibatan, pendampingan", None),
]
SERAPAN = [(re.compile(a, re.I), b, re.compile(c, re.I) if c else None) for a, b, c in SERAPAN]

SINGKATAN = ["dkk.", "hlm.", "dll.", "dsb.", "dst.", "No.", "Prof.", "Dr.", "S.Pd.", "M.Pd.", "S.S.",
             "Ph.D.", "M.AL.", "a.n.", "Swt.", "Saw.", "Jl.", "vol.", "Vol.", "ed.", "Ed.", "et al."]

# ----------------------------------------------------------------------------- baca berkas


def baca(nama):
    """Kembalikan daftar (nomor_baris, teks_mentah)."""
    if nama == "-":
        return list(enumerate(sys.stdin.read().splitlines(), 1))
    p = Path(nama)
    if p.suffix.lower() == ".docx":
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with zipfile.ZipFile(p) as z:
            akar = ET.fromstring(z.read("word/document.xml"))
        hasil = []
        for i, par in enumerate(akar.iter(f"{{{ns['w']}}}p"), 1):
            teks = "".join(t.text or "" for t in par.iter(f"{{{ns['w']}}}t"))
            if teks.strip():
                hasil.append((i, teks))
        return hasil
    return list(enumerate(p.read_text(encoding="utf-8").splitlines(), 1))


def bersihkan(teks):
    t = re.sub(r"`[^`]*`", " ", teks)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)(\{[^}]*\})?", r"\1", t)   # gambar: ambil keterangannya
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)                 # tautan
    t = re.sub(r"\[([^\]]*)\]\{[^}]*\}", r"\1", t)                 # span pandoc
    t = re.sub(r"\{[#.][^}]*\}", " ", t)                           # atribut pandoc
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[*_]{1,3}", "", t)
    t = re.sub(r"^\s*(?:[-+]|\d+\.)\s+", "", t)
    t = re.sub(r"^\s*>\s?", "", t)
    return re.sub(r"\s+", " ", t).strip()


def segmen(baris):
    """Kembalikan (nomor, teks, jenis) untuk prosa, sel tabel, judul, butir."""
    hasil, dalam_kode, abaikan, pustaka, yaml = [], False, False, False, False
    for n, mentah in baris:
        s = mentah.strip()
        if n == 1 and s == "---":
            yaml = True
            continue
        if yaml:
            if s == "---":
                yaml = False
            continue
        if s.startswith("```"):
            dalam_kode = not dalam_kode
            continue
        if dalam_kode:
            continue
        if "lazim:abaikan" in s:
            abaikan = True
            continue
        if "lazim:lanjut" in s:
            abaikan = False
            continue
        if abaikan or not s or s.startswith(":::") or re.match(r"^\|?\s*:?-{2,}", s):
            continue
        if re.match(r"^#{1,6}\s", s):
            judul = bersihkan(s.lstrip("#"))
            pustaka = bool(re.match(r"(?i)(daftar (pustaka|rujukan|referensi)|referensi|bibliografi)", judul))
            hasil.append((n, judul, "judul", []))
            continue
        if pustaka:
            continue
        if re.match(r"^(\*\*)?(Sebelum|Kalke)\b", s):
            continue
        miring = re.findall(r"(?<![*\w])[*_]([^*_]+)[*_](?![*\w])", s)
        if s.startswith("|"):
            for sel in s.strip("|").split("|"):
                sel = bersihkan(sel)
                if sel:
                    hasil.append((n, sel, "tabel", miring))
            continue
        jenis = "butir" if re.match(r"^\s*(?:[-+*]|\d+\.)\s+", mentah) else "prosa"
        t = bersihkan(s)
        if t:
            hasil.append((n, t, jenis, miring))
    return hasil


def kalimat(teks):
    t = teks
    for i, s in enumerate(SINGKATAN):
        t = t.replace(s, s.replace(".", f"\u0001{i}\u0002"))
    bagian = re.split(r"(?<=[.!?])[\"”']?\s+(?=[\"“(]?[A-Z])", t)
    keluar = []
    for b in bagian:
        for i, s in enumerate(SINGKATAN):
            b = b.replace(s.replace(".", f"\u0001{i}\u0002"), s)
        b = re.sub(r"\u0001\d+\u0002", ".", b)
        if b.strip():
            keluar.append(b.strip())
    return keluar


def token(kal):
    return re.findall(r"[A-Za-zÀ-ɏ][\wÀ-ɏ\-]*|\d+(?:[.,]\d+)*|[,;:]", kal)


# ----------------------------------------------------------------------------- pemeriksa


def awal_klausa(tok, i):
    """Apakah tok[i] berada di awal klausa (bukan objek atau bagian frasa preposisi)?"""
    if i == 0:
        return True
    sebelum = tok[i - 1].lower()
    if sebelum in (",", ";", ":"):
        return True
    if sebelum in KONJ_KLAUSA:
        return True
    if sebelum == "yang":
        return False
    return False


BUKAN_VERBA = set("""
diskusi dimensi digital dialog diagram diksi disiplin direktur diri dinamika didaktik dirinya
dirimu diriku teras terapi terminologi termasuk berita beras berat berkas bersama beserta
""".split())
VERBA_RE = re.compile(r"^(?:me(?:m[bpfaeiou]|n[cdjtszaeiou]|ng[aeiougkh]|ny[aeiou]|[lrwy])"
                      r"|be(?:r[a-z]|l)|di[a-z]{3,}|ter[a-z]{3,}|per[a-z]{3,}(?:kan|i))[a-z]+")


def verba_berimbuhan(w):
    w = w.lower()
    return bool(VERBA_RE.match(w)) and w not in BUKAN_VERBA


# nomina abstrak berkonfiks pe-an/ke-an/per-an (pendampingan, keberhasilan, pertemuan) di awal klausa
KONFIKS = re.compile(r"^(?:pe[mny]?|peng|per|ke)[a-z]{3,}an$")


def cek_pelaku(kal):
    tok = token(kal)
    rendah = [t.lower() for t in tok]
    temuan = []
    # frasa "hal ini" dan sejenisnya
    for frasa in SUBJEK_FRASA:
        for m in re.finditer(r"\b" + frasa + r"\b\s+(\w+)", kal, re.I):
            if m.group(1).lower() in VERBA_PELAKU:
                temuan.append(m.group(0))
    for i, w in enumerate(rendah):
        if (w not in SUBJEK and not KONFIKS.match(w)) or not awal_klausa(tok, i):
            continue
        # subjek di dalam frasa nomina yang lebih panjang (mis. "Ponsel yang ...") tetap diperiksa
        for j in range(i + 1, min(i + 10, len(rendah))):
            w2 = rendah[j]
            if w2 in (",", ";", ":"):
                break
            if w2 in KONJ_KLAUSA and w2 not in ("dan", "serta", "atau"):
                break
            if w2 in VERBA_PELAKU:
                sisa = [x.lower() for x in tok[j + 1:]]
                if "," in sisa:
                    sisa = sisa[:sisa.index(",")]
                if w not in SUBJEK and j == i + 1:
                    break      # "kesempatan mencoba", "kesulitan memberi": nomina + pelengkap, bukan pelaku
                if w2 in ("memberi", "memberikan") and sisa[:1] == ["kesan"]:
                    break      # "memberi kesan" lazim untuk benda
                if j == i + 1 and any(x in ("adalah", "merupakan", "ialah") or
                                      (re.match(r"^(?:di|ter)[a-z]{3,}", x) and x not in BUKAN_VERBA)
                                      for x in sisa):
                    break      # "kegiatan menjelaskan ditempatkan ...": frasa nomina, predikatnya lain
                # "X yang memperlihatkan" juga kalke (pendekatan yang menyajikan ...)
                temuan.append(" ".join(tok[i:j + 1]))
                break
            if w2 in VERBA_LAZIM:
                break
            if verba_berimbuhan(w2) and w2 not in GERUND_NP \
                    and w2 not in BANTU and w2 not in PREPOSISI and w2 not in SUBJEK:
                break
            if w2 in ("adalah", "merupakan", "ialah", "yaitu", "bahwa", "agar", "sehingga", "karena"):
                break
    return temuan


def cek_gerund(kal):
    tok = token(kal)
    if not tok:
        return []
    i = 0
    if tok[0] in ("Mengapa", "Bagaimana", "Apakah"):
        i = 1
    if i >= len(tok) or not re.match(r"^(?:me|be)", tok[i].lower()) or not verba_berimbuhan(tok[i]):
        return []
    for j in range(i + 1, min(i + 14, len(tok))):
        w = tok[j].lower()
        if w in (",", ";", ":") or w in ("dan", "atau", "serta", "untuk", "agar", "supaya", "sehingga",
                                          "adalah", "merupakan", "ialah", "yaitu") or w in KONJ_KLAUSA:
            return []
        if w in VERBA_GERUND:
            return [" ".join(tok[i:j + 1])]
        if verba_berimbuhan(w) and w not in GERUND_NP and w not in BANTU:
            return []          # predikat utamanya verba lain yang wajar (bertujuan, menuntut, ...)
    return []


URUTAN = re.compile(r"\b(?:pertama|kedua|ketiga|keempat|kelima|terakhir|berikutnya|lainnya)\b", re.I)
PENAMBAH = re.compile(r"\b(?:juga|pula|lagi|masih|tetap)\b", re.I)


def nyambung(kal):
    """Apakah kalimat ini tersambung ke kalimat sebelumnya (perangkai, kata rujuk, -nya, urutan)?"""
    tok = token(kal)
    awal = " ".join(t.lower() for t in tok[:5])
    if any(re.match(r"^" + re.escape(p) + r"\b", awal) for p in PERANGKAI):
        return True
    if kal.rstrip().endswith("?"):
        return True            # deret pertanyaan retoris tidak dihitung
    if any(t.lower().endswith("nya") and t.lower() != "hanya" for t in tok):
        return True            # rujukan balik lewat -nya (Caranya, membedakannya)
    if URUTAN.search(" ".join(tok[:6])) or PENAMBAH.search(kal):
        return True
    return bool(RUJUK.search(kal))


LABEL = re.compile(r"^:?\s*(?:Tabel|Gambar|Foto(?: ilustrasi)?|Diagram|Grafik|Bagan)\s+\d+(?:\.\d+)*\s+(?=[A-Z])")


def periksa_segmen(n, teks, jenis, keluar, miring=()):
    teks = LABEL.sub("", teks)
    kal_list = kalimat(teks)
    for kal in kal_list:
        for f in cek_pelaku(kal):
            keluar.append((n, "LZ-01", "pelaku", f, "ubah ke pasif (tampak pada, dirangkum dalam), "
                           "keterangan (Dengan ..., Dalam ...), atau pelaku manusia", kal))
        for f in cek_gerund(kal):
            keluar.append((n, "LZ-02", "gerund", f, "jadikan keterangan (Saat/Bila ...) dan munculkan pelakunya", kal))
        for pola, saran in KABUR:
            for m in pola.finditer(kal):
                keluar.append((n, "LZ-03", "kabur", m.group(0), saran, kal))
        for pola, saran in SANDING:
            for m in pola.finditer(kal):
                keluar.append((n, "LZ-04", "sanding", m.group(0), saran, kal))
        for pola, saran, kecuali in SERAPAN:
            for m in pola.finditer(kal):
                if kecuali and kecuali.search(kal):
                    continue
                if any(m.group(0).lower() in x.lower().split() for x in miring):   # istilah asing bercetak miring
                    continue
                keluar.append((n, "LZ-07", "serapan", m.group(0), saran, kal))
    if jenis != "prosa" or len(kal_list) < 4:
        return
    # LZ-05: deret kalimat tanpa perangkai/kata rujuk
    deret, mulai = 0, None
    for k, kal in enumerate(kal_list[1:], 1):
        if nyambung(kal):
            deret = 0
            continue
        deret += 1
        if deret == 1:
            mulai = k
        if deret == 3:
            keluar.append((n, "LZ-05", "kohesi", kal_list[mulai][:70] + " ...",
                           "tiga kalimat berturut-turut tanpa perangkai atau kata rujuk; rangkai (lihat kohesi.md)",
                           " ".join(kal_list[mulai:k + 1])))
    # LZ-06: pembuka kalimat yang sama
    pembuka = Counter(token(k)[0].lower() for k in kal_list if token(k))
    for w, c in pembuka.items():
        if c >= 3 and w not in ("kita", "ia", "mereka", "kami", "saya"):
            keluar.append((n, "LZ-06", "monoton", f"{c} kalimat dibuka dengan '{w}'",
                           "variasikan pembuka atau gabungkan kalimat sejajar", teks[:240]))
    dengan = sum(1 for k in kal_list if re.match(r"^(Dengan|Dalam|Melalui|Lewat)\b[^,]{2,60},", k))
    if dengan >= 3:
        keluar.append((n, "LZ-06", "monoton", f"{dengan} kalimat dibuka 'Dengan/Dalam/Melalui ...,'",
                       "perbaikan kalke jangan seragam; pakai juga pasif atau pelaku manusia", teks[:240]))


def pindai(nama):
    keluar = []
    for n, teks, jenis, miring in segmen(baca(nama)):
        periksa_segmen(n, teks, jenis, keluar, miring)
    return keluar


# ----------------------------------------------------------------------------- banding


def sitasi(teks):
    """Pasangan (nama, tahun) dari sitasi naratif maupun dalam kurung, tanpa peduli bentuknya."""
    hasil = Counter()
    nama = r"[A-Z][\w'\-À-ɏ]+(?:(?:,\s|\s(?:dan|&)\s)[A-Z][\w'\-À-ɏ]+)*(?:\sdkk\.)?"
    for m in re.finditer(r"\(([^()]*\d{4}[a-z]?[^()]*)\)", teks):
        isi = m.group(1)
        sebelum = teks[:m.start()].rstrip()
        mn = re.search(r"(" + nama + r")\s*$", sebelum)
        if re.fullmatch(r"\s*\d{4}[a-z]?(?:,\s*\d{4}[a-z]?)*(?:,\s*hlm\.[^)]*)?\s*", isi) and mn:
            for th in re.findall(r"\d{4}[a-z]?", isi):
                hasil[(mn.group(1).strip(), th)] += 1
            continue
        for bagian in isi.split(";"):
            mb = re.search(r"(" + nama + r"),?\s+(\d{4}[a-z]?(?:,\s*\d{4}[a-z]?)*)", bagian)
            if mb:
                for th in re.findall(r"\d{4}[a-z]?", mb.group(2)):
                    hasil[(mb.group(1).strip(), th)] += 1
    return hasil


def angka(teks):
    return Counter(re.findall(r"(?<![\w.])\d+(?:[.,]\d+)*(?:%|\b)", teks))


def kutipan(teks):
    return set(m.strip() for m in re.findall(r"[\"“]([^\"”]{8,})[\"”]", teks))


def banding(asli, hasil):
    ta = "\n".join(t for _, t in baca(asli))
    th = "\n".join(t for _, t in baca(hasil))
    beda = 0
    sa, sh = sitasi(ta), sitasi(th)

    def sama(k, kumpulan):
        # "di Bandung, Sari dkk. (2022)" terbaca "Bandung, Sari dkk."; cocokkan lewat akhiran nama
        return any(t == k[1] and (n == k[0] or n.endswith(", " + k[0]) or k[0].endswith(", " + n))
                   for n, t in kumpulan)
    for k in sorted(set(sa) | set(sh)):
        if k not in sh and not sama(k, sh):
            print(f"[SITASI] hilang: {k[0]} ({k[1]})"); beda += 1
        elif k not in sa and not sama(k, sa):
            print(f"[SITASI] baru: {k[0]} ({k[1]})"); beda += 1
    aa, ah = angka(ta), angka(th)
    for k in sorted(set(aa) | set(ah)):
        if aa[k] != ah[k]:
            print(f"[ANGKA] {k}: {aa[k]} kali menjadi {ah[k]} kali"); beda += 1
    ka, kh = kutipan(ta), kutipan(th)
    for k in sorted(ka - kh):
        print(f"[KUTIPAN] berubah/hilang: \"{k[:80]}\"")
    for k in sorted(kh - ka):
        print(f"[KUTIPAN] baru: \"{k[:80]}\"")
    if not beda:
        print("Sitasi (nama dan tahun) serta angka sama." +
              (" Ada kutipan yang berubah; pastikan itu contoh buatan naskah, bukan kutipan sumber."
               if ka != kh else ""))
    return 1 if beda else 0


# ----------------------------------------------------------------------------- uji mandiri


def tes():
    positif = [
        ("Tabel 2.2 memperlihatkan wujudnya dalam berbicara.", "LZ-01"),
        ("Kajian pada mahasiswa pendidikan bahasa menemukan empat kondisi.", "LZ-01"),
        ("Meskipun begitu, rekaman juga membuka peluang yang tidak dimiliki situasi lain.", "LZ-01"),
        ("Penelitian tentang metakognisi dalam berbicara memperkuat temuan itu.", "LZ-01"),
        ("Foto 5.1 Penjelasan singkat dalam rapat warga memperlihatkan kegiatan berbicara.", "LZ-01"),
        ("Gambar 1 Pendampingan orang tua menunjukkan tiga kegiatan utama.", "LZ-01"),
        ("Menjelaskan konsep kepada anggota keluarga memaksa pembelajar memilih kata.", "LZ-02"),
        ("Mengapa menjelaskan memaksa orang memilih kata?", "LZ-02"),
        ("Sementara itu, sebagian lain menggeser perhatian kepada pendengar.", "LZ-03"),
        ("Ada pula yang membuka lapisan lebih dalam.", "LZ-03"),
        ("Kontak mata membantu pembicara membangun hubungan dengan pendengar.", "LZ-04"),
        ("Bagi pendidik, pesannya jelas: kecemasan bukan sekadar kurang berani.", "LZ-04"),
        ("Pembelajaran berbicara perlu dirancang secara holistik.", "LZ-07"),
        ("Implementasi model ini memberi kontribusi yang signifikan.", "LZ-07"),
    ]
    negatif = [
        "Wujudnya dalam berbicara tampak pada Tabel 2.2.",
        "Dalam kajian pada mahasiswa pendidikan bahasa, ditemukan empat kondisi.",
        "Situasi ini menuntut konseptualisasi yang lebih matang.",
        "Saat menjelaskan konsep kepada anggota keluarga, pembelajar terdorong memilih kata.",
        "Bagi Tarigan (2008), berbicara selalu berwujud bunyi.",
        "Ada pembicara yang lalu berhenti sejenak.",
        "Penelitian ini bertujuan menguji model itu.",
        "Rekam satu penjelasan pendek, cukup satu sampai dua menit.",
        "Mahasiswa mampu menulis, tetapi kesulitan memberi penjelasan lisan.",
        "Dengan kontak mata, pembicara menjalin hubungan dengan pendengar.",
        "Perpaduannya disebut variasi vokal, yaitu perubahan volume dan nada.",
        "Perbedaannya signifikan secara statistik (p < 0,05).",
    ]
    gagal = 0
    for kal, kode in positif:
        hasil = []
        periksa_segmen(1, kal, "butir", hasil)
        if kode not in [h[1] for h in hasil]:
            print(f"GAGAL (luput {kode}): {kal}"); gagal += 1
    for kal in negatif:
        hasil = []
        periksa_segmen(1, kal, "butir", hasil)
        if hasil:
            print(f"GAGAL (salah tangkap {[h[1] for h in hasil]}): {kal}"); gagal += 1
    par = ("Berbicara sebagai interaksi menuntut kepekaan. Berbicara sebagai transaksi menuntut "
           "ketepatan isi. Berbicara sebagai penampilan menuntut persiapan. Pembicara perlu tenang.")
    hasil = []
    periksa_segmen(1, par, "prosa", hasil)
    for kode in ("LZ-05", "LZ-06"):
        if kode not in [h[1] for h in hasil]:
            print(f"GAGAL (luput {kode}) pada paragraf tumpukan"); gagal += 1
    for kal in ["Berbicara sebagai interaksi menuntut kepekaan terhadap lawan bicara.",
                "Berbicara informatif bertujuan menambah pengetahuan pendengar.",
                "Memisahkan gagasan dan memberi tekanan",
                "Postur tegak memberi kesan siap.",
                "Dalam Teknik Feynman, kegiatan menjelaskan ditempatkan sebagai cara belajar.",
                "Pemahaman lebih kuat bila pembelajar menjelaskan materi kepada orang lain.",
                ": Tabel 7.1 Belajar dengan menjelaskan menurut para ahli"]:
        hasil = []
        periksa_segmen(1, kal, "butir", hasil)
        if hasil:
            print(f"GAGAL (salah tangkap {[h[1] for h in hasil]}): {kal}"); gagal += 1
    hasil = []
    periksa_segmen(1, "Rumusan ABCD, yaitu sasaran (audience).", "butir", hasil, ["audience"])
    if hasil:
        print("GAGAL: istilah miring tertangkap LZ-07"); gagal += 1
    a = "Hal itu penting (Tarigan, 2008; Mulyati, 2015). Data 72 dan 74."
    b = "Bagi Tarigan (2008), hal itu penting, begitu pula bagi Mulyati (2015). Data 72 dan 74."
    if sitasi(a) != sitasi(b):
        print(f"GAGAL banding sitasi: {sitasi(a)} vs {sitasi(b)}"); gagal += 1
    import io, contextlib, tempfile
    with tempfile.TemporaryDirectory() as d:
        Path(d, "a.md").write_text("Kajian itu menemukan 68% (Sari dkk., 2022).")
        Path(d, "b.md").write_text("Dalam kajian di Bandung, Sari dkk. (2022) menemukan 68%.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kode = banding(str(Path(d, "a.md")), str(Path(d, "b.md")))
        if kode:
            print("GAGAL banding: nama kota sebelum sitasi naratif dianggap sitasi baru"); gagal += 1
    print("Semua uji lolos." if not gagal else f"{gagal} uji gagal.")
    return 1 if gagal else 0


# ----------------------------------------------------------------------------- utama


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--tes":
        return tes()
    if argv[0] == "--banding":
        if len(argv) != 3:
            print("Pemakaian: pindai.py --banding asli hasil"); return 2
        return banding(argv[1], argv[2])
    ringkas, kode, konteks = False, None, False
    berkas = []
    i = 0
    while i < len(argv):
        if argv[i] == "--ringkas":
            ringkas = True
        elif argv[i] == "--konteks":
            konteks = True
        elif argv[i] == "--kode":
            i += 1
            kode = set(argv[i].split(","))
        else:
            berkas.append(argv[i])
        i += 1
    total = 0
    for nama in berkas:
        temuan = [t for t in pindai(nama) if not kode or t[1] in kode]
        total += len(temuan)
        if ringkas:
            c = Counter(f"{t[1]} {t[2]}" for t in temuan)
            print(f"{nama}: {len(temuan)} temuan" + ("" if not c else " (" + ", ".join(
                f"{k}: {v}" for k, v in sorted(c.items())) + ")"))
            continue
        for n, k, label, frag, saran, kal in temuan:
            print(f"{nama}:{n}: [{k} {label}] «{frag}» → {saran}")
            if konteks:
                print(f"    {kal}")
        if temuan:
            print(f"{nama}: {len(temuan)} temuan")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
