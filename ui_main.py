import tkinter as tk
from tkinter import ttk
from core.params import GlobalState
from ui_params import DEParameterDialog
from ui_operator import OperatorSetDialog
from ui_result import ResultForm
from ui_coords import CoordsForm
import os
from pathlib import Path


class MainForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WSN 覆盖优化（Python）")
        self.geometry("600x352")
        self.state = GlobalState()
        self._build_menu()
        self._build_actions()

    def _build_menu(self):
        m = tk.Menu(self)
        alg_menu = tk.Menu(m, tearoff=0)
        alg_menu.add_command(label="基本DE", command=lambda: self._set_alg(1))
        alg_menu.add_command(label="JDE", command=lambda: self._set_alg(2))
        m.add_cascade(label="算法", menu=alg_menu)
        view_menu = tk.Menu(m, tearoff=0)
        view_menu.add_command(label="优化后的布局", command=lambda: self._open_coords("optimized"))
        view_menu.add_command(label="初始布局", command=lambda: self._open_coords("initial"))
        view_menu.add_separator()
        view_menu.add_command(label="优化后坐标文件", command=self._open_output_txt)
        view_menu.add_command(label="初始坐标文件", command=self._open_initial_txt)
        m.add_cascade(label="查看", menu=view_menu)
        self.config(menu=m)

    def _build_actions(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        btn_params = ttk.Button(frm, text="参数设置", command=self._open_params)
        btn_params.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        btn_ops = ttk.Button(frm, text="算子设置", command=self._open_ops)
        btn_ops.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        btn_run = ttk.Button(frm, text="开始优化", command=self._open_result)
        btn_run.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.label_alg = ttk.Label(frm, text="算法：基本DE")
        self.label_alg.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    def _set_alg(self, kind: int):
        self.state.alg_kind = kind
        self.label_alg.configure(text="算法：JDE" if kind == 2 else "算法：基本DE")

    def _open_params(self):
        DEParameterDialog(self, self.state)

    def _open_ops(self):
        OperatorSetDialog(self, self.state)

    def _open_result(self):
        ResultForm(self, self.state)

    def _open_coords(self, mode: str):
        CoordsForm(self, self.state, mode)

    def _open_output_txt(self):
        base_dir = Path(__file__).resolve().parent
        p = base_dir / "result" / "output.txt"
        if p.exists():
            try:
                os.startfile(str(p))
            except Exception:
                pass

    def _open_initial_txt(self):
        p = Path(self.state.networkfilename)
        if p.exists():
            try:
                os.startfile(str(p))
            except Exception:
                pass
