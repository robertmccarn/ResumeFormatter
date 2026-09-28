from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .compiler import CompilationResult, compile_resume


class ResumeFormatterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ResumeFormatter")
        self.root.geometry("1080x760")
        self.root.minsize(900, 650)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value="formatted_resume.docx")
        self.status_text = tk.StringVar(value="Ready.")
        self.busy = False

        self._build_ui()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=(12, 10))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(3, weight=1)

        ttk.Button(toolbar, text="Open TXT", command=self.open_text).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(toolbar, text="Save TXT", command=self.save_text).grid(
            row=0, column=1, padx=6
        )
        ttk.Button(toolbar, text="Compile DOCX", command=self.compile).grid(
            row=0, column=2, padx=(6, 0)
        )

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        editor_frame = ttk.Labelframe(main, text="Resume Text", padding=8)
        audit_frame = ttk.Labelframe(main, text="Compilation Audit", padding=10)
        main.add(editor_frame, weight=3)
        main.add(audit_frame, weight=2)

        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(1, weight=1)

        source_row = ttk.Frame(editor_frame)
        source_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        source_row.columnconfigure(1, weight=1)

        ttk.Label(source_row, text="Source:").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(source_row, textvariable=self.input_path).grid(
            row=0, column=1, sticky="ew"
        )

        self.editor = ScrolledText(
            editor_frame,
            wrap="word",
            undo=True,
            font=("Consolas", 10),
        )
        self.editor.grid(row=1, column=0, sticky="nsew")

        audit_frame.columnconfigure(0, weight=1)
        audit_frame.rowconfigure(2, weight=1)

        output_row = ttk.Frame(audit_frame)
        output_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        output_row.columnconfigure(1, weight=1)

        ttk.Label(output_row, text="Output:").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(output_row, textvariable=self.output_path).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(output_row, text="Browse", command=self.choose_output).grid(
            row=0, column=2, padx=(6, 0)
        )

        ttk.Label(
            audit_frame,
            textvariable=self.status_text,
            font=("Segoe UI", 11, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.audit_text = ScrolledText(
            audit_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.audit_text.grid(row=2, column=0, sticky="nsew")

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))

        ttk.Label(
            self.root,
            text="The compiler preserves supplied content unless conservative overflow trimming is required.",
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

    def open_text(self) -> None:
        path = filedialog.askopenfilename(
            title="Open Resume Text",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Open failed", str(exc))
            return

        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        self.input_path.set(path)
        self.status_text.set("Loaded resume text.")
        self._set_audit("")

    def save_text(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Resume Text",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            Path(path).write_text(
                self.editor.get("1.0", tk.END).rstrip() + "\n",
                encoding="utf-8",
            )
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self.input_path.set(path)
        self.status_text.set("Saved resume text.")

    def choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose DOCX Output",
            defaultextension=".docx",
            initialfile=Path(self.output_path.get()).name or "formatted_resume.docx",
            filetypes=[("Word documents", "*.docx")],
        )
        if path:
            self.output_path.set(path)

    def compile(self) -> None:
        if self.busy:
            return

        source = self.editor.get("1.0", tk.END).strip()
        if not source:
            messagebox.showwarning(
                "Nothing to compile",
                "Enter or open resume text first.",
            )
            return

        output_text = self.output_path.get().strip()
        if not output_text:
            messagebox.showwarning(
                "Output required",
                "Choose an output DOCX path.",
            )
            return

        output = Path(output_text)
        if output.suffix.lower() != ".docx":
            output = output.with_suffix(".docx")
            self.output_path.set(str(output))

        self.busy = True
        self.status_text.set("Compiling...")
        self.progress.start(12)
        self._set_buttons_enabled(False)

        thread = threading.Thread(
            target=self._compile_worker,
            args=(source, output),
            daemon=True,
        )
        thread.start()

    def _compile_worker(self, source: str, output: Path) -> None:
        try:
            result = compile_resume(source, output)
        except Exception as exc:
            self.root.after(0, self._compile_failed, exc)
            return

        self.root.after(0, self._compile_finished, result)

    def _compile_finished(self, result: CompilationResult) -> None:
        self.busy = False
        self.progress.stop()
        self._set_buttons_enabled(True)

        validation = result.audit.actual_validation
        lines = [
            f"Status: {'SUCCESS' if result.success else 'INCOMPLETE'}",
            f"Profile: {result.audit.profile.name}",
            f"Estimated pages: {result.audit.estimated_pages}",
            (
                f"Actual pages: {validation.page_count}"
                if validation.page_count is not None
                else "Actual pages: unavailable"
            ),
            (
                f"Experience starts: page {validation.experience_page}"
                if validation.experience_page is not None
                else "Experience starts: unverified"
            ),
            f"Trimmed: {'yes' if result.audit.trimmed else 'no'}",
        ]

        if result.audit.structural_errors:
            lines.extend(
                ["", "Structural issues:"]
                + [f"  - {issue}" for issue in result.audit.structural_errors]
            )

        if validation.issues:
            lines.extend(
                ["", "Validation issues:"]
                + [f"  - {issue}" for issue in validation.issues]
            )

        report = result.audit.trim_report
        if report and report.changed:
            lines.extend(
                [
                    "",
                    (
                        f"Trim changes: {report.changes_count} "
                        f"(~{report.lines_recovered} lines recovered)"
                    ),
                ]
            )
            lines.extend(
                f"  - {change.location}: {change.original_text}"
                for change in report.changes
            )

        self._set_audit("\n".join(lines))

        if result.success:
            self.status_text.set("Compilation successful.")
            messagebox.showinfo(
                "ResumeFormatter",
                f"Resume compiled successfully.\n\n{result.output_path}",
            )
        else:
            self.status_text.set("Compilation incomplete.")
            messagebox.showwarning(
                "ResumeFormatter",
                "The compiler produced an output, but validation did not satisfy all rules. See the audit panel.",
            )

    def _compile_failed(self, exc: Exception) -> None:
        self.busy = False
        self.progress.stop()
        self._set_buttons_enabled(True)
        self.status_text.set("Compilation failed.")
        self._set_audit(f"Error: {exc}")
        messagebox.showerror("Compilation failed", str(exc))

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for widget in self.root.winfo_children():
            self._set_button_tree_state(widget, "normal" if enabled else "disabled")

    def _set_button_tree_state(self, widget: tk.Misc, state: str) -> None:
        if isinstance(widget, ttk.Button):
            widget.configure(state=state)
        for child in widget.winfo_children():
            self._set_button_tree_state(child, state)

    def _set_audit(self, text: str) -> None:
        self.audit_text.configure(state="normal")
        self.audit_text.delete("1.0", tk.END)
        self.audit_text.insert("1.0", text)
        self.audit_text.configure(state="disabled")


def run_gui() -> None:
    root = tk.Tk()
    ResumeFormatterApp(root)
    root.mainloop()
