import tkinter as tk
from tkinter import ttk
from core.de_algo import DEAlgorithm
from core.params import GlobalState, Sensor


class ResultForm(tk.Toplevel):
    def __init__(self, master=None, state: GlobalState = None):
        super().__init__(master)
        self.state = state or GlobalState()
        self.title("结果输出")
        self.geometry("1350x700")
        self._build_ui()
        self._run_and_render()

    def _build_ui(self):
        self.canvas = tk.Canvas(self, width=1308, height=516, bg="white")
        self.canvas.pack(padx=8, pady=8)
        panel = ttk.Frame(self)
        panel.pack(fill=tk.X, padx=12, pady=6)
        self.edit_gen = ttk.Entry(panel, width=10, state="readonly")
        ttk.Label(panel, text="收敛代").grid(row=0, column=0, sticky="w")
        self.edit_gen.grid(row=0, column=1, sticky="w")
        ttk.Label(panel, text="最优值").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.edit_maxvalue = ttk.Entry(panel, width=12, state="readonly")
        self.edit_maxvalue.grid(row=0, column=3, sticky="w")
        ttk.Label(panel, text="收敛时间(秒)").grid(row=0, column=4, sticky="w", padx=(12, 0))
        self.edit_time = ttk.Entry(panel, width=10, state="readonly")
        self.edit_time.grid(row=0, column=5, sticky="w")
        ttk.Label(panel, text="程序运行时间(秒)").grid(row=0, column=6, sticky="w", padx=(12, 0))
        self.edit_runtime = ttk.Entry(panel, width=10, state="readonly")
        self.edit_runtime.grid(row=0, column=7, sticky="w")
        ttk.Label(panel, text="初始覆盖率(%)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.edit_initialcoverage = ttk.Entry(panel, width=10, state="readonly")
        self.edit_initialcoverage.grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="优化后覆盖率(%)").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(8, 0))
        self.edit_finalcoverage = ttk.Entry(panel, width=10, state="readonly")
        self.edit_finalcoverage.grid(row=1, column=3, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="中间平均移动距离").grid(row=1, column=4, sticky="w", padx=(12, 0), pady=(8, 0))
        self.edit_movedist = ttk.Entry(panel, width=10, state="readonly")
        self.edit_movedist.grid(row=1, column=5, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="DE平均移动距离").grid(row=1, column=6, sticky="w", padx=(12, 0), pady=(8, 0))
        self.edit_de_dist = ttk.Entry(panel, width=10, state="readonly")
        self.edit_de_dist.grid(row=1, column=7, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="优化平均移动距离").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.edit_optimaldist = ttk.Entry(panel, width=10, state="readonly")
        self.edit_optimaldist.grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="需移动节点数").grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(8, 0))
        self.edit_movednum = ttk.Entry(panel, width=10, state="readonly")
        self.edit_movednum.grid(row=2, column=3, sticky="w", pady=(8, 0))
        ttk.Label(panel, text="C/d").grid(row=2, column=4, sticky="w", padx=(12, 0), pady=(8, 0))
        self.edit_cov_dist = ttk.Entry(panel, width=10, state="readonly")
        self.edit_cov_dist.grid(row=2, column=5, sticky="w", pady=(8, 0))
        self._setup_setters()

    def _setup_setters(self):
        def set_entry(entry, text):
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, text)
            entry.configure(state="readonly")
        self._set_entry = set_entry

    def _run_and_render(self):
        algo = DEAlgorithm(self.state)
        if self.state.alg_kind == 2:
            algo.run_jde()
            self.title("基于JDE差分演化算法的混合WSN覆盖控制优化")
        else:
            algo.run_simple_de()
            self.title("基于基本差分演化算法的混合WSN覆盖控制优化")
        self._fill_metrics(algo)
        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width()
        col_width = 280
        col_gap = 60
        total = 4 * col_width + 3 * col_gap
        pad = max(10, (cw - total) // 2)
        base_offset = pad - 195
        offsets = [
            base_offset + 0 * (col_width + col_gap),
            base_offset + 1 * (col_width + col_gap),
            base_offset + 2 * (col_width + col_gap),
            base_offset + 3 * (col_width + col_gap),
        ]
        self._draw_column_initial(offsets[0])
        self._draw_column_positions(self.state.DEbestmobileposition, offsets[1])
        self._draw_column_positions(self.state.bestmobileposition, offsets[2])
        self._draw_column_positions(self.state.optimalmatch, offsets[3])
        for ox in offsets:
            self._draw_bounds(ox)

    def _fill_metrics(self, algo: DEAlgorithm):
        self._set_entry(self.edit_gen, str(algo.convergence.convergence_generation))
        self._set_entry(self.edit_maxvalue, f"{algo.convergence.max_fitness:.6f}")
        self._set_entry(self.edit_time, f"{algo.convergence.spenttime:.2f}")
        runtime = getattr(algo, "tick3", 0.0) - getattr(algo, "tick1", 0.0)
        self._set_entry(self.edit_runtime, f"{runtime:.2f}")
        self._set_entry(self.edit_initialcoverage, f"{self.state.initialcoverage*100:.2f}")
        self._set_entry(self.edit_finalcoverage, f"{self.state.finalcoverage*100:.2f}")
        self._set_entry(self.edit_movedist, f"{self.state.average_move_dis:.2f}")
        self._set_entry(self.edit_de_dist, f"{self.state.average_DE_dis:.2f}")
        self._set_entry(self.edit_optimaldist, f"{self.state.optimal_distance:.2f}")
        self._set_entry(self.edit_movednum, str(self.state.needmovednum))
        covdist = (self.state.finalcoverage * 100 / self.state.optimal_distance) if self.state.optimal_distance > 0 else 0.0
        self._set_entry(self.edit_cov_dist, f"{covdist:.2f}")

    def _draw_bounds(self, offset: int):
        xa, ya, xb, yb = 190 + offset, 84, 190 + 280 + offset, 84 + 280
        self.canvas.create_rectangle(xa, ya, xb, yb, outline="black", width=2)

    def _draw_static_layer(self, offset: int):
        radius = int(round(self.state.sense_range))
        self.canvas.configure()
        self.canvas.update()
        self.canvas.create_rectangle(0, 0, 0, 0)  # no-op to ensure canvas
        for i in range(1, self.state.static_num + 1):
            s = self.state.sensors[self.state.staticpos[i - 1]]
            self.canvas.create_oval(s.x - radius + offset, s.y - radius, s.x + radius + offset, s.y + radius, fill="", outline="lightgray")
        for i in range(1, self.state.static_num + 1):
            s = self.state.sensors[self.state.staticpos[i - 1]]
            r = 3
            self.canvas.create_oval(s.x - r + offset, s.y - r, s.x + r + offset, s.y + r, fill="black", outline="black")

    def _draw_mobile_layer(self, mob: list, offset: int, squares=True, lines_from_initial=True):
        radius = int(round(self.state.sense_range))
        for i in range(1, self.state.mobile_num + 1):
            m = mob[i]
            self.canvas.create_oval(m.x - radius + offset, m.y - radius, m.x + radius + offset, m.y + radius, fill="", outline="gray")
        for i in range(1, self.state.mobile_num + 1):
            m = mob[i]
            r = 3
            if squares:
                self.canvas.create_rectangle(m.x - r + offset, m.y - r, m.x + r + offset, m.y + r, fill="green", outline="green")
            else:
                self.canvas.create_oval(m.x - r + offset, m.y - r, m.x + r + offset, m.y + r, fill="green", outline="green")
        if lines_from_initial:
            for i in range(1, self.state.mobile_num + 1):
                s = self.state.sensors[self.state.mobilepos[i]]
                m = mob[i]
                self.canvas.create_line(s.x + offset, s.y, m.x + offset, m.y, fill="black")

    def _draw_column_initial(self, offset: int):
        self._draw_static_layer(offset)
        init_mob = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        for i in range(1, self.state.mobile_num + 1):
            s = self.state.sensors[self.state.mobilepos[i]]
            init_mob[i] = Sensor(s.x, s.y, s.id)
        self._draw_mobile_layer(init_mob, offset, squares=True, lines_from_initial=False)

    def _draw_column_positions(self, mob: list, offset: int):
        self._draw_static_layer(offset)
        self._draw_mobile_layer(mob, offset, squares=True, lines_from_initial=True)
