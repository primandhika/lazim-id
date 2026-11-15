# lazim-id

Skill untuk agen AI (Claude Code dan sejenisnya) yang membasmi **kalke**, yaitu terjemahan kasar
dari bahasa Inggris, dalam naskah berbahasa Indonesia sekaligus merapikan **kohesi paragraf**.
Tujuannya sederhana: naskah terdengar ditulis orang Indonesia, bukan diterjemahkan.

Prinsip kerjanya **memperbaiki, bukan menulis ulang**. Kalimat, urutan gagasan, dan suara penulis
dipertahankan. Fakta, angka, dan sitasi tidak diubah.

Skill ini lahir dari penyuntingan sebuah buku referensi pendidikan. Penulisnya berkali-kali harus
menunjuk kalimat yang "ga lazim" satu per satu. Pola-pola yang ditunjuk itu kemudian dihimpun,
diberi contoh, dan dijadikan alur kerja serta pemindai otomatis supaya agen menemukannya sendiri.

## Kalimat macam apa yang bermasalah?

Kalke jarang berupa kata yang salah. Biasanya kata-katanya Indonesia, tetapi susunannya
Inggris. Pembaca merasakannya sebagai "kok aneh", lalu berhenti percaya pada tulisannya.

### 1. Benda mati sebagai pelaku tindakan manusia

Dalam bahasa Inggris, *the table shows* dan *the study found* wajar. Dalam bahasa Indonesia,
tabel, foto, kajian, atau rekaman yang "memperlihatkan", "menemukan", "membantu", atau "membuka
peluang" terdengar seperti terjemahan.

| Kalke | Lazim |
|:--|:--|
| Tabel 2.2 memperlihatkan wujudnya dalam berbicara. | Wujudnya dalam berbicara tampak pada Tabel 2.2. |
| Kajian pada mahasiswa menemukan empat kondisi. | Dalam kajian pada mahasiswa, ditemukan empat kondisi. |
| Rekaman membuka peluang yang tidak dimiliki situasi lain. | Dengan rekaman, terbuka peluang yang tidak ada pada situasi lain. |
| Foto 5.1 Penjelasan singkat dalam rapat warga memperlihatkan kegiatan berbicara informatif. | Foto 5.1 Berbicara informatif juga berlangsung di luar kelas, misalnya saat menyampaikan penjelasan singkat dalam rapat warga. |

Tidak semua verba aktif untuk benda itu kalke. *Menentukan, membuat, memengaruhi, menuntut,
memuat, berisi* lazim untuk benda ("Situasi ini menuntut persiapan yang matang"), jadi dibiarkan.

### 2. Subjek kabur

Pola *some ... others ...* menghasilkan subjek tanpa nomina.

| Kalke | Lazim |
|:--|:--|
| Sebagian ahli mengingatkan ... Sebagian lain menggeser perhatian kepada pendengar ... Ada pula yang membuka lapisan lebih dalam ... | Bagi Tarigan (2008), ... Mulyati (2015) lebih menekankan peran pendengar ... Adapun Goh dan Liu (2023) membahas proses mental ... |
| Ada yang lalu berhenti sejenak. | Ada pembicara yang lalu berhenti sejenak. |

### 3. Kegiatan sebagai subjek

| Kalke | Lazim |
|:--|:--|
| Menjelaskan konsep kepada keluarga memaksa pembelajar memilih kata yang sederhana. | Saat menjelaskan konsep kepada keluarga, pembelajar terdorong memilih kata yang sederhana. |

Kegiatan sebagai subjek dengan verba yang wajar tetap boleh: "Berbicara di depan umum menuntut
persiapan", "Merokok membuat paru-paru rusak".

### 4. Sanding kata terjemahan

| Kalke | Lazim |
|:--|:--|
| membangun hubungan / kepercayaan / pemahaman | menjalin hubungan / menumbuhkan kepercayaan / memperoleh pemahaman |
| memainkan peran | berperan |
| membuat keputusan | mengambil keputusan |
| menutup kesenjangan | mempersempit kesenjangan |
| pembicara membeku di menit pertama (*froze*) | pembicara terdiam di menit pertama |
| pesannya jelas: ... | Jadi, ... |

### 5. Serapan Inggris yang punya padanan asli

| Serapan | Padanan |
|:--|:--|
| holistik, komprehensif | menyeluruh |
| implementasi | penerapan |
| kontribusi | sumbangan |
| paradigma, perspektif | cara pandang, sudut pandang |
| eksplisit, spesifik | secara langsung, khusus |

Padanan **tidak dipaksakan** untuk istilah bidang yang memang tidak punya padanan setara
(*metakognisi, artikulasi, register, kompetensi, efikasi diri*) dan untuk *signifikan* dalam
arti statistik. Padanan buatan yang tidak dikenal pembaca lebih buruk daripada serapannya.

### 6. Paragraf tanpa kohesi ("tumpukan ide")

Kalimat-kalimat pendek berderet tanpa penghubung sehingga paragraf terbaca seperti daftar butir
yang tandanya dihapus.

