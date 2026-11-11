"""X Media Downloader - multi-account desktop GUI.

Development:
    python -m pip install -r requirements.txt
    python twitter_photo_gui.py

The frozen application launches itself in --run-gdl mode to execute gallery-dl.
"""

from __future__ import annotations

import os
import re
import sys
import queue
import threading
import subprocess
import tkinter as tk
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote

APP_NAME = "X 미디어 다운로더"
APP_VERSION = "1.0.0"
TWITTER_START = "2006-03-21"
BROWSERS = ("chrome", "firefox", "safari", "edge", "brave", "chromium", "opera", "vivaldi")
MEDIA_MODES = ("사진만", "영상만", "사진 + 영상")
ACCOUNT_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,15}$")


def _dispatch_gallery_dl() -> None:
    """Run gallery-dl in this process; restore stdout/stderr for windowed bundles."""
    # PyInstaller --windowed applications can start with sys.stdout/sys.stderr=None.
    # When this executable is spawned with redirected pipes, recover those OS handles.
    if sys.stdout is None:
        sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

    from gallery_dl import main as gallery_dl_main

    sys.argv = ["gallery-dl", *sys.argv[2:]]
    raise SystemExit(gallery_dl_main() or 0)


if len(sys.argv) > 1 and sys.argv[1] == "--run-gdl":
    _dispatch_gallery_dl()


def clean_account(value: str) -> str:
    """Accept @handle, handle, or a normal X/Twitter profile URL."""
    value = value.strip()
    if not value:
        return ""
    if value.startswith(("https://", "http://")):
        match = re.fullmatch(r"https?://(?:www\.)?(?:x\.com|twitter\.com)/([A-Za-z0-9_]{1,15})/?", value)
        if not match:
            raise ValueError(f"X 프로필 주소를 확인해 주세요: {value}")
        value = match.group(1)
    value = value.lstrip("@").strip()
    if not ACCOUNT_PATTERN.fullmatch(value):
        raise ValueError(f"계정 ID 형식이 올바르지 않습니다: {value}")
    return value


def build_command(
    account: str,
    start_date: str,
    end_date_exclusive: str,
    browser: str,
    output_dir: str,
    media_mode: str,
) -> tuple[list[str], str]:
    """Build a gallery-dl command for X search.

    X's `until:` bound is exclusive, so the caller passes end-date + one day.
    gallery-dl's Twitter video setting lives under extractor.twitter.videos.
    """
    if media_mode == "사진만":
        filter_term = "images"
        videos_enabled = "false"
    elif media_mode == "영상만":
        filter_term = "videos"
        videos_enabled = "true"
    elif media_mode == "사진 + 영상":
        filter_term = "media"
        videos_enabled = "true"
    else:
        raise ValueError(f"지원하지 않는 미디어 옵션: {media_mode}")

    query = (
        f"from:{account} since:{start_date} "
        f"until:{end_date_exclusive} filter:{filter_term}"
    )
    url = "https://x.com/search?q=" + quote(query, safe="") + "&f=live"

    if getattr(sys, "frozen", False):
        executable = [sys.executable, "--run-gdl"]
    else:
        # Calling this file (instead of `python -m`) keeps the same CLI path
        # in development and in a PyInstaller-frozen application.
        executable = [sys.executable, str(Path(__file__).resolve()), "--run-gdl"]

    command = executable + [
        "--cookies-from-browser", browser,
        "--destination", output_dir,
        "--sleep-request", "2",
        "--download-archive", str(Path(output_dir) / ".x-media-download-archive.sqlite3"),
        "-o", f"extractor.twitter.videos={videos_enabled}",
        url,
    ]
    return command, query


class DownloaderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME}  {APP_VERSION}")
        self.geometry("850x720")
        self.minsize(700, 610)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.process: subprocess.Popen[str] | None = None
        self.stop_event = threading.Event()

        self._configure_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_events)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        themes = style.theme_names()
        # Keep native Aqua controls on macOS; use a consistent clean ttk theme elsewhere.
        if sys.platform == "darwin" and "aqua" in themes:
            style.theme_use("aqua")
        elif "clam" in themes:
            style.theme_use("clam")
            style.configure("TFrame", background="#F4F6FA")
            style.configure("TLabel", background="#F4F6FA", foreground="#202938")
            style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"), foreground="#182230")
            style.configure("Sub.TLabel", font=("TkDefaultFont", 10), foreground="#657286")
            style.configure("TLabelframe", background="#FFFFFF", bordercolor="#E0E5ED")
            style.configure("TLabelframe.Label", background="#FFFFFF", foreground="#344054", font=("TkDefaultFont", 10, "bold"))
            style.configure("TButton", padding=(11, 7), background="#FFFFFF")
            style.configure("Accent.TButton", padding=(15, 9), background="#2457D6", foreground="#FFFFFF", font=("TkDefaultFont", 10, "bold"))
            style.map("Accent.TButton", background=[("active", "#1948BB"), ("disabled", "#A8B6D8")], foreground=[("disabled", "#F5F6FA")])
            style.configure("TEntry", padding=7, fieldbackground="#FFFFFF")
            style.configure("TCombobox", padding=6, fieldbackground="#FFFFFF")
            style.configure("Horizontal.TProgressbar", troughcolor="#E6EAF1", background="#2457D6")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="X 미디어 다운로더", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="여러 계정의 사진과 영상을 기간별로 정리해서 저장합니다.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(5, 0))

        account_box = ttk.LabelFrame(root, text="  1  계정  ", padding=13)
        account_box.grid(row=1, column=0, sticky="ew", pady=(0, 11))
        account_box.columnconfigure(0, weight=1)
        ttk.Label(account_box, text="계정 ID 또는 X 프로필 주소를 입력하세요. 여러 계정은 줄바꿈으로 구분합니다.").grid(
            row=0, column=0, sticky="w", pady=(0, 7)
        )
        self.accounts_text = tk.Text(
            account_box, height=4, wrap="word", font=("TkDefaultFont", 10),
            relief="solid", bd=1, padx=8, pady=7, undo=True,
        )
        self.accounts_text.grid(row=1, column=0, sticky="ew")
        self.accounts_text.configure(highlightthickness=1, highlightbackground="#DCE2EA", highlightcolor="#2457D6")

        settings = ttk.LabelFrame(root, text="  2  다운로드 설정  ", padding=13)
        settings.grid(row=2, column=0, sticky="ew", pady=(0, 11))
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)

        ttk.Label(settings, text="다운로드 기간").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        date_frame = ttk.Frame(settings)
        date_frame.grid(row=0, column=1, columnspan=3, sticky="w", pady=6)
        self.start_var = tk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        self.end_var = tk.StringVar(value=date.today().isoformat())
        self.start_entry = ttk.Entry(date_frame, textvariable=self.start_var, width=13)
        self.start_entry.pack(side="left")
        ttk.Label(date_frame, text="  —  ").pack(side="left")
        self.end_entry = ttk.Entry(date_frame, textvariable=self.end_var, width=13)
        self.end_entry.pack(side="left")
        self.all_var = tk.BooleanVar(value=False)
        self.today_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings, text="전체 기간부터", variable=self.all_var, command=self._toggle_dates).grid(
            row=1, column=1, sticky="w", pady=4
        )
        ttk.Checkbutton(settings, text="오늘까지", variable=self.today_var, command=self._toggle_dates).grid(
            row=1, column=2, sticky="w", pady=4
        )

        ttk.Label(settings, text="미디어 종류").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        self.media_var = tk.StringVar(value="사진만")
        ttk.Combobox(settings, textvariable=self.media_var, values=MEDIA_MODES, state="readonly", width=17).grid(
            row=2, column=1, sticky="w", pady=6
        )
        ttk.Label(settings, text="로그인 브라우저").grid(row=2, column=2, sticky="e", padx=(10, 10), pady=6)
        self.browser_var = tk.StringVar(value="chrome")
        ttk.Combobox(settings, textvariable=self.browser_var, values=BROWSERS, state="readonly", width=14).grid(
            row=2, column=3, sticky="w", pady=6
        )

        ttk.Label(settings, text="저장 위치").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=6)
        self.output_var = tk.StringVar(value=str(Path.home() / "Downloads" / "X 미디어"))
        ttk.Entry(settings, textvariable=self.output_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=6)
        ttk.Button(settings, text="폴더 선택", command=self._choose_folder).grid(row=3, column=3, sticky="e", padx=(8, 0), pady=6)

        log_box = ttk.LabelFrame(root, text="  3  진행 로그  ", padding=10)
        log_box.grid(row=3, column=0, sticky="nsew", pady=(0, 11))
        log_box.columnconfigure(0, weight=1)
        log_box.rowconfigure(0, weight=1)
        self.log_text = tk.Text(
            log_box, height=12, wrap="word", state="disabled", font=("TkFixedFont", 9),
            relief="solid", bd=1, padx=8, pady=7,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(highlightthickness=1, highlightbackground="#DCE2EA")
        scrollbar = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        footer = ttk.Frame(root)
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=190)
        self.progress.grid(row=0, column=1, sticky="e", padx=(8, 0))

        buttons = ttk.Frame(root)
        buttons.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self.start_button = ttk.Button(buttons, text="다운로드 시작", style="Accent.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="중지", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Button(buttons, text="저장 폴더 열기", command=self.open_folder).pack(side="right")

        self._toggle_dates()

    def _toggle_dates(self) -> None:
        self.start_entry.configure(state="disabled" if self.all_var.get() else "normal")
        self.end_entry.configure(state="disabled" if self.today_var.get() else "normal")

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if selected:
            self.output_var.set(selected)

    def _log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message.rstrip("\n") + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _get_accounts(self) -> list[str]:
        raw_lines = self.accounts_text.get("1.0", "end").splitlines()
        accounts: list[str] = []
        seen: set[str] = set()
        for line in raw_lines:
            if not line.strip():
                continue
            account = clean_account(line)
            if account.casefold() not in seen:
                accounts.append(account)
                seen.add(account.casefold())
        return accounts

    def start(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return

        try:
            accounts = self._get_accounts()
        except ValueError as exc:
            messagebox.showwarning("계정 확인", str(exc))
            return
        if not accounts:
            messagebox.showwarning("계정 확인", "계정 ID를 한 개 이상 입력해 주세요.")
            return

        try:
            start_text = TWITTER_START if self.all_var.get() else self.start_var.get().strip()
            end_text = date.today().isoformat() if self.today_var.get() else self.end_var.get().strip()
            start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_text, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("날짜 확인", "날짜는 YYYY-MM-DD 형식으로 입력해 주세요.")
            return
        if end_date < start_date:
            messagebox.showwarning("날짜 확인", "종료일은 시작일보다 빠를 수 없습니다.")
            return

        output_dir = self.output_var.get().strip()
        if not output_dir:
            messagebox.showwarning("저장 위치", "저장 폴더를 선택해 주세요.")
            return

        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("저장 위치 오류", f"폴더를 만들 수 없습니다.\n{exc}")
            return

        # `until` is exclusive; increment by one day to include the selected end date.
        end_exclusive = (end_date + timedelta(days=1)).isoformat()
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress.start(12)
        self._log(f"작업 시작 · 계정 {len(accounts)}개 · {self.media_var.get()}")
        self._log(f"저장 위치 · {output_dir}")
        self.status_var.set(f"준비 중... (0/{len(accounts)} 계정)")

        self.worker_thread = threading.Thread(
            target=self._run_accounts,
            args=(accounts, start_text, end_exclusive, output_dir, self.browser_var.get(), self.media_var.get()),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_accounts(
        self,
        accounts: list[str],
        start_date: str,
        end_exclusive: str,
        output_dir: str,
        browser: str,
        media_mode: str,
    ) -> None:
        failed: list[str] = []
        processed = 0

        for index, account in enumerate(accounts, start=1):
            if self.stop_event.is_set():
                break
            self.events.put(("status", f"{account} 다운로드 중... ({index}/{len(accounts)})"))
            command, query = build_command(account, start_date, end_exclusive, browser, output_dir, media_mode)
            self.events.put(("log", f"\n[{index}/{len(accounts)}] @{account}"))
            self.events.put(("log", f"검색 조건 · {query}"))

            try:
                env = dict(os.environ)
                env["PYTHONUNBUFFERED"] = "1"
                env["PYTHONIOENCODING"] = "utf-8"
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=env,
                    creationflags=creationflags,
                )

                assert self.process.stdout is not None
                for line in self.process.stdout:
                    if self.stop_event.is_set():
                        if self.process.poll() is None:
                            self.process.terminate()
                        break
                    if line.strip():
                        self.events.put(("line", line.rstrip()))

                return_code = self.process.wait()
                self.process = None
                if return_code != 0 and not self.stop_event.is_set():
                    failed.append(account)
                    self.events.put(("log", f"오류 · @{account} (종료 코드 {return_code})"))
            except Exception as exc:
                self.process = None
                failed.append(account)
                self.events.put(("log", f"오류 · @{account}: {exc}"))

            processed += 1
            self.events.put(("status", f"계정 처리 중... ({processed}/{len(accounts)})"))

        self.events.put(("finished", {"stopped": self.stop_event.is_set(), "failed": failed, "total": len(accounts), "processed": processed}))

    def _poll_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind in ("log", "line"):
                    self._log(str(value))
                elif kind == "status":
                    self.status_var.set(str(value))
                elif kind == "finished":
                    self._finish(value)  # type: ignore[arg-type]
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _finish(self, result: dict[str, object]) -> None:
        self.progress.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.process = None
        if result["stopped"]:
            self.status_var.set(f"중지됨 ({result['processed']}/{result['total']} 계정 처리)")
            self._log("[중지됨] 현재 다운로드를 중단했습니다.")
        elif result["failed"]:
            failed = result["failed"]
            assert isinstance(failed, list)
            self.status_var.set(f"완료 · 실패 {len(failed)}/{result['total']}개 계정")
            self._log("실패한 계정 · " + ", ".join(failed))
        else:
            self.status_var.set(f"모든 계정 처리 완료 ({result['total']}개)")
            self._log("[모든 작업 완료]")
        self.worker_thread = None

    def stop(self) -> None:
        self.stop_event.set()
        process = self.process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        self.status_var.set("중지 요청 중...")

    def open_folder(self) -> None:
        path = self.output_var.get().strip()
        if not path:
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:
            messagebox.showerror("폴더 열기 실패", str(exc))

    def _on_close(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            if not messagebox.askyesno("종료 확인", "다운로드가 진행 중입니다. 중지하고 종료할까요?"):
                return
            self.stop()
        self.destroy()


if __name__ == "__main__":
    DownloaderApp().mainloop()
