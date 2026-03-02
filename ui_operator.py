import tkinter as tk
from tkinter import ttk
from core.params import GlobalState


class OperatorSetDialog(tk.Toplevel):
    def __init__(self, master=None, state: GlobalState = None):
        super().__init__(master)
        self.state = state
        self.title("变异算子")
        self.geometry("420x360")
        self._build()

    def _build(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        ttk.Label(frm, text="差分变异算子").pack(anchor="w")
        self.var = tk.IntVar(value=self.state.operator_kind)
        items = [
            ("DE/Best/1", 0),
            ("DE/Best/2", 1),
            ("DE/Rand/1", 2),
            ("DE/Rand/2", 3),
            ("DE/Current-to-best/1", 4),
            ("DE/Rand-to-best/1", 5),
        ]
        for text, val in items:
            ttk.Radiobutton(frm, text=text, variable=self.var, value=val).pack(anchor="w")
        btn_ok = ttk.Button(frm, text="确定", command=self._ok)
        btn_ok.pack(side=tk.LEFT, padx=8, pady=12)
        btn_cancel = ttk.Button(frm, text="取消", command=self.destroy)
        btn_cancel.pack(side=tk.LEFT, padx=8, pady=12)

    def _ok(self):
        self.state.operator_kind = self.var.get()
        self.destroy()
