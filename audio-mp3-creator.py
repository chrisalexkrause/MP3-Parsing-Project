import sys
from pathlib import Path
from typing import List, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import time

import PyPDF2
from gtts import gTTS
import tempfile
import subprocess


def clean_filename(text: str, max_len: int = 55) -> str:
    text = re.sub(r'^\d+\.\s*', '', text).strip()
    text = re.sub(r'[\\/:*?"<>|]', '', text)
    if len(text) > max_len:
        text = text[:max_len].rstrip()
    return text


def clean_japanese(text: str) -> str:
    text = re.sub(r'^\d+\.\s*', '', text).strip()
    text = re.sub(r'\s*\d+\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_english(text: str) -> str:
    text = re.sub(r'^\d+\.\s*', '', text).strip()
    text = re.sub(r'([a-zA-Z])[\d²¹³⁴⁵⁶⁷⁸⁹]+', r'\1', text)
    text = text.replace("s'ince", "since").replace("s ince", "since")
    text = text.replace("I²", "I").replace("me²", "me").replace("you²", "you")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class PdfAudiobookGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Japanese Textbook Audiobook Creator")
        self.root.geometry("860x720")
        self.pdf_path = None
        self.output_dir = "audiobook"
        self.cooldown_var = tk.IntVar(value=12)
        self.start_var = tk.IntVar(value=1)
        self.end_var = tk.IntVar(value=0)
        self.create_widgets()
        self.root.mainloop()

    def create_widgets(self):
        ttk.Label(self.root, text="Japanese Textbook → Audiobook Creator", 
                  font=("Helvetica", 16, "bold")).pack(pady=10)

        f1 = ttk.LabelFrame(self.root, text="1. Select PDF File", padding=10)
        f1.pack(fill="x", padx=20, pady=8)
        self.pdf_label = ttk.Label(f1, text="No file selected")
        self.pdf_label.pack(side="left", padx=5)
        ttk.Button(f1, text="Browse PDF", command=self.browse_pdf).pack(side="right", padx=5)

        f2 = ttk.LabelFrame(self.root, text="2. Output Folder", padding=10)
        f2.pack(fill="x", padx=20, pady=8)
        self.out_label = ttk.Label(f2, text=self.output_dir)
        self.out_label.pack(side="left", padx=5)
        ttk.Button(f2, text="Browse", command=self.browse_output).pack(side="right", padx=5)

        f3 = ttk.LabelFrame(self.root, text="3. Range & Cooldown", padding=12)
        f3.pack(fill="x", padx=20, pady=8)

        ttk.Label(f3, text="Start Sentence:").grid(row=0, column=0, sticky="w", pady=6, padx=5)
        ttk.Spinbox(f3, from_=1, to=4000, textvariable=self.start_var, width=10).grid(row=0, column=1, pady=6, padx=5)

        ttk.Label(f3, text="End Sentence (0 = all):").grid(row=1, column=0, sticky="w", pady=6, padx=5)
        ttk.Spinbox(f3, from_=0, to=4000, textvariable=self.end_var, width=10).grid(row=1, column=1, pady=6, padx=5)

        ttk.Label(f3, text="Cooldown:").grid(row=2, column=0, sticky="w", pady=6, padx=5)
        ttk.Spinbox(f3, from_=5, to=20, textvariable=self.cooldown_var, width=10).grid(row=2, column=1, pady=6, padx=5)
        ttk.Label(f3, text="seconds (12–15 recommended)").grid(row=2, column=2, sticky="w", padx=5)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="🚀 Start / Resume Range", command=self.start_processing).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🎵 Start Range + Combine", command=lambda: self.start_processing(combine=True)).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).pack(side="right", padx=10)

        log_frame = ttk.LabelFrame(self.root, text="Progress Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = tk.Text(log_frame, height=24, state="disabled", wrap="word", font=("Consolas", 9))
        sc = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sc.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def browse_pdf(self):
        file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file:
            self.pdf_path = file
            self.pdf_label.config(text=Path(file).name)

    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir = folder
            self.out_label.config(text=Path(folder).name)

    def start_processing(self, combine: bool = False):
        if not self.pdf_path:
            messagebox.showerror("Error", "Please select a PDF file.")
            return
        threading.Thread(target=self.process_audiobook, args=(combine,), daemon=True).start()

    def process_audiobook(self, combine: bool = False):
        cooldown = self.cooldown_var.get()
        start_num = self.start_var.get()
        end_num = self.end_var.get()

        try:
            self.log(f"🚀 Starting range {start_num} → {end_num if end_num > 0 else 'End'} | Cooldown: {cooldown}s")
            pdf_file = Path(self.pdf_path)
            base_dir = Path(self.output_dir) / pdf_file.stem
            base_dir.mkdir(parents=True, exist_ok=True)

            self.log("📄 Extracting text...")
            full_text = self.extract_text_from_pdf(str(pdf_file))

            self.log("🔍 Extracting sentences...")
            all_pairs = self.extract_sentences(full_text)
            total = len(all_pairs)

            start_idx = max(0, start_num - 1)
            end_idx = end_num if end_num > 0 else total
            pairs = all_pairs[start_idx:end_idx]

            self.log(f"✅ Processing {len(pairs)} sentences (total ~{total})...\n")

            mp3_files = []
            start_time = time.time()

            for i, (jp, en) in enumerate(pairs, start_idx + 1):
                jp_clean = clean_filename(jp)
                en_clean = clean_filename(en)

                jp1 = base_dir / f"{i:03d}_A_{jp_clean}_Japanese.mp3"
                en1 = base_dir / f"{i:03d}_B_{en_clean}_English.mp3"
                jp2 = base_dir / f"{i:03d}_C_{jp_clean}_Japanese_Repeat.mp3"

                if jp1.exists() and en1.exists() and jp2.exists():
                    self.log(f"{i:03d}. Skipped (already exists)")
                else:
                    self.log(f"{i:03d}. Generating...")
                    self.save_as_mp3(jp, jp1, 'ja')
                    self.save_as_mp3(en, en1, 'en')
                    self.save_as_mp3(jp, jp2, 'ja')

                mp3_files.extend([jp1, en1, jp2])

                self.log(f"   ⏳ Cooldown {cooldown} seconds...")
                time.sleep(cooldown)

                elapsed = time.time() - start_time
                avg = elapsed / (i - start_idx)
                remaining = len(pairs) - (i - start_idx)
                est = remaining * avg
                self.log(f"   ⏱️ Remaining ≈ {int(est//60)} min {int(est%60)} sec")

            if combine:
                self.log("\n🔗 Creating full audiobook...")
                final = base_dir / f"{pdf_file.stem}_FULL_Audiobook_JP_EN_JP.mp3"
                self.combine_mp3s(mp3_files, final)

            self.log("\n🎉 Done!")
            messagebox.showinfo("Success", "Range completed!")

        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                if page_text := page.extract_text():
                    text += page_text + "\n"
        return text

    def extract_sentences(self, text: str) -> List[Tuple[str, str]]:
        """Maximum strict Japanese extraction"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        pairs = []
        i = 0
        while i < len(lines):
            line = lines[i]

            if re.match(r'^\d+\.', line) and any(ord(c) > 127 for c in line):
                jp_parts = [line]
                i += 1

                # Stop Japanese at the FIRST sign of Latin text
                while i < len(lines) and not re.match(r'^\d+\.', lines[i]):
                    next_line = lines[i]
                    if re.match(r'^[A-Za-z]', next_line):   # Romaji or English
                        break
                    if re.search(r'#\d+', next_line):
                        i += 1
                        continue
                    jp_parts.append(next_line)
                    i += 1

                jp = " ".join(jp_parts).strip()

                # English
                eng_parts = []
                while i < len(lines) and not re.match(r'^\d+\.', lines[i]):
                    next_line = lines[i]
                    if re.search(r'#\d+', next_line) or len(next_line) < 15:
                        i += 1
                        continue

                    lower = next_line.lower()
                    if (' ' in next_line and (
                        any(word in lower for word in ['as for', 'the ', 'please', 'show', 'what', 'how', 'yes', 'no', 
                                                       'is ', 'it ', 'for ', 'but ', 'now ', 'big', 'small', 'this', 
                                                       'that', 'here', 'there', 'she ', 'he ', 'i ']) 
                        or len(next_line) > 45)):
                        eng_parts.append(next_line)
                    i += 1

                eng = " ".join(eng_parts).strip()

                if jp and eng and len(eng) > 20:
                    pairs.append((jp, eng))
            else:
                i += 1
        return pairs

    def save_as_mp3(self, text: str, filename: Path, lang: str = 'ja'):
        if not text.strip():
            return
        try:
            clean_text = clean_japanese(text) if lang == 'ja' else clean_english(text)
            if "kudasai" in clean_text.lower() or "ください" in clean_text:
                clean_text += "。"

            tts = gTTS(text=clean_text, lang=lang, slow=False)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tts.save(tmp.name)
                tmp_path = Path(tmp.name)

            try:
                subprocess.run(['ffmpeg', '-y', '-i', str(tmp_path), '-b:a', '128k', str(filename)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except Exception:
                tmp_path.rename(filename)

            tmp_path.unlink(missing_ok=True)
            self.log(f"   💾 Saved: {filename.name}")
        except Exception as e:
            self.log(f"   ⚠️ Failed {filename.name}: {e}")

    def combine_mp3s(self, mp3_list: List[Path], output_file: Path):
        try:
            list_file = output_file.with_suffix('.txt')
            with open(list_file, 'w', encoding='utf-8') as f:
                for p in mp3_list:
                    f.write(f"file '{p}'\n")
            subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(list_file), 
                          '-c', 'copy', str(output_file)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            list_file.unlink(missing_ok=True)
            self.log("   ✅ Full audiobook created")
        except Exception as e:
            self.log(f"   ⚠️ Combine failed: {e}")


if __name__ == "__main__":
    try:
        import PyPDF2
        from gtts import gTTS
        PdfAudiobookGUI()
    except ImportError:
        print("Missing packages. Run:")
        print("   python -m pip install PyPDF2 gtts pygame pycryptodome")
        input("Press Enter to exit...")
        sys.exit(1)