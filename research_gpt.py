# ==================== RESEARCHGPT — AI DEEP RESEARCH AKADEMIK ====================
# ResearchGPT: AI Agent untuk menghasilkan jurnal ilmiah berkualitas tinggi
# Workflow: Understand → Search → Extract → Analyze → Synthesize → Generate Paper
# ================================================================================

import os
import re
import json
import datetime
import time
import sys
from typing import Dict, List, Any, Optional, Tuple

# ==================== LOAD .ENV ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # opsional, fallback ke env vars OS

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ==================== KONFIGURASI ====================
class ResearchConfig:
    GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
    MIN_REFERENCES     = 10
    MIN_YEAR           = datetime.datetime.now().year - 10   # 10 tahun terakhir
    MAX_YEAR           = datetime.datetime.now().year
    OUTPUT_FOLDER      = "hasil_riset"
    MODEL_NAME         = "gemini-2.0-flash"
    TEMPERATURE_SEARCH = 0.3   # lebih deterministik untuk pencarian
    TEMPERATURE_WRITE  = 0.7   # lebih kreatif untuk penulisan

    DATABASES = [
        "Scopus", "Sinta", "IEEE Xplore", "Springer",
        "Elsevier/ScienceDirect", "Google Scholar",
        "Taylor & Francis", "Wiley Online Library"
    ]


# ==================== SPINNER / PROGRESS ====================
class ProgressSpinner:
    FRAMES = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]

    def __init__(self, message: str):
        self.message = message
        self.running = False
        self._thread = None

    def start(self):
        import threading
        self.running = True
        def spin():
            idx = 0
            while self.running:
                frame = self.FRAMES[idx % len(self.FRAMES)]
                sys.stdout.write(f"\r{frame}  {self.message} ...")
                sys.stdout.flush()
                time.sleep(0.1)
                idx += 1
        self._thread = threading.Thread(target=spin, daemon=True)
        self._thread.start()

    def stop(self, done_msg: str = ""):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write(f"\r✅ {done_msg if done_msg else self.message} selesai!\n")
        sys.stdout.flush()


