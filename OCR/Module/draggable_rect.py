class DraggableRect:
    def __init__(self, x, y, w, h, label, color=(0,0,255)):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.color = color
        self.mode = None
        self.selected = False
        self.resize_corner = -1
        self.handle_size = 8
        self.snap = 10
        self.min_size = 10
    def contains(self, px, py):
        if None in (self.x, self.y, self.w, self.h):
            return False
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h
    def handle_contains(self, px, py):
        if None in (self.x, self.y, self.w, self.h):
            return -1
        corners = [
            (self.x, self.y),
            (self.x + self.w, self.y),
            (self.x, self.y + self.h),
            (self.x + self.w, self.y + self.h)
        ]
        for idx, (cx, cy) in enumerate(corners):
            if abs(px - cx) <= self.handle_size and abs(py - cy) <= self.handle_size:
                return idx
        return -1
    def start_drag_or_resize(self, px, py):
        corner = self.handle_contains(px, py)
        if corner >= 0:
            self.mode = "resize"
            self.resize_corner = corner
            self.selected = True
        elif self.contains(px, py):
            self.mode = "drag"
            self.selected = True
        else:
            self.mode = None
            self.selected = False

    def end_drag_or_resize(self):
        self.mode = None
        self.resize_corner = -1
        self.selected = False
    def move(self, dx, dy, maxw, maxh):
        if self.mode != "drag" or not self.selected: return
        self.x = max(0, min(self.x + dx, maxw - self.w))
        self.y = max(0, min(self.y + dy, maxh - self.h))
    def resize(self, dx, dy, maxw, maxh):
        if self.mode != "resize" or not self.selected: return
        c = self.resize_corner
        if c == 0:  # top-left
            self.x = max(0, min(self.x + dx, self.x+self.w-self.min_size))
            self.y = max(0, min(self.y + dy, self.y+self.h-self.min_size))
            self.w = self.w - dx
            self.h = self.h - dy
        elif c == 1:  # top-right
            self.w = max(self.min_size, min(self.w + dx, maxw - self.x))
            self.y = max(0, min(self.y + dy, self.y+self.h-self.min_size))
            self.h = self.h - dy
        elif c == 2:  # bottom-left
            self.x = max(0, min(self.x + dx, self.x+self.w-self.min_size))
            self.w = self.w - dx
            self.h = max(self.min_size, min(self.h + dy, maxh - self.y))
        elif c == 3:  # bottom-right
            self.w = max(self.min_size, min(self.w + dx, maxw - self.x))
            self.h = max(self.min_size, min(self.h + dy, maxh - self.y))
    def snap_to_grid(self):
        self.x = (self.x // self.snap) * self.snap
        self.y = (self.y // self.snap) * self.snap
        self.w = (self.w // self.snap) * self.snap
        self.h = (self.h // self.snap) * self.snap