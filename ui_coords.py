import tkinter as tk
from tkinter import ttk
from core.params import GlobalState, Sensor


class CoordsForm(tk.Toplevel):
    def __init__(self, master=None, state: GlobalState = None, mode: str = "initial"):
        super().__init__(master)
        self.state = state or GlobalState()
        self.mode = mode
        self.title("节点坐标")
        self.geometry("840x620")
        self.canvas = tk.Canvas(self, width=785, height=481, bg="white")
        self.canvas.pack(padx=16, pady=16)
        btn = ttk.Button(self, text="确定", command=self.destroy)
        btn.pack(pady=8)
        self._render()

    def _render(self):
        if self.mode == "optimized":
            self.title("传感器网络节点优化后的布局")
        else:
            self.title("传感器网络节点初始布局")
        xa, ya, xb, yb = 190, 84, 190 + 280, 84 + 280
        self.canvas.create_rectangle(xa, ya, xb, yb, outline="blue", width=2)
        if self.mode == "optimized":
            for i in range(1, self.state.static_num + 1):
                s = self.state.sensors[self.state.staticpos[i - 1]]
                r = 3
                self.canvas.create_oval(s.x - r, s.y - r, s.x + r, s.y + r, fill="blue", outline="blue")
            for i in range(1, self.state.mobile_num + 1):
                m = self.state.bestmobileposition[i]
                r = 3
                self.canvas.create_oval(m.x - r, m.y - r, m.x + r, m.y + r, fill="green", outline="green")
        else:
            for i in range(1, self.state.allsensornum + 1):
                s = self.state.sensors[i]
                r = 3
                self.canvas.create_oval(s.x - r, s.y - r, s.x + r, s.y + r, fill="blue", outline="blue")
