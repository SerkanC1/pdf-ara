"""
pdf_ara_gui.pyw - PDF dosyalarinda coklu metin arama (Windows GUI)
==================================================================
Kullanim:
  - Klasor sec
  - Aramak istedigin metinleri kutulara yaz (en az 1, istedigin kadar)
  - Ara butonuna bas
  - Sonuca cift tikla → Windows varsayilan uygulamasiyla ac

Bagimlilik: pymupdf (pip install pymupdf)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

try:
    import fitz  # PyMuPDF
    fitz.TOOLS.mupdf_display_errors(False)
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

ROOT_BG = "#f5f5f5"
ACCENT  = "#0078d4"
BTN_FG  = "#ffffff"
ENTRY_BG = "#ffffff"
LIST_BG  = "#ffffff"
LIST_SEL = "#cce4f7"


class PdfAraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF-Ara")
        self.geometry("720x600")
        self.minsize(600, 500)
        self.configure(bg=ROOT_BG)
        self.resizable(True, True)

        self.selected_folder = ""
        self.term_entries: list[tk.Entry] = []
        self.result_files: list[str] = []
        self._search_thread: threading.Thread | None = None
        self._cancel_event = threading.Event()

        self._build_ui()

    # ------------------------------------------------------------------
    # UI İnşa
    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # ── Başlık ──────────────────────────────────────────────────────
        tk.Label(
            self, text="PDF-Ara", font=("Segoe UI", 16, "bold"),
            bg=ROOT_BG, fg=ACCENT
        ).pack(anchor="w", padx=12, pady=(12, 0))

        tk.Label(
            self, text="Seçilen klasördeki PDF dosyalarında metin arar (AND mantığı)",
            font=("Segoe UI", 9), bg=ROOT_BG, fg="#555"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── Klasör Seçimi ────────────────────────────────────────────────
        frm_folder = tk.Frame(self, bg=ROOT_BG)
        frm_folder.pack(fill="x", **pad)

        tk.Label(frm_folder, text="Klasör:", font=("Segoe UI", 10),
                 bg=ROOT_BG, width=8, anchor="w").pack(side="left")

        self.folder_var = tk.StringVar(value="Henüz klasör seçilmedi…")
        tk.Entry(
            frm_folder, textvariable=self.folder_var, state="readonly",
            font=("Segoe UI", 9), bg="#e8e8e8", relief="flat",
            readonlybackground="#e8e8e8"
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_folder = tk.Button(
            frm_folder, text="Klasör Seç", command=self._choose_folder,
            bg=ACCENT, fg=BTN_FG, font=("Segoe UI", 9, "bold"),
            relief="flat", padx=10, cursor="hand2"
        )
        self.btn_folder.pack(side="left")

        tk.Frame(self, bg="#d0d0d0", height=1).pack(fill="x", padx=12)

        # ── Arama Terimleri ──────────────────────────────────────────────
        tk.Label(self, text="Arama Terimleri", font=("Segoe UI", 10, "bold"),
                 bg=ROOT_BG).pack(anchor="w", padx=12, pady=(8, 2))

        tk.Label(
            self,
            text="Dolu olan tüm kutulardaki terimler PDF içinde bulunmalıdır (AND).",
            font=("Segoe UI", 8), bg=ROOT_BG, fg="#666"
        ).pack(anchor="w", padx=12)

        # Kaydırılabilir terim çerçevesi
        self.terms_outer = tk.Frame(self, bg=ROOT_BG)
        self.terms_outer.pack(fill="x", padx=12, pady=(4, 0))

        self.terms_frame = tk.Frame(self.terms_outer, bg=ROOT_BG)
        self.terms_frame.pack(fill="x")

        for _ in range(5):
            self._add_term_entry()

        frm_add = tk.Frame(self, bg=ROOT_BG)
        frm_add.pack(anchor="w", padx=12, pady=(4, 4))
        tk.Button(
            frm_add, text="+ Kutu Ekle", command=self._add_term_entry,
            bg="#e0e0e0", fg="#333", font=("Segoe UI", 8),
            relief="flat", padx=8, cursor="hand2"
        ).pack(side="left")
        tk.Button(
            frm_add, text="Tümünü Temizle", command=self._clear_terms,
            bg="#e0e0e0", fg="#333", font=("Segoe UI", 8),
            relief="flat", padx=8, cursor="hand2"
        ).pack(side="left", padx=(6, 0))

        tk.Frame(self, bg="#d0d0d0", height=1).pack(fill="x", padx=12)

        # ── Ara / Durdur Butonu ──────────────────────────────────────────
        self.btn_search = tk.Button(
            self, text="🔍  Ara", command=self._on_search_button,
            bg=ACCENT, fg=BTN_FG, font=("Segoe UI", 11, "bold"),
            relief="flat", padx=20, pady=6, cursor="hand2"
        )
        self.btn_search.pack(pady=8)

        # ── İlerleme Çubuğu ─────────────────────────────────────────────
        self.progress = ttk.Progressbar(
            self, orient="horizontal", mode="determinate"
        )
        self.progress.pack(fill="x", padx=12, pady=(0, 4))

        # ── Durum etiketi ────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.lbl_status = tk.Label(
            self, textvariable=self.status_var,
            font=("Segoe UI", 9), bg=ROOT_BG, fg="#444", anchor="w"
        )
        self.lbl_status.pack(fill="x", padx=12)

        # ── Sonuç Listesi ────────────────────────────────────────────────
        frm_list = tk.Frame(self, bg=ROOT_BG)
        frm_list.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        scrollbar = tk.Scrollbar(frm_list, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            frm_list, yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10), bg=LIST_BG, relief="flat",
            selectbackground=LIST_SEL, selectforeground="#000",
            activestyle="none", cursor="hand2"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", self._open_file)

        # Enter ile arama, Escape ile durdurma
        self.bind("<Return>", lambda e: self._on_search_button())
        self.bind("<Escape>", lambda e: self._request_cancel())

    # ------------------------------------------------------------------
    # Yardımcı Metotlar
    # ------------------------------------------------------------------
    def _add_term_entry(self):
        idx = len(self.term_entries) + 1
        frm = tk.Frame(self.terms_frame, bg=ROOT_BG)
        frm.pack(fill="x", pady=2)

        tk.Label(frm, text=f"{idx}.", font=("Segoe UI", 9),
                 bg=ROOT_BG, width=3, anchor="e").pack(side="left")

        entry = tk.Entry(
            frm, font=("Segoe UI", 10), bg=ENTRY_BG,
            relief="groove", bd=1
        )
        entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.term_entries.append(entry)

    def _clear_terms(self):
        for e in self.term_entries:
            e.delete(0, tk.END)

    def _set_searching_state(self, searching: bool):
        """UI'yi arama / bekleme moduna alır."""
        if searching:
            self.btn_search.config(text="⏹  Durdur", bg="#c0392b",
                                   command=self._request_cancel)
            self.btn_folder.config(state="disabled")
        else:
            self.btn_search.config(text="🔍  Ara", bg=ACCENT,
                                   command=self._on_search_button)
            self.btn_folder.config(state="normal")

    def _request_cancel(self):
        """Kullanıcı Durdur'a bastı — iptal bayrağını set et."""
        if self._search_thread and self._search_thread.is_alive():
            self._cancel_event.set()
            self.status_var.set("Durduruluyor…")

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="PDF Klasörü Seç")
        if folder:
            self.selected_folder = folder
            self.folder_var.set(folder)
            self.status_var.set("")
            self.listbox.delete(0, tk.END)
            self.result_files.clear()
            self.progress["value"] = 0

    def _get_terms(self) -> list[str]:
        terms = []
        for e in self.term_entries:
            val = e.get().strip()
            if val:
                terms.append(val.lower())
        return terms

    # ------------------------------------------------------------------
    # Arama
    # ------------------------------------------------------------------
    def _on_search_button(self):
        """Ara/Durdur butonuna basıldığında çağrılır."""
        if self._search_thread and self._search_thread.is_alive():
            self._request_cancel()
        else:
            self._start_search()

    def _start_search(self):
        if not FITZ_OK:
            messagebox.showerror(
                "Eksik Kütüphane",
                "PyMuPDF kurulu değil.\n\nTerminalde çalıştırın:\n  pip install pymupdf"
            )
            return

        if not self.selected_folder:
            messagebox.showwarning("Klasör Seçilmedi", "Lütfen önce bir klasör seçin.")
            return

        terms = self._get_terms()
        if not terms:
            messagebox.showwarning("Terim Girilmedi", "En az bir arama terimi girin.")
            return

        self.listbox.delete(0, tk.END)
        self.result_files.clear()
        self.status_var.set("Aranıyor…")
        self.progress["value"] = 0
        self._cancel_event.clear()
        self._set_searching_state(True)
        self.update_idletasks()

        self._search_thread = threading.Thread(
            target=self._search_worker,
            args=(self.selected_folder, terms),
            daemon=True
        )
        self._search_thread.start()

    def _search_worker(self, folder: str, terms: list[str]):
        try:
            pdf_files = sorted(
                f for f in os.listdir(folder)
                if f.lower().endswith(".pdf")
            )

            if not pdf_files:
                self.after(0, self._search_done, [], "Klasörde PDF dosyası bulunamadı.")
                return

            matches: list[str] = []
            errors = 0
            total = len(pdf_files)

            for i, filename in enumerate(pdf_files):
                if self._cancel_event.is_set():
                    self.after(0, self._search_done, matches, i, total,
                               f"Durduruldu. ({i}/{total} tarandı, "
                               f"{len(matches)} eşleşme bulundu)", True)
                    return

                self.after(0, self._update_progress, i, total, filename)
                filepath = os.path.join(folder, filename)
                try:
                    fitz.TOOLS.mupdf_warnings()
                    doc = fitz.open(filepath)
                    full_text = "".join(page.get_text() for page in doc).lower()
                    doc.close()
                    fitz.TOOLS.mupdf_warnings()

                    if all(term in full_text for term in terms):
                        matches.append(filepath)
                except Exception:
                    fitz.TOOLS.mupdf_warnings()
                    errors += 1

            if matches:
                msg = f"{len(matches)} / {total} PDF eşleşti. Çift tıkla aç."
            else:
                msg = f"Eşleşen PDF bulunamadı. ({total} dosya tarandı)"
            if errors:
                msg += f"  [{errors} dosya okunamadı]"

            self.after(0, self._search_done, matches, total, total, msg, False)

        except Exception as exc:
            self.after(0, self._search_done, [], 0, 0, f"Hata: {exc}", False)

    def _update_progress(self, current: int, total: int, filename: str):
        self.progress["maximum"] = total
        self.progress["value"] = current
        self.status_var.set(f"Taraniyor… {current + 1}/{total}: {filename}")

    def _search_done(self, matches: list[str], done: int, total: int,
                     msg: str, cancelled: bool):
        self.result_files = matches
        for filepath in matches:
            self.listbox.insert(tk.END, f"  {os.path.basename(filepath)}")
        self.progress["value"] = done
        self.status_var.set(msg)
        self._set_searching_state(False)

    # ------------------------------------------------------------------
    # Dosya Açma
    # ------------------------------------------------------------------
    def _open_file(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.result_files):
            filepath = self.result_files[idx]
            try:
                os.startfile(filepath)
            except Exception as exc:
                messagebox.showerror("Açılamadı", str(exc))


if __name__ == "__main__":
    app = PdfAraApp()
    app.mainloop()
