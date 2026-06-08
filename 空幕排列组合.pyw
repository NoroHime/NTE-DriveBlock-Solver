import tkinter as tk
from tkinter import messagebox

# ==================== 1. 严格定义形状库 ====================
# 严格按照截图中的方块定义，绝对不进行任何旋转和翻转！
# 坐标系：(行, 列)，(0,0) 为该形状最左上角的基准点
SPECIFIC_SHAPES = {
    # II型驱动
    "2-横": [[(0, 0), (0, 1)]],
    "2-竖": [[(0, 0), (1, 0)]],

    # III型驱动
    "3-横": [[(0, 0), (0, 1), (0, 2)]],
    "3-竖": [[(0, 0), (1, 0), (2, 0)]],
    "3-左上": [[(0, 0), (0, 1), (1, 0)]], # 缺口在右下
    "3-右上": [[(0, 0), (0, 1), (1, 1)]], # 缺口在左下
    "3-左下": [[(0, 0), (1, 0), (1, 1)]], # 缺口在右上
    "3-右下": [[(0, 1), (1, 0), (1, 1)]], # 缺口在左上

    # IV型驱动 (根据截图可见部分提取)
    "4-横": [[(0, 0), (0, 1), (0, 2), (0, 3)]],
    "4-竖": [[(0, 0), (1, 0), (2, 0), (3, 0)]],
    "4-Z型": [[(0, 1), (1, 0), (1, 1), (2, 0)]], # 截图中第3个
    "4-S型": [[(0, 0), (1, 0), (1, 1), (2, 1)]], # 截图中第4个
}

# 规范化坐标：确保基准点正确
for name, shapes in SPECIFIC_SHAPES.items():
    norm_shapes = []
    for shape in shapes:
        shape.sort() # 按 (r, c) 排序，第一个元素就是最靠上、最靠左的方块
        # 【修复Bug关键】：基准点必须是形状中实际存在的左上角方块，不能是 min(r) 和 min(c) 的组合！
        r0, c0 = shape[0] 
        norm = tuple(sorted((r - r0, c - c0) for r, c in shape))
        if norm not in norm_shapes:
            norm_shapes.append(norm)
    SPECIFIC_SHAPES[name] = norm_shapes

# 用于剩余空间填充的通用形状库
GENERAL_SHAPES = {
    2: SPECIFIC_SHAPES["2-横"] + SPECIFIC_SHAPES["2-竖"],
    3: SPECIFIC_SHAPES["3-横"] + SPECIFIC_SHAPES["3-竖"] + SPECIFIC_SHAPES["3-左上"] + 
       SPECIFIC_SHAPES["3-右上"] + SPECIFIC_SHAPES["3-左下"] + SPECIFIC_SHAPES["3-右下"],
    4: SPECIFIC_SHAPES["4-横"] + SPECIFIC_SHAPES["4-竖"] + SPECIFIC_SHAPES["4-Z型"] + SPECIFIC_SHAPES["4-S型"]
}

# ==================== 2. 核心算法 ====================

def get_partitions(target_area):
    """计算剩余面积能用哪些2/3/4型组合填满"""
    partitions = []
    def dfs_part(rem, current_part):
        if rem == 0:
            partitions.append(current_part)
            return
        for p in [2, 3, 4]:
            if not current_part or p <= current_part[-1]:
                if rem >= p:
                    dfs_part(rem - p, current_part + [p])
    dfs_part(target_area, [])
    return partitions

def solve_board(board_cells, required_shape_names, priority):
    total_area = len(board_cells)
    
    # 1. 计算必选形状占用的面积
    req_area = 0
    for name in required_shape_names:
        req_area += int(name[0]) # 名字的第一位就是占格数(2/3/4)
        
    rem_area = total_area - req_area
    if rem_area < 0:
        return [] # 必选形状面积超过了画布总面积

    # 2. 计算剩余面积的填充组合
    partitions = get_partitions(rem_area)
    if rem_area > 0 and not partitions:
        return [] # 剩余面积无法被2/3/4整除
        
    if not partitions:
        partitions = [[]] # 如果刚好填满，组合为空

    # 根据优先级排序填充组合
    partitions.sort(key=lambda p: p.count(priority), reverse=True)

    all_solutions = []
    seen_solutions = set()

    def dfs(cells_left, req_left, filler_counts, current_solution):
        if len(all_solutions) >= 10:
            return
        if not cells_left:
            # 【修复Bug】：必须确保必选形状也被全部用完，才能算作成功解
            if not req_left:
                sol_tuple = frozenset(frozenset(piece) for piece in current_solution)
                if sol_tuple not in seen_solutions:
                    seen_solutions.add(sol_tuple)
                    all_solutions.append(current_solution)
            return

        # 找到最左上角的空位，强制从这里开始填，减少搜索分支
        r, c = min(cells_left)

        # 优先尝试放置必选的特定形状 (使用 set 去重，防止相同的必选形状重复搜索)
        for req_name in set(req_left):
            i = req_left.index(req_name)
            for shape in SPECIFIC_SHAPES[req_name]:
                # 尝试将形状的左上角对齐到当前空格 (r, c)
                placed_piece = {(r + dr, c + dc) for dr, dc in shape}
                if placed_piece.issubset(cells_left):
                    next_req = req_left[:i] + req_left[i+1:]
                    dfs(cells_left - placed_piece, next_req, filler_counts, current_solution + [placed_piece])
                    if len(all_solutions) >= 10: return

        # 尝试放置剩余的填充形状
        for size, count in filler_counts.items():
            if count > 0:
                filler_counts[size] -= 1
                for shape in GENERAL_SHAPES[size]:
                    placed_piece = {(r + dr, c + dc) for dr, dc in shape}
                    if placed_piece.issubset(cells_left):
                        dfs(cells_left - placed_piece, req_left, filler_counts, current_solution + [placed_piece])
                        if len(all_solutions) >= 10: return
                filler_counts[size] += 1

    # 按优先级顺序尝试每一种填充组合
    for part in partitions:
        counts = {2: part.count(2), 3: part.count(3), 4: part.count(4)}
        dfs(set(board_cells), required_shape_names, counts, [])
        if len(all_solutions) >= 10:
            break

    return all_solutions

