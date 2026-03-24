# PDF-Ara

Seçilen klasördeki PDF dosyalarında çoklu metin arama aracı.

## Özellikler

- Klasör seç, arama terimlerini gir, **Ara**
- Tüm terimlerin geçtiği PDF'leri listeler (AND mantığı)
- Büyük/küçük harf duyarsız, substring arama
- Sonuca çift tıkla → Windows varsayılan uygulamasıyla açar
- Alt klasörlere bakmaz, sadece seçilen klasör

## Kullanım

`PDF-Ara.exe`'yi indirip çalıştır. Python kurulumu gerekmez.

## Geliştirici Kurulumu

```bash
git clone https://github.com/SerkanC1/pdf-ara.git
cd pdf-ara
pip install -r requirements.txt
pythonw pdf_ara_gui.pyw
```

## .exe Derleme

```bash
pyinstaller --onefile --windowed --name "PDF-Ara" pdf_ara_gui.pyw
```

Çıktı: `dist/PDF-Ara.exe`

## Bağımlılıklar

- [PyMuPDF](https://pymupdf.readthedocs.io/) (fitz)