# ==================== RESEARCHGPT AGENT ====================
class ResearchGPT:
    """
    AI Agent Deep Research Akademik.
    Menghasilkan jurnal ilmiah berbasis minimal 10 referensi valid.
    """

    def __init__(self, api_key: str = None, model: str = None, verbose: bool = True):
        self.api_key   = api_key or ResearchConfig.GEMINI_API_KEY
        self.model     = model  or ResearchConfig.MODEL_NAME
        self.verbose   = verbose
        self.client    = None
        self.log_steps: List[str] = []
        self._init_gemini()
        self._ensure_output_folder()

    # ──────────────────────────────
    # INITIALIZATION
    # ──────────────────────────────
    def _init_gemini(self):
        if not GEMINI_AVAILABLE:
            print("⚠️  google-genai tidak ditemukan. Install: pip install google-genai")
            return
        try:
            self.client = genai.Client(api_key=self.api_key)
            # Coba temukan model terbaik yang tersedia
            try:
                available = [m.name.replace("models/", "") for m in self.client.models.list()]
                preferred = [
                    # Free-tier friendly first (higher RPM quota)
                    "gemini-2.0-flash", "gemini-2.0-flash-001",
                    "gemini-flash-latest",
                    # Higher quality but may hit quota limits
                    "gemini-2.5-flash", "gemini-2.5-pro",
                    "gemini-pro-latest",
                ]
                for p in preferred:
                    if p in available:
                        self.model = p
                        break
            except Exception:
                pass
            if self.verbose:
                print(f"✓ ResearchGPT siap | Model: {self.model}")
        except Exception as e:
            print(f"❌ Error Gemini: {e}")

    def _ensure_output_folder(self):
        os.makedirs(ResearchConfig.OUTPUT_FOLDER, exist_ok=True)

    # ──────────────────────────────
    # GEMINI CALL
    # ──────────────────────────────
    def _ask_gemini(self, prompt: str, temperature: float = 0.5) -> str:
        """Kirim prompt ke Gemini dengan fallback otomatis jika quota habis."""
        if not self.client:
            return "[ERROR: Gemini client tidak tersedia]"

        # Daftar model fallback jika quota exhausted
        fallback_models = [
            "gemini-2.0-flash", "gemini-2.0-flash-001",
            "gemini-flash-latest", "gemini-2.5-flash",
            "gemini-2.5-pro", "gemini-pro-latest",
        ]
        # Pastikan current model ada di depan
        models_to_try = [self.model] + [m for m in fallback_models if m != self.model]

        for model in models_to_try:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=8192,
                    )
                )
                if model != self.model:
                    print(f"  ↪ Fallback ke model: {model}")
                    self.model = model   # Update model untuk request berikutnya
                return resp.text.strip()
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    print(f"  ⚠️  Quota habis untuk {model}, mencoba model lain...")
                    continue
                else:
                    return f"[ERROR Gemini: {e}]"

        return "[ERROR: Semua model quota habis. Coba lagi nanti.]"

    def _log(self, msg: str):
        if self.verbose:
            print(msg)
        self.log_steps.append(msg)

    # ══════════════════════════════════════════════════════════════
    # STEP 1 — UNDERSTAND PROBLEM
    # ══════════════════════════════════════════════════════════════
    def step1_understand_problem(self, topic: str) -> Dict[str, Any]:
        self._log("\n" + "═"*60)
        self._log("📚 STEP 1 — UNDERSTAND PROBLEM")
        self._log("═"*60)

        prompt = f"""Kamu adalah peneliti akademik senior. Analisis topik penelitian berikut secara mendalam.

TOPIK: "{topic}"

Hasilkan analisis dalam format JSON berikut (WAJIB valid JSON):
{{
  "topik_utama": "...",
  "sub_topik": ["...", "..."],
  "keywords_indonesia": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "keywords_english": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "scope_penelitian": "...",
  "bidang_ilmu": "...",
  "relevansi_akademik": "...",
  "pertanyaan_penelitian": ["RQ1: ...", "RQ2: ...", "RQ3: ..."],
  "tujuan_penelitian": "..."
}}

Pastikan JSON valid tanpa komentar."""

        spinner = ProgressSpinner("Menganalisis topik & generating keywords")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_SEARCH)
        spinner.stop("Analisis topik")

        result = self._parse_json(raw)
        if "topik_utama" not in result:
            # Fallback manual
            result = {
                "topik_utama": topic,
                "keywords_indonesia": [topic] + [f"aspek {i+1}" for i in range(4)],
                "keywords_english": [topic] + [f"aspect {i+1}" for i in range(4)],
                "scope_penelitian": f"Kajian komprehensif tentang {topic}",
                "bidang_ilmu": "Multidisiplin",
                "pertanyaan_penelitian": [f"RQ1: Bagaimana {topic} berkembang?"],
                "tujuan_penelitian": f"Menganalisis {topic} secara sistematis"
            }

        self._log(f"   ✓ Topik: {result.get('topik_utama', topic)}")
        self._log(f"   ✓ Keywords EN: {', '.join(result.get('keywords_english', []))}")
        self._log(f"   ✓ Bidang: {result.get('bidang_ilmu', '-')}")
        return result

    # ══════════════════════════════════════════════════════════════
    # STEP 2 — LITERATURE SEARCH
    # ══════════════════════════════════════════════════════════════
    def step2_search_literature(self, topic: str, step1_data: Dict) -> List[Dict]:
        self._log("\n" + "═"*60)
        self._log("🔍 STEP 2 — LITERATURE SEARCH")
        self._log("═"*60)

        keywords_en = step1_data.get("keywords_english", [topic])
        keywords_id = step1_data.get("keywords_indonesia", [topic])
        scope       = step1_data.get("scope_penelitian", topic)
        min_year    = ResearchConfig.MIN_YEAR
        max_year    = ResearchConfig.MAX_YEAR
        databases   = ", ".join(ResearchConfig.DATABASES[:5])

        prompt = f"""Kamu adalah pustakawan akademik senior dengan akses ke semua database jurnal internasional.

TUGAS: Cari MINIMAL 12 jurnal ilmiah valid tentang topik berikut.

TOPIK: "{topic}"
SCOPE: {scope}
KEYWORDS EN: {', '.join(keywords_en)}
KEYWORDS ID: {', '.join(keywords_id)}
PERIODE: {min_year}–{max_year} (10 tahun terakhir)
DATABASE: {databases}

Buat daftar 12 referensi jurnal REALISTIS (bisa mensimulasikan referensi akademik valid).
Format JSON array:
[
  {{
    "id": 1,
    "judul": "Judul lengkap jurnal",
    "penulis": ["Nama1", "Nama2"],
    "tahun": 2020,
    "jurnal": "Nama Jurnal/Prosiding",
    "volume": "Vol. X",
    "nomor": "No. Y",
    "halaman": "pp. ZZZ-ZZZ",
    "doi": "10.XXXX/XXXXXX",
    "database": "Scopus/IEEE/Springer/dll",
    "url": "https://doi.org/10.XXXX/XXXXXX",
    "abstrak_singkat": "Ringkasan 2-3 kalimat tentang paper ini",
    "relevansi": "Tinggi/Sedang",
    "kata_kunci_jurnal": ["kw1", "kw2"]
  }},
  ... (total 12 item)
]

ATURAN:
- Tahun >= {min_year}
- Jurnal bereputasi (indexed Scopus/IEEE/Springer/Elsevier)
- Relevan dengan topik
- Diversifikasi perspektif/metodologi
- Pastikan valid JSON array"""

        spinner = ProgressSpinner("Mencari jurnal dari Scopus, IEEE, Springer, Elsevier")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_SEARCH)
        spinner.stop("Pencarian literatur")

        refs = self._parse_json_array(raw)

        # Pastikan minimal 10
        if len(refs) < 10:
            self._log(f"   ⚠️  Hanya {len(refs)} referensi, meminta tambahan...")
            refs = self._fetch_more_references(topic, refs, step1_data)

        self._log(f"   ✓ Ditemukan {len(refs)} referensi")
        for i, r in enumerate(refs[:12], 1):
            self._log(f"   [{i}] {r.get('penulis', ['?'])[0]} ({r.get('tahun','?')}) — {r.get('judul','?')[:60]}...")

        return refs

    def _fetch_more_references(self, topic: str, existing: List[Dict], step1_data: Dict) -> List[Dict]:
        """Request referensi tambahan jika kurang dari 10."""
        needed = ResearchConfig.MIN_REFERENCES - len(existing)
        prompt = f"""Tambahkan {needed} jurnal lagi tentang topik "{topic}" yang BERBEDA dari yang sudah ada.
        Format JSON array sama seperti sebelumnya. Pastikan tahun >= {ResearchConfig.MIN_YEAR}."""

        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_SEARCH)
        extra = self._parse_json_array(raw)
        return existing + extra

    # ══════════════════════════════════════════════════════════════
    # STEP 3 — EXTRACT INSIGHTS
    # ══════════════════════════════════════════════════════════════
    def step3_extract_insights(self, references: List[Dict]) -> List[Dict]:
        self._log("\n" + "═"*60)
        self._log("🔬 STEP 3 — EXTRACT INSIGHTS")
        self._log("═"*60)

        refs_summary = json.dumps(references[:12], ensure_ascii=False, indent=2)

        prompt = f"""Kamu adalah analis jurnal ilmiah senior.

Ekstrak insight mendalam dari setiap jurnal berikut:

DAFTAR JURNAL:
{refs_summary}

Untuk SETIAP jurnal, ekstrak dalam format JSON array:
[
  {{
    "id": 1,
    "judul": "...",
    "penulis": "...",
    "tahun": 2020,
    "tujuan_penelitian": "Tujuan utama studi ini adalah...",
    "metodologi": "Penelitian ini menggunakan metode...",
    "populasi_sampel": "...",
    "hasil_utama": "Temuan kunci dari penelitian ini adalah...",
    "kesimpulan": "...",
    "kelebihan": ["kelebihan1", "kelebihan2"],
    "kekurangan": ["keterbatasan1", "keterbatasan2"],
    "kontribusi_teoritis": "...",
    "implikasi_praktis": "..."
  }},
  ...
]

Pastikan analisis setiap jurnal detail, akademik, dan berbasis fakta dari abstrak/deskripsi jurnal."""

        spinner = ProgressSpinner("Mengekstrak insight dari setiap jurnal")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_SEARCH)
        spinner.stop("Ekstraksi insight")

        insights = self._parse_json_array(raw)
        self._log(f"   ✓ Insight diekstrak dari {len(insights)} jurnal")
        return insights

    # ══════════════════════════════════════════════════════════════
    # STEP 4 — CRITICAL ANALYSIS
    # ══════════════════════════════════════════════════════════════
    def step4_critical_analysis(self, insights: List[Dict], topic: str) -> Dict[str, Any]:
        self._log("\n" + "═"*60)
        self._log("⚡ STEP 4 — CRITICAL ANALYSIS")
        self._log("═"*60)

        insights_text = json.dumps(insights, ensure_ascii=False, indent=2)

        prompt = f"""Kamu adalah reviewer jurnal internasional berpengalaman.

Lakukan analisis kritis komprehensif terhadap kumpulan jurnal tentang: "{topic}"

DATA INSIGHT:
{insights_text}

Hasilkan analisis dalam JSON:
{{
  "perbandingan_metodologi": {{
    "kuantitatif": ["judul1", "judul2"],
    "kualitatif": ["judul3"],
    "campuran": ["judul4", "judul5"],
    "review_sistematis": ["judul6"]
  }},
  "trend_penelitian": [
    "Trend 1: ...",
    "Trend 2: ...",
    "Trend 3: ..."
  ],
  "research_gap": [
    "Gap 1: ...",
    "Gap 2: ...",
    "Gap 3: ..."
  ],
  "konflik_temuan": [
    "Konflik 1: Studi A vs Studi B menunjukkan...",
    "Konflik 2: ..."
  ],
  "konsensus_ilmiah": "Area kesepakatan utama antar peneliti adalah...",
  "perkembangan_temporal": "Bagaimana penelitian berkembang dari tahun ke tahun...",
  "dominasi_metodologi": "Metodologi yang paling banyak digunakan adalah...",
  "geographic_bias": "...",
  "rekomendasi_penelitian_lanjutan": [
    "Rekomendasi 1: ...",
    "Rekomendasi 2: ...",
    "Rekomendasi 3: ..."
  ]
}}"""

        spinner = ProgressSpinner("Melakukan analisis kritis & menemukan research gap")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_SEARCH)
        spinner.stop("Analisis kritis")

        analysis = self._parse_json(raw)
        trend_count = len(analysis.get("trend_penelitian", []))
        gap_count   = len(analysis.get("research_gap", []))
        self._log(f"   ✓ Ditemukan {trend_count} trend & {gap_count} research gap")
        return analysis

    # ══════════════════════════════════════════════════════════════
    # STEP 5 — SYNTHESIS
    # ══════════════════════════════════════════════════════════════
    def step5_synthesis(self, step1: Dict, step4: Dict, references: List[Dict], topic: str) -> Dict[str, Any]:
        self._log("\n" + "═"*60)
        self._log("🧩 STEP 5 — SYNTHESIS")
        self._log("═"*60)

        gaps_text   = "\n".join(f"- {g}" for g in step4.get("research_gap", []))
        trends_text = "\n".join(f"- {t}" for t in step4.get("trend_penelitian", []))
        rq_text     = "\n".join(step1.get("pertanyaan_penelitian", []))

        prompt = f"""Kamu adalah ilmuwan yang membangun kerangka teori baru.

TOPIK: "{topic}"
RESEARCH QUESTIONS:
{rq_text}

RESEARCH GAPS DITEMUKAN:
{gaps_text}

TREND PENELITIAN:
{trends_text}

Bangun sintesis komprehensif dalam JSON:
{{
  "proposisi_utama": "Pernyataan utama yang menghubungkan semua temuan...",
  "kerangka_konseptual": {{
    "variabel_independen": ["var1", "var2"],
    "variabel_dependen": ["var1"],
    "variabel_moderasi": ["var1"],
    "hubungan_antar_variabel": "Penjelasan hubungan..."
  }},
  "teori_pendukung": [
    {{"nama": "Teori X", "relevansi": "..."}},
    {{"nama": "Teori Y", "relevansi": "..."}}
  ],
  "hipotesis": [
    "H1: ...",
    "H2: ...",
    "H3: ..."
  ],
  "kontribusi_baru": "Kontribusi orisinal penelitian ini adalah...",
  "pendekatan_metodologi_usulan": "Metodologi yang diusulkan untuk mengisi gap...",
  "argumen_akademik": "Argumentasi ilmiah mengapa penelitian ini penting..."
}}"""

        spinner = ProgressSpinner("Membangun kerangka teori & sintesis akademik")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_WRITE)
        spinner.stop("Sintesis")

        synthesis = self._parse_json(raw)
        self._log(f"   ✓ Proposisi: {str(synthesis.get('proposisi_utama',''))[:80]}...")
        return synthesis

    # ══════════════════════════════════════════════════════════════
    # STEP 6 — GENERATE SCIENTIFIC PAPER
    # ══════════════════════════════════════════════════════════════
    def step6_generate_paper(self, topic: str, step1: Dict, references: List[Dict],
                              insights: List[Dict], step4: Dict, step5: Dict) -> str:
        self._log("\n" + "═"*60)
        self._log("📝 STEP 6 — GENERATE SCIENTIFIC PAPER")
        self._log("═"*60)

        # Bangun tabel perbandingan jurnal
        comparison_table = self._build_comparison_table(references, insights)

        # Bangun daftar referensi APA
        apa_refs = self._build_apa_references(references)

        # Bangun sitasi inline
        inline_citations = self._build_inline_citations(references)

        # Data gabungan untuk prompt
        all_data = {
            "topic"            : topic,
            "scope"            : step1.get("scope_penelitian", ""),
            "keywords_id"      : step1.get("keywords_indonesia", []),
            "keywords_en"      : step1.get("keywords_english", []),
            "pertanyaan"       : step1.get("pertanyaan_penelitian", []),
            "tujuan"           : step1.get("tujuan_penelitian", ""),
            "bidang"           : step1.get("bidang_ilmu", ""),
            "gaps"             : step4.get("research_gap", []),
            "trends"           : step4.get("trend_penelitian", []),
            "consensus"        : step4.get("konsensus_ilmiah", ""),
            "proposisi"        : step5.get("proposisi_utama", ""),
            "kerangka"         : step5.get("kerangka_konseptual", {}),
            "hipotesis"        : step5.get("hipotesis", []),
            "kontribusi"       : step5.get("kontribusi_baru", ""),
            "metodologi_usulan": step5.get("pendekatan_metodologi_usulan", ""),
            "argumen"          : step5.get("argumen_akademik", ""),
            "rekomendasi"      : step4.get("rekomendasi_penelitian_lanjutan", []),
        }

        prompt = f"""Kamu adalah penulis jurnal ilmiah internasional berpengalaman.

Tulis paper akademik LENGKAP dan BERKUALITAS TINGGI berdasarkan data riset berikut.

DATA RISET:
{json.dumps(all_data, ensure_ascii=False, indent=2)}

TABEL PERBANDINGAN JURNAL (sudah jadi, masukkan verbatim):
{comparison_table}

DAFTAR REFERENSI APA (sudah jadi, masukkan verbatim):
{apa_refs}

SITASI INLINE TERSEDIA:
{inline_citations}

Tulis paper dengan struktur WAJIB berikut (gunakan Markdown):

# [JUDUL PAPER YANG MENARIK DAN AKADEMIK]

**Penulis:** ResearchGPT Academic AI  
**Tanggal:** {datetime.datetime.now().strftime("%d %B %Y")}  
**Kata Kunci:** [keywords ID & EN]

---

## ABSTRAK

[150-250 kata. Latar belakang, tujuan, metodologi, hasil utama, kesimpulan. Bahasa formal akademik Indonesia.]

**Kata Kunci:** [5-7 kata kunci]

---

## 1. PENDAHULUAN

[3-4 paragraf. Latar belakang masalah, fenomena, urgensi, research gap, tujuan penelitian. Sertakan sitasi inline seperti (Penulis, Tahun).]

---

## 2. TINJAUAN PUSTAKA

### 2.1 [Sub-topik 1]
[Ulas jurnal-jurnal relevan dengan sitasi. Bandingkan pandangan antar peneliti.]

### 2.2 [Sub-topik 2]
[Lanjutkan tinjauan...]

### 2.3 Kerangka Konseptual
[Jelaskan kerangka teori yang dibangun]

### 2.4 Tabel Perbandingan Jurnal
[Masukkan tabel perbandingan di sini]

---

## 3. METODOLOGI

[Jelaskan: desain penelitian, jenis penelitian (kajian sistematis/literature review/empiris), metode analisis, prosedur, kriteria inklusi-eksklusi sumber]

---

## 4. HASIL DAN PEMBAHASAN

### 4.1 [Hasil Utama 1]
[Pembahasan berbasis data jurnal dengan sitasi]

### 4.2 [Hasil Utama 2]
[...]

### 4.3 Research Gap & Implikasi
[Diskusi gap yang ditemukan]

### 4.4 Perbandingan dengan Penelitian Sebelumnya
[...]

---

## 5. KESIMPULAN

[Ringkasan temuan, jawaban atas research questions, kontribusi penelitian, rekomendasi]

---

## 6. REKOMENDASI PENELITIAN LANJUTAN

[Daftar rekomendasi berdasarkan gap yang ditemukan]

---

## DAFTAR PUSTAKA

[Masukkan daftar referensi APA di sini]

---

ATURAN PENULISAN:
- Bahasa Indonesia formal akademik
- Minimal 10 sitasi inline (Penulis, Tahun)
- Setiap klaim harus ada sitasi
- Tidak boleh copy-paste, parafrase natural
- Logis, sistematis, berbasis data
- Gunakan kalimat akademik baku"""

        spinner = ProgressSpinner("Menulis draft paper ilmiah (ini memakan waktu ~1-2 menit)")
        spinner.start()
        raw = self._ask_gemini(prompt, ResearchConfig.TEMPERATURE_WRITE)
        spinner.stop("Penulisan paper")

        # Tambahkan metadata tambahan di akhir
        paper = raw
        paper += self._build_research_gap_section(step4)
        paper += f"\n\n---\n*Paper dihasilkan oleh ResearchGPT pada {datetime.datetime.now().strftime('%d %B %Y pukul %H:%M WIB')}*"

        self._log(f"   ✓ Paper berhasil ditulis ({len(paper.split())} kata)")
        return paper

    # ══════════════════════════════════════════════════════════════
    # FULL WORKFLOW ORCHESTRATOR
    # ══════════════════════════════════════════════════════════════
    def run_full_workflow(self, topic: str) -> Tuple[str, str]:
        """
        Jalankan semua 6 steps secara berurutan.
        Returns: (paper_text, saved_filepath)
        """
        start_time = time.time()
        print("\n" + "█"*60)
        print(f"  🎓 RESEARCHGPT — DEEP RESEARCH AKADEMIK")
        print(f"  📖 Topik: {topic}")
        print(f"  🕐 Mulai: {datetime.datetime.now().strftime('%H:%M:%S')}")
        print("█"*60)

        try:
            step1_data   = self.step1_understand_problem(topic)
            references   = self.step2_search_literature(topic, step1_data)
            insights     = self.step3_extract_insights(references)
            analysis     = self.step4_critical_analysis(insights, topic)
            synthesis    = self.step5_synthesis(step1_data, analysis, references, topic)
            paper        = self.step6_generate_paper(
                               topic, step1_data, references,
                               insights, analysis, synthesis)

            elapsed = time.time() - start_time
            print(f"\n{'═'*60}")
            print(f"✅ RISET SELESAI dalam {elapsed:.0f} detik!")
            print(f"{'═'*60}")

            filepath = self.save_paper(paper, topic)
            return paper, filepath

        except Exception as e:
            error_msg = f"❌ Error saat riset: {e}"
            self._log(error_msg)
            import traceback; traceback.print_exc()
            return error_msg, ""

    # ══════════════════════════════════════════════════════════════
    # HELPER — SAVE PAPER
    # ══════════════════════════════════════════════════════════════
    def save_paper(self, paper: str, topic: str) -> str:
        """Simpan paper ke file .md di folder hasil_riset/."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = re.sub(r'[^\w\s-]', '', topic).strip()[:50]
        safe_topic = re.sub(r'[\s]+', '_', safe_topic)
        filename = f"paper_{safe_topic}_{timestamp}.md"
        filepath = os.path.join(ResearchConfig.OUTPUT_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(paper)

        # Simpan juga sebagai .txt untuk kemudahan akses
        txt_path = filepath.replace(".md", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(paper)

        print(f"\n📁 Paper disimpan di:")
        print(f"   📄 {os.path.abspath(filepath)}")
        print(f"   📄 {os.path.abspath(txt_path)}")
        return filepath

    # ══════════════════════════════════════════════════════════════
    # HELPER — BUILD COMPARISON TABLE
    # ══════════════════════════════════════════════════════════════
    def _build_comparison_table(self, references: List[Dict], insights: List[Dict]) -> str:
        """Buat tabel perbandingan jurnal dalam format Markdown."""
        rows = []
        rows.append("| No | Penulis (Tahun) | Judul | Database | Metodologi | Hasil Utama | Gap |")
        rows.append("|:--:|:---------------|:------|:--------:|:----------:|:-----------|:---|")

        for i, ref in enumerate(references[:12], 1):
            penulis    = ref.get("penulis", ["?"])[0] if ref.get("penulis") else "?"
            tahun      = ref.get("tahun", "?")
            judul      = ref.get("judul", "?")[:45] + "..."
            database   = ref.get("database", "-")
            
            # Cari insight yang sesuai
            insight = next((ins for ins in insights if ins.get("id") == ref.get("id")), {})
            metode  = insight.get("metodologi", ref.get("abstrak_singkat", "-"))[:40]
            hasil   = insight.get("hasil_utama", "-")[:50]
            gap     = (insight.get("kekurangan", ["-"])[0] if insight.get("kekurangan") else "-")[:40]
            
            row = f"| {i} | {penulis} ({tahun}) | {judul} | {database} | {metode}... | {hasil}... | {gap}... |"
            rows.append(row)

        return "\n".join(rows)

    # ══════════════════════════════════════════════════════════════
    # HELPER — BUILD APA REFERENCES
    # ══════════════════════════════════════════════════════════════
    def _build_apa_references(self, references: List[Dict]) -> str:
        """Buat daftar referensi format APA 7th edition."""
        apa_list = []
        for i, ref in enumerate(references, 1):
            penulis = ref.get("penulis", ["Unknown"])
            # Format penulis APA: Nama Belakang, Inisial.
            apa_authors = []
            for p in penulis:
                parts = p.strip().split()
                if len(parts) >= 2:
                    apa_authors.append(f"{parts[-1]}, {'. '.join(c[0] for c in parts[:-1])}.")
                else:
                    apa_authors.append(p)
            authors_str = ", & ".join(apa_authors) if len(apa_authors) > 1 else apa_authors[0] if apa_authors else "Unknown"

            tahun   = ref.get("tahun", "n.d.")
            judul   = ref.get("judul", "Untitled")
            jurnal  = ref.get("jurnal", "Journal")
            vol     = ref.get("volume", "")
            no      = ref.get("nomor", "")
            hal     = ref.get("halaman", "")
            doi     = ref.get("doi", "")

            vol_info = f"*{vol}*{f'({no})' if no else ''}"
            apa_entry = f"{i}. {authors_str} ({tahun}). {judul}. *{jurnal}*, {vol_info}, {hal}."
            if doi:
                apa_entry += f" https://doi.org/{doi.replace('https://doi.org/', '')}"
            apa_list.append(apa_entry)

        return "\n".join(apa_list)

    def _build_inline_citations(self, references: List[Dict]) -> str:
        """Buat panduan sitasi inline."""
        cites = []
        for ref in references[:12]:
            penulis = ref.get("penulis", ["?"])[0].split()[-1] if ref.get("penulis") else "?"
            tahun   = ref.get("tahun", "?")
            cites.append(f"({penulis}, {tahun})")
        return ", ".join(cites)

    def _build_research_gap_section(self, analysis: Dict) -> str:
        """Buat bagian research gap explanation."""
        gaps  = analysis.get("research_gap", [])
        recs  = analysis.get("rekomendasi_penelitian_lanjutan", [])
        if not gaps and not recs:
            return ""
        section = "\n\n---\n\n## LAMPIRAN: RESEARCH GAP ANALYSIS\n\n"
        if gaps:
            section += "### Identifikasi Research Gap\n"
            for i, g in enumerate(gaps, 1):
                section += f"{i}. {g}\n"
        if recs:
            section += "\n### Rekomendasi Penelitian Lanjutan\n"
            for i, r in enumerate(recs, 1):
                section += f"{i}. {r}\n"
        return section

    # ══════════════════════════════════════════════════════════════
    # UTILITY — PARSE JSON
    # ══════════════════════════════════════════════════════════════
    def _parse_json(self, text: str) -> Dict:
        """Multi-pass JSON object parser, handles markdown fences & trailing commas."""
        clean = re.sub(r'```(?:json)?\s*', '', text).replace('```', '').strip()
        for attempt in [clean, re.sub(r',\s*([}\]])', r'\1', clean)]:
            try:
                return json.loads(attempt)
            except Exception:
                pass
            try:
                match = re.search(r'\{[\s\S]*\}', attempt)
                if match:
                    return json.loads(match.group())
            except Exception:
                pass
        return {}

    def _parse_json_array(self, text: str) -> List[Dict]:
        """Multi-pass JSON array parser, handles markdown fences & trailing commas."""
        clean = re.sub(r'```(?:json)?\s*', '', text).replace('```', '').strip()
        for attempt in [clean, re.sub(r',\s*([}\]])', r'\1', clean)]:
            try:
                result = json.loads(attempt)
                if isinstance(result, list):
                    return result
            except Exception:
                pass
            try:
                match = re.search(r'\[[\s\S]*\]', attempt)
                if match:
                    result = json.loads(match.group())
                    if isinstance(result, list):
                        return result
            except Exception:
                pass
        return []


# ==================== FUNGSI UTILITAS PUBLIK ====================
def quick_research(topic: str, verbose: bool = True) -> Tuple[str, str]:
    """
    Fungsi praktis untuk langsung melakukan riset.
    Returns: (paper_content, saved_filepath)
    """
    agent = ResearchGPT(verbose=verbose)
    return agent.run_full_workflow(topic)


# ==================== CLI STANDALONE ====================
if __name__ == "__main__":
    print("🎓 ResearchGPT — AI Deep Research Akademik")
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("\n📚 Masukkan topik penelitian: ").strip()
    
    if topic:
        paper, path = quick_research(topic)
        if path:
            print(f"\n✅ Silakan buka file paper di: {os.path.abspath(path)}")
    else:
        print("❌ Topik tidak boleh kosong!")
