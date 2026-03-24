#!/usr/bin/env bash
# =============================================================
# pdf_ara.sh - Ana dizindeki PDF dosyalarinda coklu metin arama
# =============================================================
# AMAC:
#   - Sadece scriptin bulundugu ANA DIZINDEKI PDF leri tarar.
#   - Alt klasorlere BAKMAZ.
#   - Verilen TUM metinlerin ayni PDF icinde gecmesini arar (AND).
#   - Her metin SUBSTRING olarak aranir:
#       "wheel" yazsan "wheelhouse" icinde de bulur.
#   - Buyuk/kucuk harf DUYARSIZDIR: "850w" = "850W"
#
# KULLANIM:
#   bash pdf_ara.sh "metin1"
#   bash pdf_ara.sh "metin1" "metin2" "metin3"
#
# ORNEK:
#   bash pdf_ara.sh "850"
#   bash pdf_ara.sh "850" "wheel" "fly"
#   bash pdf_ara.sh "850W" "ET1" "ET2"
#
# BAGIMLILIK:
#   pdfgrep veya pdftotext (Poppler) kurulu olmali.
#   Git Bash icerisinde calistirilir.
# =============================================================

if [ $# -eq 0 ]; then
    echo "Kullanim: bash pdf_ara.sh \"metin1\" [\"metin2\"] [\"metin3\"] ..."
    echo "Ornek   : bash pdf_ara.sh \"850\" \"wheel\" \"fly\""
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v pdfgrep >/dev/null 2>&1; then
    TOOL=pdfgrep
elif command -v pdftotext >/dev/null 2>&1; then
    TOOL=pdftotext
else
    echo "HATA: 'pdfgrep' veya 'pdftotext' bulunamadi."
    exit 2
fi

found_any=0

for f in "$SCRIPT_DIR"/*.pdf "$SCRIPT_DIR"/*.PDF; do
    [ -e "$f" ] || continue
    all_found=1

    if [ "$TOOL" = "pdfgrep" ]; then
        for term in "$@"; do
            pdfgrep -qi -- "$term" "$f" 2>/dev/null || { all_found=0; break; }
        done
    else
        content="$(pdftotext -q "$f" - 2>/dev/null)" || { all_found=0; continue; }
        for term in "$@"; do
            printf '%s' "$content" | grep -qi -- "$term" 2>/dev/null || { all_found=0; break; }
        done
    fi

    if [ "$all_found" -eq 1 ]; then
        printf '%s\n' "$(basename "$f")"
        found_any=1
    fi
done

if [ "$found_any" -eq 0 ]; then
    echo "Eslesen PDF bulunamadi."
fi
