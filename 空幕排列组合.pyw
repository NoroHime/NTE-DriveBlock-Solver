import tkinter as tk
from tkinter import messagebox
import json
import os

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
        self.is_erasing = False
        
        self.config_file = "puzzle_config.json"
        self.shape_buttons = {} # 用于存储形状按钮的引用，以便动态修改状态
        
        self.setup_ui()
        self.load_config() # 启动时加载配置
        self.update_ui_state() # 初始化UI状态

    def setup_ui(self):
        # 左侧：画布
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_frame, text="1. 绘制空幕 (灰=不可用)", font=("Arial", 11, "bold")).pack(pady=5)
        self.canvas = tk.Canvas(left_frame, width=self.grid_size*self.cell_size, height=self.grid_size*self.cell_size, bg="white", highlightthickness=1, highlightbackground="black")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.toggle_cell)
        self.canvas.bind("<B1-Motion>", self.draw_cell)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release) # 拖拽结束后保存配置
        self.draw_grid()

        # 中间：必选形状与优先级控制
        mid_frame = tk.Frame(self.root, padx=10, pady=10)
        mid_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(mid_frame, text="2. 添加套装必选形状", font=("Arial", 11, "bold")).pack(pady=(5, 0))
        
        # 剩余格子提示标签
        self.lbl_remaining = tk.Label(mid_frame, text="剩余可用格子数: 25", font=("Arial", 9), fg="blue")
        self.lbl_remaining.pack(pady=(0, 5))
        
        # 形状选择按钮 (按类型分组显示)
        shape_btns_frame = tk.Frame(mid_frame)
        shape_btns_frame.pack()
        
        row, col = 0, 0
        for name in SPECIFIC_SHAPES.keys():
            btn = tk.Button(shape_btns_frame, text=name, width=8, command=lambda n=name: self.add_required(n))
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.shape_buttons[name] = btn # 保存按钮引用
            col += 1
            if col > 2:  # 每行3个按钮
                col = 0
                row += 1

        tk.Label(mid_frame, text="已选套装需求:", font=("Arial", 10)).pack(pady=(10, 0))
        self.req_listbox = tk.Listbox(mid_frame, height=6, width=25)
        self.req_listbox.pack()
        
        # 列表操作按钮区
        list_btn_frame = tk.Frame(mid_frame)
        list_btn_frame.pack(pady=5)
        tk.Button(list_btn_frame, text="删除选中", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(list_btn_frame, text="清空已选", command=self.clear_required).pack(side=tk.LEFT, padx=5)

        tk.Label(mid_frame, text="3. 剩余空间填充优先级", font=("Arial", 11, "bold")).pack(pady=(15, 5))
        self.priority_var = tk.IntVar(value=3)
        tk.Radiobutton(mid_frame, text="优先 II型 (2格)", variable=self.priority_var, value=2, command=self.save_config).pack(anchor=tk.W)
        tk.Radiobutton(mid_frame, text="优先 III型 (3格)", variable=self.priority_var, value=3, command=self.save_config).pack(anchor=tk.W)
        tk.Radiobutton(mid_frame, text="优先 IV型 (4格)", variable=self.priority_var, value=4, command=self.save_config).pack(anchor=tk.W)

        tk.Button(mid_frame, text="开始组合 (最多10种)", command=self.run_solver, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=5).pack(fill=tk.X, pady=20)

        # 右侧：结果展示区
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="组合结果 (前10种):", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        self.result_frame = tk.Frame(right_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

    def load_config(self):
        """从本地加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.board_state = data.get("board_state", self.board_state)
                self.required_shapes = data.get("required_shapes", [])
                self.priority_var.set(data.get("priority", 3))
                
                # 恢复列表框显示
                self.req_listbox.delete(0, tk.END)
                for req in self.required_shapes:
                    self.req_listbox.insert(tk.END, req)
                
                self.draw_grid()
            except Exception as e:
                print(f"读取配置失败: {e}")

    def save_config(self):
        """保存当前状态到本地配置文件"""
        data = {
            "board_state": self.board_state,
            "required_shapes": self.required_shapes,
            "priority": self.priority_var.get()
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def update_ui_state(self):
        """更新剩余格子提示，并动态禁用不可用的形状按钮"""
        # 计算空幕总可用格子
        total_available = sum(1 for r in range(self.grid_size) for c in range(self.grid_size) if self.board_state[r][c])
        # 计算已选形状占用的格子
        used_cells = sum(int(name[0]) for name in self.required_shapes)
        # 剩余格子
        rem_cells = total_available - used_cells
        
        # 更新提示文本
        if rem_cells < 0:
            self.lbl_remaining.config(text=f"空间不足！超出 {-rem_cells} 格", fg="red")
        else:
            self.lbl_remaining.config(text=f"剩余可用格子数: {rem_cells}", fg="blue")
            
        # 动态更新按钮状态
        for name, btn in self.shape_buttons.items():
            shape_size = int(name[0])
            if shape_size > rem_cells:
                btn.config(state=tk.DISABLED)
            else:
                btn.config(state=tk.NORMAL)

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
            self.is_erasing = not self.board_state[r][c] 
            self.board_state[r][c] = self.is_erasing
            self.draw_grid()
            self.update_ui_state()
            self.save_config()

    def draw_cell(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            if self.board_state[r][c] != self.is_erasing:
                self.board_state[r][c] = self.is_erasing
                self.draw_grid()
                self.update_ui_state()
                # 注意：拖拽过程中不频繁保存文件，避免卡顿

    def on_drag_release(self, event):
        """拖拽结束后统一保存一次配置"""
        self.save_config()

    def add_required(self, shape_name):
        """添加新形状到列表，并自动选中和定位"""
        self.required_shapes.append(shape_name)
        self.req_listbox.insert(tk.END, shape_name)
        
        # 1. 清除当前列表中的所有选中状态（防止多选冲突）
        self.req_listbox.selection_clear(0, tk.END)
        # 2. 获取新添加项的索引（即最后一项）
        new_index = len(self.required_shapes) - 1
        # 3. 选中刚刚添加的新项
        self.req_listbox.selection_set(new_index)
        # 4. 自动滚动列表，确保新添加的项在可视范围内
        self.req_listbox.see(new_index)
        
        self.update_ui_state()
        self.save_config()

    def delete_selected(self):
        """删除列表框中当前选中的单个形状，并自动选中下一个或最后一个"""
        selection = self.req_listbox.curselection()
        if selection:
            index = selection[0]
            # 从UI列表和数据列表中删除
            self.req_listbox.delete(index)
            del self.required_shapes[index]
            
            # 清除可能残留的选中状态
            self.req_listbox.selection_clear(0, tk.END)
            
            # 如果删除后列表还不为空，则自动选中
            if self.required_shapes:
                # 如果删除的是原本的最后一个，index 会等于现在的列表长度（越界）
                # 此时让它选中现在的最后一个；否则选中当前 index 位置的新元素
                new_index = index if index < len(self.required_shapes) else len(self.required_shapes) - 1
                self.req_listbox.selection_set(new_index)
                # 确保删除后，自动选中的那个元素也在可视范围内
                self.req_listbox.see(new_index)
                
            self.update_ui_state()
            self.save_config()

    def clear_required(self):
        self.required_shapes.clear()
        self.req_listbox.delete(0, tk.END)
        self.update_ui_state()
        self.save_config()

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