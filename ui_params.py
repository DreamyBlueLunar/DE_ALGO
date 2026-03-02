import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from core.params import GlobalState
from core.data_utils import copy_input_file


class DEParameterDialog(tk.Toplevel):
    def __init__(self, master=None, state: GlobalState = None):
        super().__init__(master)
        self.state = state
        self._selected_path: str | None = None
        self.title("参数设置")
        self.geometry("700x480")
        self.transient(master)
        self.grab_set()
        self.bind("<Return>", lambda e: "break")
        self.bind("<KP_Enter>", lambda e: "break")
        self._build()

    def _build(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        ttk.Label(frm, text="混合传感器网络").grid(row=0, column=0, sticky="w")
        self.combo_network = ttk.Combobox(frm, values=["从文件读出", "随机产生"], state="readonly")
        self.combo_network.grid(row=0, column=1, sticky="w")
        self.combo_network.bind("<<ComboboxSelected>>", self._on_network_change)
        self.btn_select = ttk.Button(frm, text="选择传感器网络", command=self._select_file)
        self.btn_select.grid(row=1, column=0, sticky="w")
        self.entry_file = ttk.Entry(frm, width=50, state="readonly")
        self.entry_file.grid(row=1, column=1, sticky="w")
        ttk.Label(frm, text="移动节点比例").grid(row=2, column=0, sticky="w")
        self.combo_mobile_percent = ttk.Combobox(frm, values=[
            "0.04","0.05","0.06","0.07","0.08","0.09","0.1","0.11","0.12","0.13","0.14","0.15","0.2"
        ], state="readonly")
        self.combo_mobile_percent.grid(row=2, column=1, sticky="w")
        ttk.Label(frm, text="移动节点分布").grid(row=3, column=0, sticky="w")
        self.mobile_var = tk.IntVar(value=0)
        ttk.Radiobutton(frm, text="位置固定", variable=self.mobile_var, value=0).grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(frm, text="随机分布", variable=self.mobile_var, value=1).grid(row=3, column=2, sticky="w")
        group = ttk.LabelFrame(frm, text="差分演化算法参数")
        group.grid(row=4, column=0, columnspan=3, pady=12, sticky="we")
        ttk.Label(group, text="种群规模").grid(row=0, column=0, sticky="w")
        self.combo_pop = ttk.Combobox(group, values=["20","30","40","50"], state="readonly")
        self.combo_pop.grid(row=0, column=1, sticky="w")
        ttk.Label(group, text="交叉概率").grid(row=1, column=0, sticky="w")
        self.combo_cross = ttk.Combobox(group, values=["0.1","0.15","0.20","0.25","0.45","0.75","0.85","0.95"], state="readonly")
        self.combo_cross.grid(row=1, column=1, sticky="w")
        ttk.Label(group, text="缩放因子").grid(row=2, column=0, sticky="w")
        self.combo_factor = ttk.Combobox(group, values=["0.4","0.5","0.6","0.7","0.8","0.9","1.0"], state="readonly")
        self.combo_factor.grid(row=2, column=1, sticky="w")
        ttk.Label(group, text="最大迭代数").grid(row=3, column=0, sticky="w")
        self.combo_gen = ttk.Combobox(group, values=["100","300","500","1000","2000","3000","10000","100000"], state="readonly")
        self.combo_gen.grid(row=3, column=1, sticky="w")
        btn_ok = ttk.Button(frm, text="确定", command=self._ok)
        btn_ok.grid(row=5, column=1, pady=12, sticky="e")
        btn_cancel = ttk.Button(frm, text="取消", command=self.destroy)
        btn_cancel.grid(row=5, column=2, pady=12, sticky="w")
        self._prefill()

    def _prefill(self):
        self.combo_network.set("随机产生" if self.state.network_random_generated else "从文件读出")
        self.entry_file.delete(0, tk.END)
        try:
            name = Path(self.state.networkfilename).name if self.state.networkfilename else ""
            self.entry_file.insert(0, name)
        except Exception:
            self.entry_file.insert(0, self.state.networkfilename)
        self.combo_mobile_percent.set(f"{self.state.mobile_percent:.2f}")
        self.mobile_var.set(1 if self.state.random_placed else 0)
        self.combo_pop.set(str(self.state.de_population_size))
        self.combo_cross.set(f"{self.state.de_cross_prob:.2f}")
        self.combo_factor.set(f"{self.state.de_factor:.1f}")
        self.combo_gen.set(str(self.state.de_max_generations))
        self._toggle_file_controls()

    def _toggle_file_controls(self):
        is_file = self.combo_network.get() == "从文件读出"
        self.btn_select.configure(state="normal" if is_file else "disabled")
        self.entry_file.configure(state="normal" if is_file else "disabled")

    def _on_network_change(self, _evt):
        self._toggle_file_controls()

    def _select_file(self):
        base_dir = Path(__file__).resolve().parent
        default_dir = base_dir / "data"
        init_dir = default_dir
        try:
            cur = Path(self.entry_file.get() or self.state.networkfilename)
            if cur.exists():
                init_dir = cur.parent
        except Exception:
            pass
        path = filedialog.askopenfilename(parent=self, initialdir=str(init_dir), filetypes=[("WSN 文本文件", "*.txt"), ("所有文件", "*.*")])
        if path:
            self._selected_path = path
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, Path(path).name)
            self.entry_file.focus_set()

    def _ok(self):
        self.state.network_random_generated = self.combo_network.get() == "随机产生"
        self.state.random_placed = self.mobile_var.get() == 1
        try:
            self.state.mobile_percent = float(self.combo_mobile_percent.get())
        except Exception:
            pass
        if not self.state.network_random_generated:
            src = self._selected_path or self.state.networkfilename
            try:
                dest = copy_input_file(src)
                self.state.networkfilename = str(dest)
            except Exception:
                self.state.networkfilename = src
        try:
            self.state.de_population_size = int(self.combo_pop.get())
        except Exception:
            pass
        try:
            self.state.de_cross_prob = float(self.combo_cross.get())
        except Exception:
            pass
        try:
            self.state.de_factor = float(self.combo_factor.get())
        except Exception:
            pass
        try:
            self.state.de_max_generations = int(self.combo_gen.get())
        except Exception:
            pass
        self.destroy()
