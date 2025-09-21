import tkinter as tk
from tkinter import ttk
from Database import Database

class App:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.configure(bg="Snow")
        self.root.title("CUD Notification App")
        self.root.geometry("980x500")
        self.root.resizable(False, False)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(root)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar()
        
        self.create_cards()

    def scrollbar(self):
        vertical_scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.canvas.yview)
        vertical_scrollbar.grid(row=0, column=1, sticky='ns')

        self.canvas.configure(yscrollcommand=vertical_scrollbar.set)
    
    def configure_scroll_region(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def bind_to_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel)

    def create_scrollable_label(self, parent, **kwargs):
        label = tk.Label(parent, **kwargs)
        label.pack(pady=(10, 5), fill='x', padx=10)
        self.bind_to_mousewheel(label)
        return label

    def create_cards(self):
        db = Database()
        tasks = db.get_tasks_details()

        inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=inner_frame, anchor='nw')

        #self.create_scrollable_label(self.canvas, text="All Tasks", justify="center", font=("Arial", 12, "bold"))

        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.columnconfigure(0, weight=1)
        inner_frame.columnconfigure(1, weight=1)

        inner_frame.bind('<Configure>', self.configure_scroll_region)
        self.bind_to_mousewheel(inner_frame)
        self.bind_to_mousewheel(self.canvas)
        
        # Configure grid weights for responsive layout
        self.canvas.columnconfigure(0, weight=1)
        self.canvas.columnconfigure(1, weight=1)
        self.canvas.columnconfigure(2, weight=1)
        
        for i, task in enumerate(tasks):
            row = i // 3
            col = i % 3
            
            status = task['status']
            card_color = 'light green' if status == 'Submitted for grading' else 'light red'
            # Create card with consistent styling
            card = tk.Frame(
                inner_frame, 
                background=card_color,
                relief=tk.RAISED,
                borderwidth=1,
                height=150
            )
            self.bind_to_mousewheel(card)
            card.grid(column=col, row=row, padx=10, pady=10, sticky="nsew")

            card.grid_propagate(False)
            card.columnconfigure(0, weight=1)
            
            # Add content to card
            self.create_scrollable_label(
                card,
                text=task['course'], 
                font=("Arial", 12, "bold"), 
                background=card_color, 
                wraplength=300
            )

            self.create_scrollable_label(
                card, 
                text=f"Assignment: {task['assignment']}", 
                background=card_color,
                wraplength=300
            )

            self.create_scrollable_label(
                card, 
                text=f"Due on: {task['due_date']}", 
                background=card_color,
                wraplength=300
            )

