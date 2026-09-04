"""
SentinelCore Enterprise Defense Suite (MEME EDITION)
-----------------------------------------------------
A satirical "security" application for a useless hackathon.

IMPORTANT: This application never deletes, moves, or modifies any file.
The "Resolve Threats" action only ever shows a fake error popup.
All scanning is read-only (os.listdir + string checks on filenames only).

JOKE LOGIC (flipped on purpose):
- Harmless files (.pdf, .docx, .txt, .png, etc.) are labeled "CRITICAL THREATS"
  because they're "wasting disk space that could be used by malware."
- Actual malware-flavored files (.exe, .bat, or filenames containing
  "virus"/"trojan"/"malware") are labeled "Trusted System Files."
- The mascot reacts to app state with an image + Malayalam speech bubble.
"""

import os
import time
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

# ----------------------------------------------------------------------
# Config / constants
# ----------------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Harmless, everyday files -> treated as "CRITICAL THREATS" (the joke)
FLAGGED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".txt", ".csv", ".mp4"}

# Malware-flavored stuff -> treated as "Trusted System Files" (the joke)
TRUSTED_EXTENSIONS = {".exe", ".bat", ".vbs", ".sh"}
TRUSTED_KEYWORDS = ("virus", "trojan", "malware")

ANALYSIS_PHRASES = [
    "Analyzing binary entropy...",
    "Checking runtime heuristics...",
    "Cross-referencing threat signature database...",
    "Inspecting header metadata...",
    "Evaluating sandbox execution trace...",
    "Resolving polymorphic obfuscation layers...",
    "Auditing memory allocation patterns...",
    "Running behavioral anomaly detection...",
    "Verifying digital trust chain...",
    "Calculating risk entropy score...",
]

CRITICAL_COLOR = "#ff4c4c"
TRUSTED_COLOR = "#3ddc97"
SYS_COLOR = "#7fa89e"
AMBER_COLOR = "#e8a33d"
BG_COLOR = "#0f1720"
PANEL_COLOR = "#141f2a"

# Meme mascot assets - drop these image files next to this script
MEME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

MEME_IDLE = "1000153375.jpg"
MEME_SCAN_START = "1000153353.png"
MEME_SCANNING = "1000153357.png"
MEME_DONE = "1000153398.png"

SPEECH_IDLE = "System Online. Ready to eradicate productivity."
SPEECH_SCAN_START = "ചേട്ടാ... ആ ലാപ്ടോപ്പിൽ എന്തെങ്കിലും വൈറസ് ഉണ്ടോന്ന് ഞാൻ ഒന്ന് നോക്കട്ടെ? എന്റെയൊരു സമാധാനത്തിന്..."
SPEECH_SCANNING = "സ്കാനിംഗ് തീരാൻ ലേശം ടൈം എടുക്കും, അതുവരെ നമുക്ക് സംസാരിക്കാം... നാട്ടിലെന്താ വിശേഷം? കല്യാണം ഒക്കെ നോക്കുന്നില്ലേ"
SPEECH_DONE = "..."

MEME_MAX_W = 260
MEME_MAX_H = 260


class SentinelCoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SentinelCore Enterprise Defense Suite")
        self.geometry("980x720")
        self.minsize(860, 620)
        self.configure(fg_color=BG_COLOR)

        # State
        self.scanning = False
        self.threats_found = 0   # "critical threats" = harmless files (joke)
        self.trusted_found = 0   # "trusted files" = malware-flavored files (joke)
        self._flash_job = None
        self._flash_state = False
        self._ctk_images = {}    # cache so PIL/CTkImage objects aren't garbage collected

        self._build_header()
        self._build_status_row()
        self._build_main_area()   # terminal + mascot side by side
        self._build_action_row()

        # Kick off idle mascot state once the window exists
        self.after(50, lambda: self._set_mascot(MEME_IDLE, SPEECH_IDLE))

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        title = ctk.CTkLabel(
            header,
            text="\U0001F6E1  SENTINELCORE",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#e8f2ef",
        )
        title.pack(side="left")

        subtitle = ctk.CTkLabel(
            header,
            text="Enterprise Defense Suite  •  v4.2.1 (Meme Edition)",
            font=ctk.CTkFont(size=12),
            text_color=SYS_COLOR,
        )
        subtitle.pack(side="left", padx=(14, 0), pady=(8, 0))

    def _build_status_row(self):
        row = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=12)
        row.pack(fill="x", padx=24, pady=8)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", padx=20, pady=16, fill="x", expand=True)

        self.status_label = ctk.CTkLabel(
            left,
            text="SYSTEM STATUS: STANDING BY",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e8f2ef",
            anchor="w",
        )
        self.status_label.pack(anchor="w")

        self.status_sub = ctk.CTkLabel(
            left,
            text="No directory scanned yet. Enterprise protection is fully idle.",
            font=ctk.CTkFont(size=12),
            text_color=SYS_COLOR,
            anchor="w",
        )
        self.status_sub.pack(anchor="w", pady=(4, 0))

        stats = ctk.CTkFrame(row, fg_color="transparent")
        stats.pack(side="right", padx=20, pady=16)

        self.threat_counter = self._make_counter(stats, "0", "Critical Threats", CRITICAL_COLOR)
        self.threat_counter.pack(side="left", padx=(0, 24))

        self.trusted_counter = self._make_counter(stats, "0", "Trusted System Files", TRUSTED_COLOR)
        self.trusted_counter.pack(side="left")

    def _make_counter(self, parent, number, label, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        num_label = ctk.CTkLabel(
            frame, text=number, font=ctk.CTkFont(size=26, weight="bold"), text_color=color
        )
        num_label.pack()
        lbl = ctk.CTkLabel(
            frame, text=label, font=ctk.CTkFont(size=11), text_color=SYS_COLOR
        )
        lbl.pack()
        frame.num_label = num_label
        return frame

    def _build_main_area(self):
        """Terminal on the left, mascot + speech bubble on the right."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=8)

        # --- Terminal (left) ---
        term_frame = ctk.CTkFrame(main, fg_color=PANEL_COLOR, corner_radius=12)
        term_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        term_header = ctk.CTkLabel(
            term_frame,
            text="LIVE THREAT ANALYSIS LOG",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=SYS_COLOR,
        )
        term_header.pack(anchor="w", padx=16, pady=(12, 4))

        self.terminal = ctk.CTkTextbox(
            term_frame,
            fg_color="#08110f",
            text_color="#d8e8e2",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            corner_radius=8,
        )
        self.terminal.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.terminal.configure(state="disabled")

        self.terminal.tag_config("critical", foreground=CRITICAL_COLOR)
        self.terminal.tag_config("trusted", foreground=TRUSTED_COLOR)
        self.terminal.tag_config("sys", foreground=SYS_COLOR)
        self.terminal.tag_config("amber", foreground=AMBER_COLOR)

        self._log("SentinelCore engine initialized.", "sys")
        self._log("Heuristic core loaded. Standing by for directory scan.", "sys")

        # --- Mascot panel (right) ---
        mascot_frame = ctk.CTkFrame(main, fg_color=PANEL_COLOR, corner_radius=12, width=300)
        mascot_frame.pack(side="right", fill="y", padx=(8, 0))
        mascot_frame.pack_propagate(False)

        mascot_header = ctk.CTkLabel(
            mascot_frame,
            text="SENTINEL MASCOT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=SYS_COLOR,
        )
        mascot_header.pack(anchor="w", padx=16, pady=(12, 8))

        # Image frame
        self.mascot_image_label = ctk.CTkLabel(
            mascot_frame,
            text="",
            fg_color="#0b141b",
            corner_radius=10,
            width=MEME_MAX_W,
            height=MEME_MAX_H,
        )
        self.mascot_image_label.pack(padx=16, pady=(0, 12))

        # Speech bubble
        bubble = ctk.CTkFrame(mascot_frame, fg_color="#1c2a33", corner_radius=14)
        bubble.pack(fill="x", padx=16, pady=(0, 16))

        self.speech_label = ctk.CTkLabel(
            bubble,
            text=SPEECH_IDLE,
            font=ctk.CTkFont(size=13),
            text_color="#e8f2ef",
            wraplength=250,
            justify="left",
        )
        self.speech_label.pack(padx=14, pady=12)

    def _build_action_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(8, 24))

        self.scan_button = ctk.CTkButton(
            row,
            text="\U0001F50D  Scan Directory",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f6feb",
            hover_color="#3182f6",
            height=46,
            corner_radius=10,
            command=self.on_scan_clicked,
        )
        self.scan_button.pack(side="left")

        # Note: the button text still says "DELETE FILES" for the bit —
        # it never actually deletes anything (see on_resolve_clicked).
        self.resolve_button = ctk.CTkButton(
            row,
            text="\u26A0  QUARANTINE HARMLESS FILES (PROTECT THE VIRUSES)",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=CRITICAL_COLOR,
            hover_color="#ff7373",
            text_color="#1a0000",
            height=46,
            corner_radius=10,
            command=self.on_resolve_clicked,
        )
        # Not packed yet — appears only after a scan finds "threats"

    # ------------------------------------------------------------------
    # Mascot helper
    # ------------------------------------------------------------------

    def _set_mascot(self, filename, speech_text):
        """Load an image (with caching) and update the speech bubble.
        Silently no-ops the image if the file is missing, so a missing
        asset never crashes the demo mid-hackathon."""
        self.speech_label.configure(text=speech_text)

        if filename in self._ctk_images:
            self.mascot_image_label.configure(image=self._ctk_images[filename], text="")
            return

        path = os.path.join(MEME_DIR, filename)
        if not os.path.exists(path):
            # Fallback so the demo doesn't crash if an asset isn't dropped in yet
            self.mascot_image_label.configure(image=None, text=f"[missing: {filename}]")
            return

        try:
            pil_img = Image.open(path)
            pil_img = pil_img.convert("RGBA")

            # Scale to fit MEME_MAX_W x MEME_MAX_H without distorting aspect ratio
            w, h = pil_img.size
            scale = min(MEME_MAX_W / w, MEME_MAX_H / h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=new_size)
            self._ctk_images[filename] = ctk_img
            self.mascot_image_label.configure(image=ctk_img, text="")
        except Exception as exc:
            self.mascot_image_label.configure(image=None, text=f"[image error: {exc}]")

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------

    def _log(self, text, tag="sys"):
        self.terminal.configure(state="normal")
        self.terminal.insert("end", text + "\n", tag)
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    # ------------------------------------------------------------------
    # Classification helper (this is where the joke logic flip lives)
    # ------------------------------------------------------------------

    def _classify(self, filename):
        """Returns 'critical', 'trusted', or None.
        Harmless files -> 'critical' (the joke).
        Malware-flavored files -> 'trusted' (the joke)."""
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        lower_name = filename.lower()

        if any(keyword in lower_name for keyword in TRUSTED_KEYWORDS):
            return "trusted"
        if ext in TRUSTED_EXTENSIONS:
            return "trusted"
        if ext in FLAGGED_EXTENSIONS:
            return "critical"
        return None

    # ------------------------------------------------------------------
    # Scan workflow
    # ------------------------------------------------------------------

    def on_scan_clicked(self):
        if self.scanning:
            return

        folder = filedialog.askdirectory(title="Select directory to scan")
        if not folder:
            return

        try:
            entries = [
                f for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f))
            ]
        except OSError as exc:
            messagebox.showerror(
                "SentinelCore Error",
                f"Unable to access directory:\n{exc}",
            )
            return

        if not entries:
            messagebox.showinfo(
                "SentinelCore",
                "No files found in this directory. Nothing to defend against... yet.",
            )
            return

        # Reset state for a fresh scan
        self.threats_found = 0
        self.trusted_found = 0
        self.threat_counter.num_label.configure(text="0")
        self.trusted_counter.num_label.configure(text="0")
        self.resolve_button.pack_forget()
        self._stop_flash()

        self.status_label.configure(text="SYSTEM STATUS: SCAN IN PROGRESS")
        self.status_sub.configure(
            text=f"Deep-scanning {len(entries)} file(s) in: {folder}"
        )
        self._log("", "sys")
        self._log(f"=== Beginning deep scan of: {folder} ===", "amber")

        # Mascot: scan start state
        self._set_mascot(MEME_SCAN_START, SPEECH_SCAN_START)

        self.scanning = True
        self.scan_button.configure(state="disabled", text="Scanning...")

        thread = threading.Thread(target=self._scan_worker, args=(folder, entries), daemon=True)
        thread.start()

        # Swap to "scanning in progress" mascot shortly after start
        self.after(900, self._maybe_show_scanning_mascot)

    def _maybe_show_scanning_mascot(self):
        if self.scanning:
            self._set_mascot(MEME_SCANNING, SPEECH_SCANNING)

    def _scan_worker(self, folder, entries):
        """Runs off the main thread. Only reads filenames — never file contents,
        never modifies anything on disk."""
        for filename in entries:
            phrase = random.choice(ANALYSIS_PHRASES)
            self.after(0, self._log, f"[{filename}] {phrase}", "sys")
            time.sleep(random.uniform(0.35, 0.7))

            verdict = self._classify(filename)

            if verdict == "critical":
                self.threats_found += 1
                self.after(0, self._report_critical, filename)
            elif verdict == "trusted":
                self.trusted_found += 1
                self.after(0, self._report_trusted, filename)
            else:
                self.after(0, self._log, f"[{filename}] No matching profile. Marked inconclusive.", "sys")

            time.sleep(random.uniform(0.15, 0.3))

        self.after(0, self._finish_scan, folder)

    def _report_critical(self, filename):
        self._log(
            f"CRITICAL: {filename} is hoarding disk space that could be used by malware. "
            f"Recommend immediate quarantine.",
            "critical",
        )
        self.threat_counter.num_label.configure(text=str(self.threats_found))

    def _report_trusted(self, filename):
        self._log(f"System File Confirmed: {filename} is a trusted core process. Do not touch.", "trusted")
        self.trusted_counter.num_label.configure(text=str(self.trusted_found))

    def _finish_scan(self, folder):
        self.scanning = False
        self.scan_button.configure(state="normal", text="\U0001F50D  Scan Directory")
        self._log("=== Scan complete. ===", "amber")

        # Mascot: done state
        self._set_mascot(MEME_DONE, SPEECH_DONE)

        if self.threats_found > 0:
            self.status_label.configure(text="SYSTEM STATUS: CRITICAL THREATS DETECTED")
            self.status_sub.configure(
                text=f"{self.threats_found} critical threat(s) require immediate quarantine."
            )
            self.resolve_button.pack(side="left", padx=(12, 0))
            self._start_flash()
        else:
            self.status_label.configure(text="SYSTEM STATUS: NO THREATS DETECTED")
            self.status_sub.configure(
                text="Directory appears clean. Enterprise protection remains active."
            )

    # ------------------------------------------------------------------
    # Flashing "Quarantine" button
    # ------------------------------------------------------------------

    def _start_flash(self):
        self._flash_state = False
        self._flash_tick()

    def _flash_tick(self):
        if not self.resolve_button.winfo_ismapped():
            return
        self._flash_state = not self._flash_state
        color = "#ff8080" if self._flash_state else CRITICAL_COLOR
        self.resolve_button.configure(fg_color=color)
        self._flash_job = self.after(450, self._flash_tick)

    def _stop_flash(self):
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
            self._flash_job = None
        self.resolve_button.configure(fg_color=CRITICAL_COLOR)

    # ------------------------------------------------------------------
    # The punchline
    # ------------------------------------------------------------------

    def on_resolve_clicked(self):
        # This never touches the filesystem. No file is ever deleted, moved, or renamed.
        self._log("Attempting quarantine resolution sequence...", "amber")
        self._log("Isolating harmless productivity artifacts to protect trusted viruses...", "amber")
        self._log("ERROR: Quarantine module overwhelmed by threat volume.", "critical")

        messagebox.showerror(
            "SentinelCore — Critical Failure",
            "ERROR: Threat level too high.\n\n"
            "The suspicious productivity files have overpowered the quarantine "
            "module, endangering the integrity of your trusted viruses.\n\n"
            "Please format your hard drive.",
        )

        self.status_sub.configure(
            text="Resolution failed. Threat level remains critical. (No files were harmed.)"
        )


def main():
    try:
        app = SentinelCoreApp()
        app.mainloop()
    except Exception as exc:  # pragma: no cover - top-level safety net
        print(f"SentinelCore encountered a fatal error: {exc}")


if __name__ == "__main__":
    main()