"""
pdf_ara.py - Ana dizindeki PDF dosyalarinda coklu metin arama
=============================================================
AMAC:
  - Sadece scriptin bulundugu ANA DIZINDEKI PDF leri tarar (alt klasor yok).
  - Verilen TUM metinlerin ayni PDF icinde gecmesini arar (AND mantigi).
  - Her metin SUBSTRING olarak aranir: "wheel" yazsan "wheelhouse" da bulur.
  - Buyuk/kucuk harf DUYARSIZDIR.

KULLANIM (CMD veya PowerShell):
  python pdf_ara.py "metin1"
  python pdf_ara.py "metin1" "metin2" "metin3"

ORNEK:
  python pdf_ara.py "850W"
  python pdf_ara.py "850" "wheel" "fly"
  python pdf_ara.py "850W" "ET1" "ET2"

BAGIMLILIK:
  pip install pymupdf

NOT:
  - Global Python ile calisir, .venv gerekmez.
  - Farkli klasorlere kopyalanip kullanilabilir.
  - python komutu PATH'de yoksa tam yolu kullanin:
    C:/Users/Serkan/AppData/Local/Programs/Python/Python313/python.exe pdf_ara.py ...
"""

import sys
import os
import fitz  # PyMuPDF

# MuPDF'in C katmanindan gelen stderr uyarilarini sustur
fitz.TOOLS.mupdf_display_errors(False)

def main():
    if len(sys.argv) < 2:
        print("Kullanim: python pdf_ara.py \"metin1\" [\"metin2\"] ...")
        print("Ornek   : python pdf_ara.py \"850W\" \"ET1\" \"ET2\"")
        sys.exit(2)

    terms = [t.lower() for t in sys.argv[1:]]
    script_dir = os.path.dirname(os.path.abspath(__file__))

    pdf_files = sorted(
        f for f in os.listdir(script_dir)
        if f.lower().endswith(".pdf")
    )

    if not pdf_files:
        print("Ana dizinde PDF bulunamadi:", script_dir)
        sys.exit(0)

    found_any = False

    for filename in pdf_files:
        filepath = os.path.join(script_dir, filename)
        try:
            fitz.TOOLS.mupdf_warnings()  # onceki uyarilari temizle
            doc = fitz.open(filepath)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
            fitz.TOOLS.mupdf_warnings()  # bu PDF'in uyarilarini gizle
            full_text_lower = full_text.lower()

            if all(term in full_text_lower for term in terms):
                print(filename)
                found_any = True
        except Exception:
            fitz.TOOLS.mupdf_warnings()  # hata durumunda da temizle

    if not found_any:
        print("Eslesen PDF bulunamadi.")

if __name__ == "__main__":
    main()
