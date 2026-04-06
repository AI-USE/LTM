import tkinter as tk
import random
import time

class CyberTheme:
    """
    SHINOBIの「ハッカー風」UIテーマ設定。
    """
    BG_COLOR = "#0D0D0D" # 超ダークグレー（ほぼ黒）
    FG_ACCENT = "#00FF41" # マトリックス・グリーン
    FG_WARNING = "#FF003C" # ネオン・レッド
    FG_INFO = "#00E5FF" # サイバー・ブルー
    FONT_MONO = ("Consolas", 12)
    FONT_HEADER = ("Consolas", 48, "bold")
    FONT_SUB = ("Consolas", 18)

class MatrixRain(tk.Canvas):
    """
    背景に流れるマトリックス風のデジタル・レイン（簡易版）。
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=CyberTheme.BG_COLOR, highlightthickness=0, **kwargs)
        self.columns = []
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        self.chars = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.root = master
        self.root.after(100, self.setup_rain)

    def setup_rain(self):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        font_size = 14
        num_columns = self.width // font_size
        for i in range(num_columns):
            self.columns.append({
                "x": i * font_size,
                "y": random.randint(-self.height, 0),
                "speed": random.randint(5, 15),
                "chars": []
            })
        self.animate()

    def animate(self):
        self.delete("all")
        for col in self.columns:
            char = random.choice(self.chars)
            # 文字を描画（先端は白、後ろは緑）
            self.create_text(col["x"], col["y"], text=char, fill=CyberTheme.FG_ACCENT, font=("Consolas", 12), anchor="nw")

            col["y"] += col["speed"]
            if col["y"] > self.height:
                col["y"] = random.randint(-200, 0)
                col["speed"] = random.randint(5, 15)

        self.root.after(50, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    rain = MatrixRain(root)
    rain.pack(expand=True, fill="both")
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()