> **Sebelum:** Dalam obrolan santai, tujuan kita sederhana, topiknya akrab, dan pendengar langsung
> memberi isyarat bila bingung. Ketiga tahap berjalan hampir otomatis. Di depan kelas, tujuan lebih
> rumit. Konseptualisasi dan formulasi tidak lagi otomatis. Beban berpikir meningkat.
>
> **Sesudah:** Dalam obrolan santai, tujuan kita sederhana, topiknya akrab, dan pendengar langsung
> memberi isyarat bila bingung **sehingga** ketiga tahap berjalan hampir otomatis. **Sebaliknya**, di
> depan kelas tujuan lebih rumit. **Akibatnya**, konseptualisasi dan formulasi tidak lagi otomatis.
> Beban berpikir **pun** meningkat.

Yang berubah hanya perangkai. Isi dan urutan kalimat tetap.

## Bagaimana skill ini bekerja

1. **Batas pekerjaan dulu.** "Perbaiki", "improve", "rapikan" berarti sunting, bukan tulis ulang.
2. **Baca utuh**, lalu jaring dengan pemindai (`scripts/pindai.py`).
3. **Sisir manual per kalimat** dengan enam pertanyaan: siapa pelakunya, apakah subjeknya jelas,
   adakah sanding kata terjemahan, adakah serapan yang punya padanan akrab, apakah kalimat ini
   tersambung ke kalimat sebelumnya, dan apakah orang Indonesia akan menulis begini tanpa membaca
   versi Inggrisnya. Keterangan gambar, isi tabel, label diagram, dan contoh kalimat ikut disisir.
4. **Satu temuan berarti sisir semua.** Bila pengguna menunjuk satu kalimat, pola yang sama dicari
   di seluruh naskah.
5. **Perbaiki dengan edit kecil dan jalan keluar yang beragam** (pasif, pelaku manusia,
   keterangan), supaya tidak lahir pola monoton baru.
6. **Periksa fakta** dengan `pindai.py --banding`: nama dan tahun sitasi (dalam kurung maupun
   naratif), angka, dan kutipan dibandingkan dengan naskah asli.
7. **Sisir ulang hasil sendiri**, karena kalke baru paling sering lahir dari perbaikan.
8. **Laporkan** jumlah perbaikan per jenis, contoh sebelum dan sesudah, serta yang sengaja
   dibiarkan.

## Pemindai

`scripts/pindai.py` hanya memakai pustaka standar Python 3. Hasilnya kandidat, bukan putusan.

```bash
python3 scripts/pindai.py naskah.md bab2.md berkas.docx   # .md, .txt, .docx
python3 scripts/pindai.py --ringkas folder/*.md           # jumlah temuan per kode per berkas
python3 scripts/pindai.py --konteks naskah.md             # tampilkan kalimat utuhnya
python3 scripts/pindai.py --kode LZ-01,LZ-07 naskah.md    # hanya kode tertentu
python3 scripts/pindai.py --banding asli.md hasil.md      # sitasi, angka, kutipan yang berubah
python3 scripts/pindai.py --tes                           # uji mandiri
```

| Kode | Label | Yang ditangkap |
|:--|:--|:--|
| LZ-01 | pelaku | benda, dokumen, gagasan, atau nomina pe-an/ke-an sebagai pelaku verba tindakan manusia |
| LZ-02 | gerund | kegiatan sebagai subjek verba seperti *memaksa, membantu, mendorong* |
| LZ-03 | kabur | *sebagian lain, ada pula yang, yang lain lagi* |
| LZ-04 | sanding | sanding kata dan istilah terjemahan |
| LZ-05 | kohesi | tiga kalimat atau lebih berturut-turut tanpa perangkai atau kata rujuk |
| LZ-06 | monoton | kalimat dalam satu paragraf dibuka dengan kata atau pola yang sama |
| LZ-07 | serapan | serapan Inggris yang punya padanan Indonesia yang lebih akrab |

Contoh keluaran:

```text
bab3.md:21: [LZ-01 pelaku] «Tabel 3.2 memperlihatkan» → ubah ke pasif (tampak pada, dirangkum dalam), ...
bab3.md:34: [LZ-03 kabur] «sebagian lain» → sebut pelakunya (nama ahli atau nomina)
bab3.md:52: [LZ-07 serapan] «holistik» → menyeluruh, utuh
```

## Tinjauan uji

### Pada naskah buku sungguhan

Pemindai dijalankan pada delapan bab buku referensi pendidikan (sekitar 18.000 kata), sebelum dan
sesudah disunting dengan alur skill ini.

| | Naskah sebelum disunting | Naskah sesudah disunting |
|:--|:--|:--|
| Kandidat dari `pindai.py` | 129 | 20 |

Sisa 20 kandidat itu memang hal yang masih lolos dan layak diperiksa (misalnya *eksplisit*,
*spesifik*, *skala holistik*, dan tiga kalimat beruntun yang dibuka "Dalam ..."). Sebagai
gambaran, pemeriksa skill `naskah-id`, yang dirancang untuk kaidah EYD dan pola klise mesin,
mengeluarkan 10 temuan pada naskah sebelum disunting. Keduanya saling melengkapi: naskah-id
untuk kaidah, lazim-id untuk kelaziman.