# ==================== 3. GUI 界面 ====================

class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("异环空幕排列组合")
        self.root.geometry("1000x650")
        
        self.grid_size = 5
        self.cell_size = 45
        self.board_state = [[True for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.required_shapes = []
        self.is_erasing = False # 【修复Bug】：用于记录拖拽时是涂灰还是擦除
        
        self.setup_ui()

    def setup_ui(self):
        # 左侧：画布
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_frame, text="1. 绘制空幕 (灰=不可用)", font=("Arial", 11, "bold")).pack(pady=5)
        self.canvas = tk.Canvas(left_frame, width=self.grid_size*self.cell_size, height=self.grid_size*self.cell_size, bg="white", highlightthickness=1, highlightbackground="black")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.toggle_cell)
        self.canvas.bind("<B1-Motion>", self.draw_cell)
        self.draw_grid()

        # 中间：必选形状与优先级控制
        mid_frame = tk.Frame(self.root, padx=10, pady=10)
        mid_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(mid_frame, text="2. 添加套装必选形状", font=("Arial", 11, "bold")).pack(pady=5)
        
        # 形状选择按钮 (按类型分组显示)
        shape_btns_frame = tk.Frame(mid_frame)
        shape_btns_frame.pack()
        
        row, col = 0, 0
        for name in SPECIFIC_SHAPES.keys():
            tk.Button(shape_btns_frame, text=name, width=8, command=lambda n=name: self.add_required(n)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 2:  # 每行3个按钮
                col = 0
                row += 1

        tk.Label(mid_frame, text="已选套装需求:", font=("Arial", 10)).pack(pady=(10, 0))
        self.req_listbox = tk.Listbox(mid_frame, height=6, width=25)
        self.req_listbox.pack()
        
        tk.Button(mid_frame, text="清空已选", command=self.clear_required).pack(pady=5)

        tk.Label(mid_frame, text="3. 剩余空间填充优先级", font=("Arial", 11, "bold")).pack(pady=(15, 5))
        self.priority_var = tk.IntVar(value=3)
        tk.Radiobutton(mid_frame, text="优先 II型 (2格)", variable=self.priority_var, value=2).pack(anchor=tk.W)
        tk.Radiobutton(mid_frame, text="优先 III型 (3格)", variable=self.priority_var, value=3).pack(anchor=tk.W)
        tk.Radiobutton(mid_frame, text="优先 IV型 (4格)", variable=self.priority_var, value=4).pack(anchor=tk.W)

        tk.Button(mid_frame, text="开始组合 (最多10种)", command=self.run_solver, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=5).pack(fill=tk.X, pady=20)

        # 右侧：结果展示区
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="组合结果 (前10种):", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        self.result_frame = tk.Frame(right_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "white" if self.board_state[r][c] else "#444444"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cccccc")

    def toggle_cell(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            # 【修复Bug】：记录按下的瞬间是想涂灰还是擦除
            self.is_erasing = not self.board_state[r][c] 
            self.board_state[r][c] = self.is_erasing
            self.draw_grid()

    def draw_cell(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            # 【修复Bug】：拖拽时保持初始意图，实现丝滑滑动
            if self.board_state[r][c] != self.is_erasing:
                self.board_state[r][c] = self.is_erasing
                self.draw_grid()

    def add_required(self, shape_name):
        self.required_shapes.append(shape_name)
        self.req_listbox.insert(tk.END, shape_name)

    def clear_required(self):
        self.required_shapes.clear()
        self.req_listbox.delete(0, tk.END)

    def run_solver(self):
        board_cells = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size) if self.board_state[r][c]]
        
        if not board_cells:
            messagebox.showwarning("提示", "空幕为空！")
            return
            
        priority = self.priority_var.get()
        
        for widget in self.result_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.result_frame, text="正在计算排列组合...").pack()
        self.root.update()

        solutions = solve_board(board_cells, self.required_shapes, priority)

        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if not solutions:
            tk.Label(self.result_frame, text="没有找到可行的组合方案。\n请检查：\n1. 空间是否足够放下必选形状\n2. 剩余空间能否被2/3/4整除\n3. 形状不可旋转，请确认空幕形状是否匹配", fg="red", justify=tk.LEFT).pack(anchor=tk.W)
            return

        colors = ["#FF9999", "#99CCFF", "#99FF99", "#FFCC99", "#CC99FF", "#FFFF99", "#FF99CC", "#99FFFF", "#C0C0C0", "#FFD700"]
        
        for i, sol in enumerate(solutions):
            row, col = divmod(i, 5)
            
            res_canvas = tk.Canvas(self.result_frame, width=70, height=70, bg="white", highlightthickness=1, highlightbackground="#aaa")
            res_canvas.grid(row=row, column=col, padx=5, pady=5)
            
            scale = 70 / self.grid_size
            
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if not self.board_state[r][c]:
                        res_canvas.create_rectangle(c*scale, r*scale, (c+1)*scale, (r+1)*scale, fill="#444444", outline="")
            
            for piece_idx, piece in enumerate(sol):
                color = colors[piece_idx % len(colors)]
                for (r, c) in piece:
                    res_canvas.create_rectangle(c*scale, r*scale, (c+1)*scale, (r+1)*scale, fill=color, outline="black")

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()