# ==================== RUN RESEARCH — ENTRY POINT RESEARCHGPT ====================
# Jalankan: python run_research.py
# Atau dengan argumen: python run_research.py "Machine Learning dalam Pendidikan"
# =================================================================================

import sys
import os
import time
import datetime

# Pastikan direktori saat ini ada di path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from research_gpt import ResearchGPT, ResearchConfig


def print_banner():
    """Tampilkan banner ResearchGPT."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🎓  R E S E A R C H G P T  —  Deep Academic Research AI      ║
║                                                                  ║
║    ✅ Minimal 10 referensi jurnal valid                          ║
║    ✅ Scopus | IEEE | Springer | Elsevier | Google Scholar       ║
║    ✅ 10 tahun terakhir                                          ║
║    ✅ Paper ilmiah siap revisi dosen                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_workflow_steps():
    """Tampilkan langkah-langkah workflow."""
    steps = [
        ("STEP 1", "📚 Understand Problem     — Analisis topik & generate keywords"),
        ("STEP 2", "🔍 Literature Search      — Cari 10+ jurnal valid"),
        ("STEP 3", "🔬 Extract Insights       — Analisis setiap jurnal"),
        ("STEP 4", "⚡ Critical Analysis      — Research gap & trend"),
        ("STEP 5", "🧩 Synthesis             — Kerangka teori baru"),
        ("STEP 6", "📝 Generate Paper        — Draft jurnal siap revisi"),
    ]
    print("  📋 WORKFLOW:")
    for code, desc in steps:
        print(f"     [{code}] {desc}")
    print()


def get_topic_from_user() -> str:
    """Tanyakan topik riset kepada user."""
    print("  💡 Contoh topik:")
    examples = [
        "Machine Learning dalam Sistem Deteksi Penyakit Kanker",
        "Blockchain untuk Keamanan Data Rekam Medis",
        "Deep Learning dalam Natural Language Processing Bahasa Indonesia",
        "Artificial Intelligence untuk Prediksi Perubahan Iklim",
        "Internet of Things dalam Smart Agriculture",
    ]
    for ex in examples:
        print(f"     • {ex}")
    print()
    
    while True:
        topic = input("  📚 Masukkan topik penelitian Anda: ").strip()
        if len(topic) >= 5:
            return topic
        print("  ⚠️  Topik terlalu pendek, minimal 5 karakter.\n")


def confirm_research(topic: str) -> bool:
    """Konfirmasi sebelum memulai riset."""
    print(f"\n  🎯 Topik: '{topic}'")
    print(f"  ⏱️  Estimasi waktu: 3–8 menit")
    print(f"  📁 Output: folder hasil_riset/\n")
    confirm = input("  ▶️  Mulai riset? (y/n): ").strip().lower()
    return confirm in ['y', 'ya', 'yes', '']


def show_paper_preview(paper: str, filepath: str):
    """Tampilkan preview 40 baris pertama paper."""
    print("\n" + "═"*70)
    print("  📄 PREVIEW PAPER (40 baris pertama):")
    print("═"*70)
    lines = paper.split('\n')
    for i, line in enumerate(lines[:40]):
        print(f"  {line}")
    if len(lines) > 40:
        print(f"\n  ... ({len(lines) - 40} baris lagi)")
    print("═"*70)
    
    abs_path = os.path.abspath(filepath)
    print(f"\n  📁 File lengkap tersimpan di:")
    print(f"     {abs_path}")
    print(f"\n  📊 Statistik paper:")
    word_count = len(paper.split())
    char_count = len(paper)
    line_count = len(lines)
    print(f"     • Jumlah kata : {word_count:,}")
    print(f"     • Karakter    : {char_count:,}")
    print(f"     • Baris       : {line_count:,}")


def research_menu():
    """Menu interaktif untuk ResearchGPT."""
    print_banner()
    print_workflow_steps()
    
    # Dapatkan topik
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
        print(f"  📚 Topik dari argumen: '{topic}'")
    else:
        topic = get_topic_from_user()
    
    # Konfirmasi
    if not confirm_research(topic):
        print("\n  ❌ Riset dibatalkan.\n")
        return
    
    # Mulai riset
    start_time = time.time()
    agent = ResearchGPT(verbose=True)
    paper, filepath = agent.run_full_workflow(topic)
    elapsed = time.time() - start_time
    
    if not filepath:
        print("\n  ❌ Riset gagal. Cek error di atas.")
        return
    
    # Tampilkan preview
    show_paper_preview(paper, filepath)
    
    print(f"\n  ✅ Selesai dalam {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print("\n  📌 LANGKAH SELANJUTNYA:")
    print("     1. Buka file .md dengan VS Code / Typora untuk tampilan terbaik")
    print("     2. Review dan revisi sesuai kebutuhan")
    print("     3. Submit ke dosen / konferensi")
    print("\n" + "═"*70 + "\n")
    
    # Tanya apakah mau riset lagi
    again = input("  🔄 Riset topik lain? (y/n): ").strip().lower()
    if again in ['y', 'ya', 'yes']:
        print()
        research_menu()


# ==================== MAIN ====================
if __name__ == "__main__":
    try:
        research_menu()
    except KeyboardInterrupt:
        print("\n\n  ⏹️  ResearchGPT dihentikan. Sampai jumpa!\n")
    except Exception as e:
        print(f"\n  ❌ Error tidak terduga: {e}")
        import traceback
        traceback.print_exc()