### Tiga kasus uji

Setiap kasus dikerjakan agen terpisah yang hanya berbekal skill ini, tanpa konteks percakapan.
Kasus dan kriterianya ada di `evals/`.

| Kasus | Yang diuji | Lulus |
|:--|:--|:--|
| `sunting-bab-buku` | Bab penuh kalke dan paragraf tumpukan ide, diminta "improve, jangan ditulis ulang" | 6/6 |
| `satu-kalimat-ditunjuk` | Pengguna menunjuk satu kalimat; apakah kalimat sejenis di tempat lain ikut diperbaiki | 5/5 |
| `serapan-dan-istilah` | Serapan diganti, istilah tanpa padanan dan *signifikan* statistik tetap | 5/5 |

Cuplikan hasil `sunting-bab-buku`:

> **Sebelum:** Tabel 1 memperlihatkan beberapa rumusan tersebut. Sebagian ahli menekankan kemampuan
> teknis memakai perangkat (Gilster, 1997). Sebagian lain menggeser perhatian kepada kemampuan
> menilai informasi (Hobbs, 2010). Ada pula yang membuka lapisan lebih dalam, yaitu etika dan
> keamanan di ruang digital (Ribble, 2015).
>
> **Sesudah:** Beberapa rumusan tersebut dirangkum dalam Tabel 1. Gilster (1997) menekankan
> kemampuan teknis memakai perangkat, sedangkan Hobbs (2010) lebih memusatkan perhatian pada
> kemampuan menilai informasi. Adapun Ribble (2015) membahas sisi yang lebih mendasar, yaitu etika
> dan keamanan di ruang digital.

Cuplikan hasil `serapan-dan-istilah`:

> **Sebelum:** Paradigma pembelajaran berbicara saat ini menuntut pendekatan yang holistik, yaitu
> pendekatan yang mengintegrasikan aspek kognitif, afektif, dan metakognitif secara eksplisit.
> Metakognisi memungkinkan pembelajar merencanakan, memantau, dan mengevaluasi penampilannya
> (Goh dan Liu, 2023), sedangkan efikasi diri berkontribusi pada keberanian tampil (Bandura, 1977).
>
> **Sesudah:** Cara pandang terhadap pembelajaran berbicara saat ini menuntut pendekatan yang
> menyeluruh, yaitu pendekatan yang memadukan aspek kognitif, afektif, dan metakognitif secara
> langsung. Dengan metakognisi, pembelajar dapat merencanakan, memantau, dan mengevaluasi
> penampilannya (Goh dan Liu, 2023), sedangkan efikasi diri ikut menentukan keberanian tampil
> (Bandura, 1977).

Selama uji, agen juga menemukan hal yang tidak dijaring pemindai (*"buku ini memahami"*),
memperbaiki kalimat dengan cara yang beragam, dan menanyakan masalah isi alih-alih mengarang,
misalnya data survei tanpa sumber dan rumusan ahli di paragraf yang berbeda dari tabel.

Uji yang sama dapat dijalankan ulang dari folder skill dengan Claude Code:
`claude plugin eval . --allow-tools Write,Edit,Bash --scaffold`.

## Pemasangan

Salin atau tautkan folder ini ke folder skill Claude Code. Dari folder yang memuat `lazim-id/`:

```bash
ln -s "$(pwd)/lazim-id" ~/.claude/skills/lazim-id
```

Setelah sesi baru dibuka, skill dipanggil otomatis saat diminta merapikan atau menyisir naskah
Indonesia, atau langsung dengan `/lazim-id`.

## Struktur

```text
lazim-id/
├── SKILL.md                 alur kerja dan prinsip (dibaca agen)
├── references/
│   ├── pola-kalke.md        katalog pola, contoh sebelum-sesudah, daftar serapan
│   ├── kohesi.md            perangkai menurut hubungan makna, cara merangkai
│   └── contoh.md            dua paragraf utuh sebelum dan sesudah
├── scripts/pindai.py        pemindai kalke, kohesi, dan pembanding fakta
└── evals/                   tiga kasus uji beserta kriterianya
```

## Hubungan dengan naskah-id

Skill `naskah-id` mengurus kaidah: EYD V, kata baku, singkatan, dan sitasi.
lazim-id mengurus rasa bahasa: kalke, serapan, dan kohesi. Keduanya bisa dipakai bersamaan.

## Batasan

- Pemindai bersifat heuristik. Ia melewatkan sebagian kalke dan sesekali salah tangkap, jadi
  pembacaan utuh tetap wajib.
- Sasaran utamanya naskah nonfiksi: buku, artikel ilmiah, modul, dan bahan ajar. Untuk karya
  sastra dan dialog, sebagian "kalke" bisa jadi pilihan gaya.
- Skill ini tidak dirancang untuk menyamarkan teks buatan AI dari detektor. Tujuannya keterbacaan
  bagi pembaca Indonesia.
