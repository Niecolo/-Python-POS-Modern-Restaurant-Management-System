"""
Python Standalone POS Application
Fully offline POS system with all features
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import csv
from datetime import datetime
import os
import threading
import time

# Database initialization
DB_NAME = "pos_database.db"

# Global database connection
db_conn = None
db_cursor = None

def get_db_connection():
    """Get a fresh database connection"""
    global db_conn, db_cursor
    if db_conn is None:
        db_conn = sqlite3.connect(DB_NAME, timeout=10)
        db_cursor = db_conn.cursor()
    return db_conn, db_cursor

def init_database():
    """Initialize the SQLite database with all tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'server',
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id INTEGER,
            emoji TEXT,
            sku TEXT,
            stock INTEGER DEFAULT 0,
            is_available INTEGER DEFAULT 1,
            preparation_time INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT UNIQUE NOT NULL,
            capacity INTEGER DEFAULT 4,
            status TEXT DEFAULT 'available',
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            order_type TEXT DEFAULT 'dine_in',
            status TEXT DEFAULT 'pending',
            table_id INTEGER,
            server_id INTEGER,
            subtotal REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES tables(id),
            FOREIGN KEY (server_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            server_id INTEGER,
            quantity INTEGER DEFAULT 1,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (server_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_number TEXT UNIQUE NOT NULL,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT DEFAULT 'cash',
            status TEXT DEFAULT 'pending',
            transaction_id TEXT,
            processed_by INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (processed_by) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        insert_demo_data(cursor)
    
    conn.commit()
    conn.close()

def insert_demo_data(cursor):
    demo_users = [
        ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'System Administrator', 'admin', 'admin@posystem.com', '+1234567890'),
        ('manager1', hashlib.sha256('admin123'.encode()).hexdigest(), 'John Manager', 'manager', 'manager@posystem.com', '+1234567891'),
        ('server1', hashlib.sha256('admin123'.encode()).hexdigest(), 'Sarah Server', 'server', 'server1@posystem.com', '+1234567892'),
        ('server2', hashlib.sha256('admin123'.encode()).hexdigest(), 'Mike Waiter', 'server', 'server2@posystem.com', '+1234567893'),
        ('counter1', hashlib.sha256('admin123'.encode()).hexdigest(), 'Emily Cashier', 'counter', 'counter1@posystem.com', '+1234567894'),
        ('kitchen1', hashlib.sha256('admin123'.encode()).hexdigest(), 'Chef Gordon', 'kitchen', 'kitchen@posystem.com', '+1234567895'),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password, full_name, role, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
        demo_users
    )
    
    demo_categories = [
        ('Appetizers', 'Starters and small bites', '🥗', 1),
        ('Main Course', 'Hearty main dishes', '🍽️', 2),
        ('Pizza', 'Hand-tossed pizzas', '🍕', 3),
        ('Beverages', 'Hot and cold drinks', '☕', 4),
        ('Desserts', 'Sweet treats', '🍰', 5),
    ]
    cursor.executemany(
        "INSERT INTO categories (name, description, icon, sort_order) VALUES (?, ?, ?, ?)",
        demo_categories
    )
    
    demo_products = [
        ('Caesar Salad', 'Fresh romaine with Caesar dressing', 9.99, 1, '🥗'),
        ('Chicken Wings', 'Crispy wings with sauce', 11.99, 1, '🍗'),
        ('French Fries', 'Golden crispy fries', 5.99, 1, '🍟'),
        ('Garlic Bread', 'Toasted with garlic butter', 4.99, 1, '🥖'),
        ('Classic Burger', 'Beef patty with toppings', 12.99, 2, '🍔'),
        ('Grilled Salmon', 'Atlantic salmon fillet', 22.99, 2, '🐟'),
        ('Pasta Carbonara', 'Creamy pasta with bacon', 15.99, 2, '🍝'),
        ('Steak', 'Premium ribeye steak', 28.99, 2, '🥩'),
        ('Margherita Pizza', 'Classic tomato and mozzarella', 14.99, 3, '🍕'),
        ('Pepperoni Pizza', 'Pizza with pepperoni', 16.99, 3, '🍕'),
        ('Cappuccino', 'Espresso with milk foam', 4.99, 4, '☕'),
        ('Fresh Juice', 'Fresh fruit juice', 5.99, 4, '🧃'),
        ('Red Wine', 'House red wine', 12.99, 4, '🍷'),
        ('Beer', 'Draft beer', 6.99, 4, '🍺'),
        ('Chocolate Cake', 'Rich chocolate layer cake', 7.99, 5, '🍰'),
        ('Ice Cream', 'Three scoops', 6.99, 5, '🍨'),
    ]
    cursor.executemany(
        "INSERT INTO products (name, description, price, category_id, emoji) VALUES (?, ?, ?, ?, ?)",
        demo_products
    )
    
    demo_tables = [
        ('1', 2, 'available', 'Indoor'),
        ('2', 4, 'available', 'Indoor'),
        ('3', 4, 'available', 'Indoor'),
        ('4', 6, 'available', 'Indoor'),
        ('5', 4, 'available', 'Indoor'),
        ('6', 2, 'available', 'Indoor'),
        ('7', 8, 'available', 'Indoor'),
        ('8', 4, 'available', 'Indoor'),
        ('O1', 4, 'available', 'Outdoor'),
        ('O2', 6, 'available', 'Outdoor'),
        ('O3', 4, 'available', 'Outdoor'),
        ('O4', 2, 'available', 'Outdoor'),
        ('V1', 10, 'available', 'VIP'),
        ('V2', 8, 'available', 'VIP'),
    ]
    cursor.executemany(
        "INSERT INTO tables (table_number, capacity, status, location) VALUES (?, ?, ?, ?)",
        demo_tables
    )
    
    demo_settings = [
        ('restaurant_name', 'TanStack Restaurant', 'Restaurant name'),
        ('currency_symbol', '$', 'Currency symbol'),
        ('tax_rate', '10', 'Tax rate percentage'),
        ('receipt_header', 'Thank you for dining with us!', 'Receipt header'),
        ('receipt_footer', 'Please visit us again!', 'Receipt footer'),
    ]
    cursor.executemany(
        "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
        demo_settings
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_setting(key, default=''):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    return result[0] if result else default

def get_currency():
    return get_setting('currency_symbol', '$')

COLORS = {
    'bg_dark': '#0f0f23',
    'bg_medium': '#1a1a2e',
    'bg_light': '#16213e',
    'bg_lighter': '#0f3460',
    'accent': '#00d4ff',
    'accent_hover': '#00a8cc',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'text': '#ffffff',
    'text_secondary': '#94a3b8',
    'border': '#334155'
}

class POSApplication(tk.Tk):
    
    def __init__(self):
        super().__init__()
        
        self.title(f"{get_setting('restaurant_name', 'TanStack POS')} - Restaurant Management System")
        self.geometry("1400x900")
        self.configure(bg=COLORS['bg_dark'])
        
        self.minsize(1024, 700)
        
        # Open maximized
        self.state('zoomed')
        
        init_database()
        
        self.current_user = None
        self.refresh_callbacks = []
        
        self.show_login()
    
    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    def register_refresh(self, callback):
        """Register a callback to be called on refresh"""
        if callback not in self.refresh_callbacks:
            self.refresh_callbacks.append(callback)
    
    def trigger_refresh(self):
        """Trigger all registered refresh callbacks"""
        for callback in self.refresh_callbacks:
            try:
                callback()
            except:
                pass
    
    def create_styled_button(self, parent, text, command, bg=COLORS['accent'], fg='#000000', width=None):
        btn = tk.Button(parent, text=text, command=command, 
                       bg=bg, fg=fg, font=('Arial', 10, 'bold'),
                       relief=tk.FLAT, borderwidth=0, padx=15, pady=8,
                       cursor='hand2')
        if width:
            btn.config(width=width)
        return btn
    
    def create_header(self, parent, title, subtitle=""):
        header_frame = tk.Frame(parent, bg=COLORS['bg_lighter'])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(header_frame, text=title, font=('Arial', 22, 'bold'),
                             bg=COLORS['bg_lighter'], fg=COLORS['accent'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        if subtitle:
            sub_label = tk.Label(header_frame, text=subtitle, font=('Arial', 10),
                                bg=COLORS['bg_lighter'], fg=COLORS['text_secondary'])
            sub_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        return header_frame
    
    def refresh_title(self):
        self.title(f"{get_setting('restaurant_name', 'TanStack POS')} - Restaurant Management System")
    
    def show_login(self):
        self.clear_window()
        
        main_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        card = tk.Frame(main_frame, bg=COLORS['bg_medium'], relief=tk.FLAT, borderwidth=0)
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=420, height=540)
        
        accent_bar = tk.Frame(card, bg=COLORS['accent'], height=4)
        accent_bar.pack(fill=tk.X)
        
        logo_frame = tk.Frame(card, bg=COLORS['bg_medium'])
        logo_frame.pack(pady=(30, 10))
        
        restaurant_name = get_setting('restaurant_name', 'Restaurant')
        tk.Label(logo_frame, text=restaurant_name, font=('Arial', 26, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['accent']).pack(pady=(10, 5))
        
        tk.Label(card, text="Restaurant Management System",
                font=('Arial', 11), bg=COLORS['bg_medium'], fg=COLORS['text_secondary']).pack()
        
        form_frame = tk.Frame(card, bg=COLORS['bg_medium'])
        form_frame.pack(pady=20, fill=tk.X, padx=30)
        
        tk.Label(form_frame, text="Username", font=('Arial', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=tk.W, pady=(10, 5))
        
        self.username_entry = tk.Entry(form_frame, font=('Arial', 12), 
                                       bg=COLORS['bg_lighter'], fg=COLORS['text'],
                                       relief=tk.FLAT, borderwidth=0, insertbackground=COLORS['text'])
        self.username_entry.pack(fill=tk.X, pady=5)
        
        tk.Frame(form_frame, bg=COLORS['accent'], height=2).pack(fill=tk.X)
        
        tk.Label(form_frame, text="Password", font=('Arial', 10, 'bold'),
                bg=COLORS['bg_medium'], fg=COLORS['text']).pack(anchor=tk.W, pady=(15, 5))
        
        self.password_entry = tk.Entry(form_frame, font=('Arial', 12), show='*',
                                       bg=COLORS['bg_lighter'], fg=COLORS['text'],
                                       relief=tk.FLAT, borderwidth=0, insertbackground=COLORS['text'])
        self.password_entry.pack(fill=tk.X, pady=5)
        
        tk.Frame(form_frame, bg=COLORS['accent'], height=2).pack(fill=tk.X)
        
        login_btn = self.create_styled_button(form_frame, "SIGN IN", self.login, 
                                              bg=COLORS['accent'], width=20)
        login_btn.pack(pady=25)
        
        demo_frame = tk.LabelFrame(card, text="Quick Login", font=('Arial', 10, 'bold'),
                                   bg=COLORS['bg_medium'], fg=COLORS['accent'],
                                   bd=0, padx=15, pady=10)
        demo_frame.pack(pady=10, padx=20, fill=tk.X)
        
        demo_users = [
            ('admin', 'Administrator'),
            ('manager1', 'Manager'),
            ('server1', 'Server'),
            ('kitchen1', 'Kitchen'),
        ]
        
        for username, role in demo_users:
            btn = tk.Button(demo_frame, text=f"{username} ({role})",
                           command=lambda u=username: self.quick_login(u),
                           bg=COLORS['bg_lighter'], fg=COLORS['text'],
                           relief=tk.FLAT, font=('Arial', 9),
                           cursor='hand2')
            btn.pack(fill=tk.X, pady=2)
        
        self.password_entry.bind('<Return>', lambda e: self.login())
        self.username_entry.bind('<Return>', lambda e: self.login())
    
    def quick_login(self, username):
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, 'admin123')
        self.login()
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        conn, cursor = get_db_connection()
        
        cursor.execute("SELECT id, username, full_name, role FROM users WHERE username = ? AND password = ? AND is_active = 1",
                      (username, hash_password(password)))
        user = cursor.fetchone()
        
        if user:
            self.current_user = {'id': user[0], 'username': user[1], 'full_name': user[2], 'role': user[3]}
            self.refresh_title()
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def show_dashboard(self):
        self.clear_window()
        
        header = tk.Frame(self, bg=COLORS['bg_lighter'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        restaurant_name = get_setting('restaurant_name', 'Restaurant')
        tk.Label(header, text=f"🍽️ {restaurant_name}", font=('Arial', 18, 'bold'),
                bg=COLORS['bg_lighter'], fg=COLORS['accent']).pack(side=tk.LEFT, padx=20)
        
        user_info = tk.Frame(header, bg=COLORS['bg_lighter'])
        user_info.pack(side=tk.RIGHT, padx=20)
        
        role_colors = {
            'admin': COLORS['danger'],
            'manager': '#8b5cf6',
            'server': COLORS['accent'],
            'counter': COLORS['success'],
            'kitchen': COLORS['warning']
        }
        
        tk.Label(user_info, text=f"{self.current_user['full_name']}",
                 font=('Arial', 11, 'bold'), bg=COLORS['bg_lighter'], fg=COLORS['text']).pack(anchor=tk.E)
        
        tk.Label(user_info, text=self.current_user['role'].title(),
                 font=('Arial', 9), bg=COLORS['bg_lighter'], 
                 fg=role_colors.get(self.current_user['role'], COLORS['text_secondary'])).pack(anchor=tk.E)
        
        logout_btn = tk.Button(header, text="Logout", command=self.logout,
                             bg=COLORS['danger'], fg=COLORS['text'],
                             relief=tk.FLAT, font=('Arial', 9, 'bold'),
                             padx=15, pady=5, cursor='hand2')
        logout_btn.pack(side=tk.RIGHT, padx=10)
        
        main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        sidebar = tk.Frame(main_container, bg=COLORS['bg_medium'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        nav_items = [
            ('POS', '📱', 'main'),
            ('Kitchen', '👨‍🍳', 'kitchen'),
            ('Orders', '📋', 'orders'),
            ('Payments', '💳', 'payments'),
            ('Products', '🍽️', 'products'),
            ('Tables', '🪑', 'tables'),
            ('Staff', '👥', 'staff'),
            ('Reports', '📊', 'reports'),
            ('Settings', '⚙️', 'settings')
        ]
        
        role = self.current_user['role']
        if role == 'server':
            nav_items = [nav_items[0], nav_items[2]]
        elif role == 'counter':
            nav_items = [nav_items[0], nav_items[2], nav_items[3]]
        elif role == 'kitchen':
            nav_items = [nav_items[1], nav_items[2]]
        
        for text, icon, page in nav_items:
            btn = tk.Button(sidebar, text=f"  {icon}  {text}",
                           font=('Arial', 11), bg=COLORS['bg_medium'], fg=COLORS['text'],
                           relief=tk.FLAT, anchor=tk.W, padx=20, pady=12,
                           command=lambda p=page: self.show_page(p), cursor='hand2')
            btn.pack(fill=tk.X)
            
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['bg_lighter']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_medium']))
        
        self.content_frame = tk.Frame(main_container, bg=COLORS['bg_dark'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        if role == 'kitchen':
            self.show_page('kitchen')
        else:
            self.show_page('main')
    
    def logout(self):
        self.current_user = None
        self.show_login()
    
    def show_page(self, page_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if page_name == 'main':
            self.show_pos_page()
        elif page_name == 'kitchen':
            self.show_kitchen_page()
        elif page_name == 'orders':
            self.show_orders_page()
        elif page_name == 'payments':
            self.show_payments_page()
        elif page_name == 'products':
            self.show_products_page()
        elif page_name == 'tables':
            self.show_tables_page()
        elif page_name == 'staff':
            self.show_staff_page()
        elif page_name == 'reports':
            self.show_reports_page()
        elif page_name == 'settings':
            self.show_settings_page()
    
    def show_pos_page(self):
        selected_category = tk.StringVar(value='all')
        search_query = tk.StringVar()
        order_type = tk.StringVar(value='dine_in')
        selected_table = tk.IntVar(value=0)
        cart = []
        currency = get_currency()
        
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Point of Sale", "Create new orders")
        
        content = tk.Frame(main, bg=COLORS['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True)
        
        left = tk.Frame(content, bg=COLORS['bg_dark'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        filter_bar = tk.Frame(left, bg=COLORS['bg_dark'])
        filter_bar.pack(fill=tk.X, pady=(0, 10))
        
        search_entry = tk.Entry(filter_bar, textvariable=search_query, font=('Arial', 11),
                               bg=COLORS['bg_medium'], fg=COLORS['text'],
                               relief=tk.FLAT, insertbackground=COLORS['text'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        search_entry.bind('<KeyRelease>', lambda e: refresh_products())
        
        for otype in [('dine_in', 'Dine In'), ('takeaway', 'Takeaway'), ('delivery', 'Delivery')]:
            rb = tk.Radiobutton(filter_bar, text=otype[1], variable=order_type, value=otype[0],
                                bg=COLORS['bg_dark'], fg=COLORS['text'], selectcolor=COLORS['accent'],
                                font=('Arial', 9, 'bold'))
            rb.pack(side=tk.LEFT, padx=5)
        
        table_label = tk.LabelFrame(left, text="Select Table", bg=COLORS['bg_dark'], fg=COLORS['text'])
        table_label.pack(fill=tk.X, pady=(0, 10))
        
        conn, cursor = get_db_connection()
        cursor.execute("SELECT id, table_number, status FROM tables ORDER BY table_number")
        tables = cursor.fetchall()
        
        table_buttons = {}
        table_status = {}  # Store actual table status
        table_frame = tk.Frame(table_label, bg=COLORS['bg_dark'])
        table_frame.pack(pady=5)
        
        for table_id, table_num, status in tables:
            table_status[table_id] = status
            colors = {'available': COLORS['success'], 'occupied': COLORS['danger'], 
                     'reserved': '#8b5cf6', 'cleaning': '#6b7280'}
            color = colors.get(status, COLORS['text_secondary'])
            
            def make_click_handler(tid, tnum, stat):
                def click_handler():
                    if stat == 'available':
                        select_table(tid, tnum)
                    else:
                        messagebox.showwarning("Table Occupied", f"Table {tnum} is currently {stat}. Please wait or select another table.")
                return click_handler
            
            btn = tk.Button(table_frame, text=f"{table_num}", bg=color, fg='#000',
                          width=4, font=('Arial', 10, 'bold'), relief=tk.RAISED,
                          command=make_click_handler(table_id, table_num, status))
            btn.pack(side=tk.LEFT, padx=3, pady=3)
            table_buttons[table_id] = btn
        
        def select_table(table_id, table_num):
            selected_table.set(table_id)
            for btn in table_buttons.values():
                btn.config(relief=tk.RAISED)
            table_buttons[table_id].config(relief=tk.SUNKEN)
        
        def refresh_table_buttons():
            """Refresh table button colors based on table status"""
            cursor.execute("SELECT id, status FROM tables")
            all_tables = cursor.fetchall()
            
            for table_id, status in all_tables:
                if table_id in table_buttons:
                    table_status[table_id] = status
                    colors = {'available': COLORS['success'], 'occupied': COLORS['danger'], 
                             'reserved': '#8b5cf6', 'cleaning': '#6b7280'}
                    color = colors.get(status, COLORS['text_secondary'])
                    table_buttons[table_id].config(bg=color)
                    
                    # Update click handler based on new status
                    def make_click_handler(tid, tnum, stat):
                        def click_handler():
                            if stat == 'available':
                                select_table(tid, tnum)
                            else:
                                messagebox.showwarning("Table Occupied", f"Table {tnum} is currently {stat}. Please wait or select another table.")
                        return click_handler
                    
                    table_buttons[table_id].config(command=make_click_handler(table_id, 
                        table_buttons[table_id].cget('text'), status))
        
        cat_frame = tk.Frame(left, bg=COLORS['bg_dark'])
        cat_frame.pack(fill=tk.X, pady=(0, 10))
        
        cursor.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY sort_order")
        categories = [('all', 'All')] + cursor.fetchall()
        
        for cat_id, cat_name in categories:
            rb = tk.Radiobutton(cat_frame, text=cat_name, variable=selected_category, value=str(cat_id),
                                bg=COLORS['bg_dark'], fg=COLORS['text'], selectcolor=COLORS['accent'],
                                font=('Arial', 9), command=lambda: refresh_products())
            rb.pack(side=tk.LEFT, padx=8)
        
        # Scrollable products
        products_canvas = tk.Canvas(left, bg=COLORS['bg_dark'], highlightthickness=0)
        products_scroll_y = tk.Scrollbar(left, orient=tk.VERTICAL, command=products_canvas.yview)
        products_scroll_x = tk.Scrollbar(left, orient=tk.HORIZONTAL, command=products_canvas.xview)
        
        products_canvas.configure(yscrollcommand=products_scroll_y.set, xscrollcommand=products_scroll_x.set)
        
        products_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        products_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        products_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        products_frame = tk.Frame(products_canvas, bg=COLORS['bg_dark'])
        products_canvas.create_window((0, 0), window=products_frame, anchor=tk.NW)
        
        def refresh_products():
            for widget in products_frame.winfo_children():
                widget.destroy()
            
            cat_val = selected_category.get()
            search_val = search_query.get().lower()
            
            if cat_val == 'all':
                cursor.execute("SELECT id, name, price, emoji FROM products WHERE is_available = 1 ORDER BY name")
            else:
                cursor.execute("SELECT id, name, price, emoji FROM products WHERE category_id = ? AND is_available = 1 ORDER BY name", (int(cat_val),))
            
            products = cursor.fetchall()
            products = [p for p in products if search_val in p[1].lower()] if search_val else products
            
            row = col = 0
            for prod_id, prod_name, price, emoji in products:
                if col >= 5:
                    col = 0
                    row += 1
                
                prod_frame = tk.Frame(products_frame, bg=COLORS['bg_medium'], relief=tk.RAISED, borderwidth=1)
                prod_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                
                tk.Label(prod_frame, text=emoji, font=('Arial', 28), bg=COLORS['bg_medium']).pack(pady=(10, 5))
                tk.Label(prod_frame, text=prod_name, font=('Arial', 9, 'bold'), bg=COLORS['bg_medium'], 
                        fg=COLORS['text'], wraplength=90).pack(pady=2)
                tk.Label(prod_frame, text=f"{currency}{price:.2f}", font=('Arial', 11, 'bold'),
                        bg=COLORS['bg_medium'], fg=COLORS['accent']).pack(pady=2)
                
                add_btn = tk.Button(prod_frame, text="ADD", bg=COLORS['accent'], fg='#000',
                                  font=('Arial', 9, 'bold'), relief=tk.FLAT,
                                  command=lambda p=prod_id, n=prod_name, e=emoji, pr=price: add_to_cart(p, n, e, pr))
                add_btn.pack(pady=5)
                
                col += 1
            
            products_frame.update_idletasks()
            products_canvas.configure(scrollregion=products_canvas.bbox('all'))
        
        right = tk.Frame(content, bg=COLORS['bg_medium'], width=350)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)
        
        cart_header = tk.Frame(right, bg=COLORS['bg_lighter'])
        cart_header.pack(fill=tk.X)
        
        tk.Label(cart_header, text="🛒 Current Order", font=('Arial', 14, 'bold'),
                bg=COLORS['bg_lighter'], fg=COLORS['text']).pack(pady=10)
        
        cart_scroll = tk.Scrollbar(right)
        cart_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        cart_list = tk.Listbox(right, yscrollcommand=cart_scroll.set, bg=COLORS['bg_medium'],
                              fg=COLORS['text'], borderwidth=0, font=('Arial', 10))
        cart_list.pack(fill=tk.BOTH, expand=True, padx=5)
        cart_scroll.config(command=cart_list.yview)
        
        total_frame = tk.Frame(right, bg=COLORS['bg_lighter'])
        total_frame.pack(fill=tk.X, pady=10)
        
        cart_total_label = tk.Label(total_frame, text=f"Total: {currency}0.00", font=('Arial', 16, 'bold'),
                                    bg=COLORS['bg_lighter'], fg=COLORS['accent'])
        cart_total_label.pack(pady=10)
        
        btn_frame = tk.Frame(right, bg=COLORS['bg_medium'])
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def add_to_cart(prod_id, prod_name, emoji, price):
            for item in cart:
                if item['id'] == prod_id:
                    item['quantity'] += 1
                    item['subtotal'] = item['quantity'] * price
                    break
            else:
                cart.append({'id': prod_id, 'name': prod_name, 'emoji': emoji,
                           'price': price, 'quantity': 1, 'subtotal': price})
            update_cart_display()
        
        def update_cart_display():
            cart_list.delete(0, tk.END)
            total = 0
            for i, item in enumerate(cart):
                total += item['subtotal']
                cart_list.insert(tk.END, f"{item['emoji']} {item['name']} x{item['quantity']} = {currency}{item['subtotal']:.2f}")
            
            tax = total * 0.10
            final_total = total + tax
            cart_total_label.config(text=f"Total: {currency}{final_total:.2f}")
        
        def process_payment():
            """Process payment - keeps cart for adding more orders"""
            if not cart:
                messagebox.showwarning("Warning", "Cart is empty")
                return
            
            if order_type.get() == 'dine_in' and not selected_table.get():
                messagebox.showwarning("Warning", "Please select a table")
                return
            
            try:
                cursor.execute("SELECT MAX(id) FROM orders")
                max_id = cursor.fetchone()[0] or 0
                order_num = f"ORD-{max_id + 1:04d}"
                
                subtotal = sum(item['subtotal'] for item in cart)
                tax = subtotal * 0.10
                total = subtotal + tax
                
                cursor.execute("""INSERT INTO orders (order_number, order_type, table_id, server_id,
                                 subtotal, tax_amount, total, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                             (order_num, order_type.get(), selected_table.get() if selected_table.get() else None,
                              self.current_user['id'], subtotal, tax, total, 'completed'))
                order_id = cursor.lastrowid
                
                for item in cart:
                    cursor.execute("""INSERT INTO order_items (order_id, product_id, server_id, quantity, unit_price, subtotal, status)
                                    VALUES (?, ?, ?, ?, ?, ?, 'served')""",
                                 (order_id, item['id'], self.current_user['id'], item['quantity'],
                                  item['price'], item['subtotal']))
                
                cursor.execute("SELECT MAX(id) FROM payments")
                max_pay_id = cursor.fetchone()[0] or 0
                pay_num = f"PAY-{max_pay_id + 1:04d}"
                
                cursor.execute("""INSERT INTO payments (payment_number, order_id, amount, method, status)
                                VALUES (?, ?, ?, ?, 'paid')""", (pay_num, order_id, total, 'cash'))
                
                if selected_table.get():
                    cursor.execute("UPDATE tables SET status = 'available' WHERE id = ?", (selected_table.get(),))
                
                conn.commit()
                
                # Keep cart displayed - don't clear it (user can add more)
                refresh_products()
                refresh_table_buttons()
                messagebox.showinfo("Success", f"Payment of {currency}{total:.2f} processed!")
            except Exception as e:
                messagebox.showerror("Error", f"Payment failed: {str(e)}")
        
        def send_to_kitchen():
            """Send to kitchen - cart stays for adding more"""
            if not cart:
                messagebox.showwarning("Warning", "Cart is empty")
                return
            
            if order_type.get() == 'dine_in' and not selected_table.get():
                messagebox.showwarning("Warning", "Please select a table")
                return
            
            try:
                cursor.execute("SELECT MAX(id) FROM orders")
                max_id = cursor.fetchone()[0] or 0
                order_num = f"ORD-{max_id + 1:04d}"
                
                subtotal = sum(item['subtotal'] for item in cart)
                tax = subtotal * 0.10
                total = subtotal + tax
                
                cursor.execute("""INSERT INTO orders (order_number, order_type, table_id, server_id,
                                 subtotal, tax_amount, total, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                             (order_num, order_type.get(), selected_table.get() if selected_table.get() else None,
                              self.current_user['id'], subtotal, tax, total, 'pending'))
                order_id = cursor.lastrowid
                
                for item in cart:
                    cursor.execute("""INSERT INTO order_items (order_id, product_id, server_id, quantity, unit_price, subtotal)
                                    VALUES (?, ?, ?, ?, ?, ?)""",
                                 (order_id, item['id'], self.current_user['id'], item['quantity'],
                                  item['price'], item['subtotal']))
                
                conn.commit()
                
                if selected_table.get():
                    cursor.execute("UPDATE tables SET status = 'preparing' WHERE id = ?", (selected_table.get(),))
                    conn.commit()
                
                cart.clear()
                update_cart_display()
                refresh_products()
                refresh_table_buttons()
                self.trigger_refresh()  # Refresh kitchen
                messagebox.showinfo("Success", f"Order {order_num} sent to kitchen!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send order: {str(e)}")
        
        def cancel_order():
            if not cart:
                messagebox.showwarning("Warning", "Cart is empty")
                return
            cart.clear()
            update_cart_display()
        
        # Payment first button
        pay_btn = self.create_styled_button(btn_frame, "Process Payment", process_payment,
                                             bg=COLORS['success'], fg='#000')
        pay_btn.pack(fill=tk.X, pady=3)
        
        # Send to kitchen button
        send_btn = self.create_styled_button(btn_frame, "Send to Kitchen", send_to_kitchen,
                                             bg=COLORS['warning'], fg='#000')
        send_btn.pack(fill=tk.X, pady=3)
        
        cancel_btn = self.create_styled_button(btn_frame, "Cancel Order", cancel_order,
                                              bg=COLORS['danger'], fg='#fff')
        cancel_btn.pack(fill=tk.X, pady=3)
        
        clear_btn = self.create_styled_button(btn_frame, "Clear Cart", lambda: [cart.clear(), update_cart_display()],
                                              bg='#6b7280', fg='#fff')
        clear_btn.pack(fill=tk.X, pady=3)
        
        refresh_products()
        refresh_table_buttons()
        
        # Auto-refresh table status every 2 seconds
        def auto_refresh_tables():
            try:
                if table_frame.winfo_exists():
                    refresh_table_buttons()
            except:
                pass
            self.after(2000, auto_refresh_tables)
        
        auto_refresh_tables()
        
        # Register for refresh callbacks
        self.register_refresh(refresh_table_buttons)
    
    def show_kitchen_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Kitchen Display", "Manage order preparation")
        
        filter_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        filter_frame.pack(fill=tk.X, pady=10)
        
        status_filter = tk.StringVar(value='all')
        
        for status in [('all', 'All'), ('pending', 'Pending'), ('preparing', 'Preparing'), ('ready', 'Ready')]:
            rb = tk.Radiobutton(filter_frame, text=status[1], variable=status_filter, value=status[0],
                               bg=COLORS['bg_dark'], fg=COLORS['text'], selectcolor=COLORS['accent'],
                               font=('Arial', 10), command=lambda: refresh_orders())
            rb.pack(side=tk.LEFT, padx=10)
        
        refresh_btn = tk.Button(filter_frame, text="🔄 Refresh", command=lambda: refresh_orders(),
                              bg=COLORS['accent'], fg='#000', relief=tk.FLAT, font=('Arial', 10, 'bold'))
        refresh_btn.pack(side=tk.LEFT, padx=20)
        
        # Scrollable orders
        orders_canvas = tk.Canvas(main, bg=COLORS['bg_dark'], highlightthickness=0)
        orders_scroll_y = tk.Scrollbar(main, orient=tk.VERTICAL, command=orders_canvas.yview)
        
        orders_canvas.configure(yscrollcommand=orders_scroll_y.set)
        
        orders_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        orders_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        orders_frame = tk.Frame(orders_canvas, bg=COLORS['bg_dark'])
        orders_canvas.create_window((0, 0), window=orders_frame, anchor=tk.NW)
        
        conn, cursor = get_db_connection()
        
        def refresh_orders():
            for widget in orders_frame.winfo_children():
                widget.destroy()
            
            filter_val = status_filter.get()
            
            # Get orders based on filter
            if filter_val == 'all':
                cursor.execute("""SELECT o.id, o.order_number, o.order_type, t.table_number, o.created_at, o.status
                                 FROM orders o LEFT JOIN tables t ON o.table_id = t.id
                                 WHERE o.status IN ('pending', 'preparing', 'ready') ORDER BY o.created_at""")
            else:
                cursor.execute("""SELECT o.id, o.order_number, o.order_type, t.table_number, o.created_at, o.status
                                 FROM orders o LEFT JOIN tables t ON o.table_id = t.id
                                 WHERE o.status = ? ORDER BY o.created_at""", (filter_val,))
            
            orders = cursor.fetchall()
            
            if not orders:
                tk.Label(orders_frame, text="No orders in this category", font=('Arial', 14),
                        bg=COLORS['bg_dark'], fg=COLORS['text_secondary']).pack(pady=50)
                return
            
            for order_id, order_num, order_type, table_num, created_at, status in orders:
                cursor.execute("""SELECT oi.id, p.name, oi.quantity, oi.status, oi.notes
                                 FROM order_items oi JOIN products p ON oi.product_id = p.id
                                 WHERE oi.order_id = ?""", (order_id,))
                items = cursor.fetchall()
                
                if not items:
                    continue
                
                status_colors = {'pending': COLORS['warning'], 'preparing': '#3b82f6', 'ready': COLORS['success']}
                
                card = tk.LabelFrame(orders_frame, text=f"{order_num} - Table {table_num or 'Takeaway'}",
                                   font=('Arial', 12, 'bold'), bg=COLORS['bg_medium'], fg=COLORS['text'],
                                   padx=10, pady=10)
                card.pack(fill=tk.X, padx=5, pady=5)
                
                tk.Label(card, text=f"Status: {status.upper()}",
                        bg=COLORS['bg_medium'], fg=status_colors.get(status, COLORS['text_secondary']),
                        font=('Arial', 10, 'bold')).pack(anchor=tk.W)
                
                def cancel_order(oid=order_id):
                    if messagebox.askyesno("Cancel Order", "Are you sure you want to cancel this order?"):
                        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (oid,))
                        conn.commit()
                        refresh_orders()
                        self.trigger_refresh()
                
                tk.Button(card, text="❌ Cancel Order", bg=COLORS['danger'], fg='#fff',
                         font=('Arial', 8), relief=tk.FLAT, command=cancel_order).pack(anchor=tk.E, pady=5)
                
                for item_id, item_name, qty, item_status, notes in items:
                    item_card = tk.Frame(card, bg=COLORS['bg_lighter'])
                    item_card.pack(fill=tk.X, pady=3)
                    
                    icons = {'pending': '⏳', 'preparing': '🔥', 'ready': '✅', 'served': '✓', 'cancelled': '❌'}
                    tk.Label(item_card, text=f"{qty}x {item_name} {icons.get(item_status, '')}",
                            bg=COLORS['bg_lighter'], fg=COLORS['text'], font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
                    
                    if notes:
                        tk.Label(item_card, text=f"📝 {notes}", bg=COLORS['bg_lighter'],
                                fg=COLORS['warning'], font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
                    
                    btn_frame = tk.Frame(item_card, bg=COLORS['bg_lighter'])
                    btn_frame.pack(side=tk.RIGHT, padx=10)
                    
                    # FIXED: Proper callback with default arguments
                    if item_status == 'pending':
                        btn = tk.Button(btn_frame, text="Start", bg='#3b82f6', fg='#fff', font=('Arial', 8), relief=tk.FLAT)
                        btn.config(command=lambda iid=item_id, oid=order_id: change_status_item(iid, oid, 'preparing'))
                        btn.pack(side=tk.LEFT, padx=2)
                    elif item_status == 'preparing':
                        btn = tk.Button(btn_frame, text="Ready", bg=COLORS['success'], fg='#fff', font=('Arial', 8), relief=tk.FLAT)
                        btn.config(command=lambda iid=item_id, oid=order_id: change_status_item(iid, oid, 'ready'))
                        btn.pack(side=tk.LEFT, padx=2)
                    elif item_status == 'ready':
                        btn = tk.Button(btn_frame, text="Served", bg=COLORS['accent'], fg='#000', font=('Arial', 8), relief=tk.FLAT)
                        btn.config(command=lambda iid=item_id, oid=order_id: change_status_item(iid, oid, 'served'))
                        btn.pack(side=tk.LEFT, padx=2)
            
            orders_frame.update_idletasks()
            orders_canvas.configure(scrollregion=orders_canvas.bbox('all'))
        
        def change_status_item(item_id, order_id, new_status):
            try:
                conn2, cursor2 = get_db_connection()
                cursor2.execute("UPDATE order_items SET status = ? WHERE id = ?", (new_status, item_id))
                
                # Check if all items are ready/served
                cursor2.execute("SELECT status FROM order_items WHERE order_id = ?", (order_id,))
                all_statuses = [s[0] for s in cursor2.fetchall()]
                
                order_status = 'pending'
                if all(s in ['ready', 'served'] for s in all_statuses):
                    order_status = 'ready'
                elif any(s == 'preparing' for s in all_statuses):
                    order_status = 'preparing'
                
                cursor2.execute("UPDATE orders SET status = ? WHERE id = ?", (order_status, order_id))
                
                # Update table status - when served, table becomes occupied (customer is eating)
                cursor2.execute("SELECT table_id FROM orders WHERE id = ?", (order_id,))
                table_result = cursor2.fetchone()
                if table_result and table_result[0]:
                    if new_status == 'ready':
                        cursor2.execute("UPDATE tables SET status = 'occupied' WHERE id = ?", (table_result[0],))
                    elif new_status == 'served':
                        cursor2.execute("UPDATE tables SET status = 'occupied' WHERE id = ?", (table_result[0],))
                
                conn2.commit()
                refresh_orders()
                self.trigger_refresh()  # Refresh POS tables
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update status: {str(e)}")
        
        def auto_refresh():
            try:
                if orders_frame.winfo_exists():
                    refresh_orders()
            except:
                pass
            self.after(2000, auto_refresh)
        
        refresh_orders()
        auto_refresh()
        
        self.register_refresh(refresh_orders)
    
    def show_orders_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Orders", "View and manage all orders")
        
        tree_frame = tk.Frame(main, bg=COLORS['bg_medium'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        conn, cursor = get_db_connection()
        currency = get_currency()
        
        columns = ('Order #', 'Type', 'Table', 'Server', 'Status', 'Total', 'Date')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        cursor.execute("""SELECT o.order_number, o.order_type, t.table_number, u.full_name, o.status, o.total, o.created_at
                         FROM orders o LEFT JOIN tables t ON o.table_id = t.id
                         LEFT JOIN users u ON o.server_id = u.id ORDER BY o.created_at DESC""")
        
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=(row[0], row[1], row[2] or 'N/A', row[3] or 'N/A', row[4], f"{currency}{row[5]:.2f}", row[6]))
    
    def show_payments_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Payments", "Payment history")
        
        tree_frame = tk.Frame(main, bg=COLORS['bg_medium'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        conn, cursor = get_db_connection()
        currency = get_currency()
        
        columns = ('Payment #', 'Order #', 'Amount', 'Method', 'Status', 'Date')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        cursor.execute("SELECT payment_number, order_id, amount, method, status, created_at FROM payments ORDER BY created_at DESC")
        
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=(row[0], row[1], f"{currency}{row[2]:.2f}", row[3], row[4], row[5]))
    
    def show_products_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Products", "Manage menu items and categories")
        
        btn_bar = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.create_styled_button(btn_bar, "+ Add Product", lambda: product_dialog(None),
                                 bg=COLORS['success']).pack(side=tk.LEFT, padx=5)
        
        self.create_styled_button(btn_bar, "+ Add Category", lambda: category_dialog(None),
                                 bg='#8b5cf6').pack(side=tk.LEFT, padx=5)
        
        conn, cursor = get_db_connection()
        currency = get_currency()
        
        tree_frame = tk.Frame(main, bg=COLORS['bg_medium'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Name', 'Category', 'Price', 'Available')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        def load_products():
            for item in tree.get_children():
                tree.delete(item)
            
            cursor.execute("""SELECT p.id, p.name, c.name, p.price, p.is_available
                             FROM products p LEFT JOIN categories c ON p.category_id = c.id""")
            
            for row in cursor.fetchall():
                tree.insert('', tk.END, values=(row[0], row[1], row[2] or 'N/A', f"{currency}{row[3]:.2f}", 'Yes' if row[4] else 'No'))
        
        load_products()
        
        def on_double_click(event):
            item = tree.selection()
            if item:
                values = tree.item(item)['values']
                product_dialog(values[0])
        
        tree.bind('<Double-Button-1>', on_double_click)
        
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="Edit", command=lambda: product_dialog(tree.selection()[0]) if tree.selection() else None)
        menu.add_command(label="Delete", command=lambda: delete_product(tree.selection()[0]) if tree.selection() else None)
        
        def show_menu(event):
            menu.post(event.x_root, event.y_root)
        
        tree.bind('<Button-3>', show_menu)
        
        def product_dialog(product_id=None):
            dialog = tk.Toplevel(self)
            dialog.title("Edit Product" if product_id else "Add Product")
            dialog.geometry("450x520")
            dialog.configure(bg=COLORS['bg_medium'])
            dialog.transient(self)
            dialog.grab_set()
            
            existing = None
            if product_id:
                cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
                existing = cursor.fetchone()
            
            tk.Label(dialog, text="Product Name *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            name_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            name_entry.pack(fill=tk.X, padx=20)
            if existing:
                name_entry.insert(0, existing[1])
            
            tk.Label(dialog, text="Description", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            desc_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            desc_entry.pack(fill=tk.X, padx=20)
            if existing:
                desc_entry.insert(0, existing[2] or '')
            
            tk.Label(dialog, text="Price *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            price_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            price_entry.pack(fill=tk.X, padx=20)
            if existing:
                price_entry.insert(0, existing[3])
            
            tk.Label(dialog, text="Category *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            
            cat_var = tk.StringVar()
            cat_combo = ttk.Combobox(dialog, textvariable=cat_var, state='readonly')
            cursor.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name")
            cats = cursor.fetchall()
            cat_combo['values'] = [c[1] for c in cats]
            cat_combo.pack(fill=tk.X, padx=20)
            if existing and existing[4]:
                for c in cats:
                    if c[0] == existing[4]:
                        cat_combo.set(c[1])
                        break
            
            tk.Label(dialog, text="Emoji", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            emoji_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            emoji_entry.pack(fill=tk.X, padx=20)
            if existing:
                emoji_entry.insert(0, existing[5] or '🍽️')
            else:
                emoji_entry.insert(0, '🍽️')
            
            avail_var = tk.IntVar(value=1)
            if existing and not existing[9]:
                avail_var.set(0)
            tk.Checkbutton(dialog, text="Product is available for ordering", variable=avail_var,
                          bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent']).pack()
            
            def save():
                name = name_entry.get()
                price = float(price_entry.get() or 0)
                cat_name = cat_var.get()
                emoji = emoji_entry.get() or '🍽️'
                desc = desc_entry.get()
                available = avail_var.get()
                
                if not name or price <= 0:
                    messagebox.showerror("Error", "Name and price are required")
                    return
                
                if not cat_name:
                    messagebox.showerror("Error", "Please select a category")
                    return
                
                cat_id = None
                for c in cats:
                    if c[1] == cat_name:
                        cat_id = c[0]
                        break
                
                if product_id:
                    cursor.execute("""UPDATE products SET name=?, description=?, price=?, category_id=?,
                                    emoji=?, is_available=? WHERE id=?""",
                                 (name, desc, price, cat_id, emoji, available, product_id))
                else:
                    cursor.execute("""INSERT INTO products (name, description, price, category_id, emoji, is_available)
                                    VALUES (?, ?, ?, ?, ?, ?)""",
                                 (name, desc, price, cat_id, emoji, available))
                
                conn.commit()
                dialog.destroy()
                load_products()
            
            tk.Button(dialog, text="Save", command=save, bg=COLORS['accent'], fg='#000',
                      font=('Arial', 11, 'bold'), relief=tk.FLAT).pack(pady=20)
        
        def category_dialog(category_id=None):
            dialog = tk.Toplevel(self)
            dialog.title("Edit Category" if category_id else "Add Category")
            dialog.geometry("400x400")
            dialog.configure(bg=COLORS['bg_medium'])
            dialog.transient(self)
            dialog.grab_set()
            
            existing = None
            if category_id:
                cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
                existing = cursor.fetchone()
            
            tk.Label(dialog, text="Category Name *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            name_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            name_entry.pack(fill=tk.X, padx=20)
            if existing:
                name_entry.insert(0, existing[1])
            
            tk.Label(dialog, text="Description", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            desc_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            desc_entry.pack(fill=tk.X, padx=20)
            if existing:
                desc_entry.insert(0, existing[2] or '')
            
            tk.Label(dialog, text="Emoji/Icon", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            icon_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            icon_entry.pack(fill=tk.X, padx=20)
            if existing:
                icon_entry.insert(0, existing[3] or '🍽️')
            else:
                icon_entry.insert(0, '🍽️')
            
            active_var = tk.IntVar(value=1)
            if existing and not existing[5]:
                active_var.set(0)
            tk.Checkbutton(dialog, text="Category is active", variable=active_var,
                          bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent']).pack()
            
            def save():
                name = name_entry.get()
                if not name:
                    messagebox.showerror("Error", "Category name is required")
                    return
                
                desc = desc_entry.get()
                icon = icon_entry.get() or '🍽️'
                active = active_var.get()
                
                if category_id:
                    cursor.execute("""UPDATE categories SET name=?, description=?, icon=?, is_active=? WHERE id=?""",
                                 (name, desc, icon, active, category_id))
                else:
                    cursor.execute("SELECT MAX(sort_order) FROM categories")
                    max_order = (cursor.fetchone()[0] or 0) + 1
                    cursor.execute("""INSERT INTO categories (name, description, icon, sort_order, is_active)
                                    VALUES (?, ?, ?, ?, ?)""",
                                 (name, desc, icon, max_order, active))
                
                conn.commit()
                dialog.destroy()
                messagebox.showinfo("Success", "Category saved!")
            
            tk.Button(dialog, text="Save", command=save, bg=COLORS['accent'], fg='#000',
                      font=('Arial', 11, 'bold'), relief=tk.FLAT).pack(pady=20)
        
        def delete_product(product_id):
            if messagebox.askyesno("Confirm", "Delete this product?"):
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                load_products()
    
    def show_tables_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Tables", "Manage restaurant tables")
        
        btn_bar = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.create_styled_button(btn_bar, "+ Add Table", lambda: table_dialog(None),
                                 bg=COLORS['success']).pack(side=tk.LEFT, padx=5)
        
        # Scrollable tables
        tables_canvas = tk.Canvas(main, bg=COLORS['bg_dark'], highlightthickness=0)
        tables_scroll_y = tk.Scrollbar(main, orient=tk.VERTICAL, command=tables_canvas.yview)
        
        tables_canvas.configure(yscrollcommand=tables_scroll_y.set)
        
        tables_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tables_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tables_grid = tk.Frame(tables_canvas, bg=COLORS['bg_dark'])
        tables_canvas.create_window((0, 0), window=tables_grid, anchor=tk.NW)
        
        conn, cursor = get_db_connection()
        cursor.execute("SELECT id, table_number, capacity, status, location FROM tables ORDER BY table_number")
        tables = cursor.fetchall()
        
        colors = {'available': COLORS['success'], 'occupied': COLORS['warning'], 
                  'reserved': '#8b5cf6', 'cleaning': '#6b7280', 'preparing': COLORS['warning'], 'ready': COLORS['danger'], 'served': COLORS['success']}
        
        for i, (table_id, table_num, capacity, status, location) in enumerate(tables):
            card = tk.Frame(tables_grid, bg=colors.get(status, '#888'), relief=tk.RAISED, borderwidth=2)
            card.grid(row=i//4, column=i%4, padx=10, pady=10, sticky='nsew')
            
            tk.Label(card, text=f"Table {table_num}", font=('Arial', 14, 'bold'),
                    bg=colors.get(status, '#888'), fg='#000').pack(pady=10)
            tk.Label(card, text=f"Capacity: {capacity}", bg=colors.get(status, '#888'), fg='#000').pack()
            tk.Label(card, text=f"Status: {status.title()}", bg=colors.get(status, '#888'), fg='#000').pack()
            tk.Label(card, text=f"Location: {location}", bg=colors.get(status, '#888'), fg='#000').pack()
            
            btn_frame = tk.Frame(card, bg=colors.get(status, '#888'))
            btn_frame.pack(pady=5)
            
            tk.Button(btn_frame, text="Edit", bg='#3b82f6', fg='#fff', font=('Arial', 8),
                     relief=tk.FLAT, command=lambda tid=table_id: table_dialog(tid)).pack(side=tk.LEFT, padx=2)
            
            for st in ['available', 'occupied', 'reserved', 'cleaning']:
                tk.Button(btn_frame, text=st[:3].upper(), bg=colors.get(st), fg='#000', font=('Arial', 8),
                         width=4, relief=tk.FLAT,
                         command=lambda tid=table_id, s=st: change_status(tid, s)).pack(side=tk.LEFT, padx=2)
        
        def change_status(table_id, new_status):
            cursor.execute("UPDATE tables SET status = ? WHERE id = ?", (new_status, table_id))
            conn.commit()
            self.show_page('tables')
        
        def table_dialog(table_id=None):
            dialog = tk.Toplevel(self)
            dialog.title("Edit Table" if table_id else "Add Table")
            dialog.geometry("350x350")
            dialog.configure(bg=COLORS['bg_medium'])
            dialog.transient(self)
            dialog.grab_set()
            
            existing = None
            if table_id:
                cursor.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
                existing = cursor.fetchone()
            
            tk.Label(dialog, text="Table Number *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            num_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            num_entry.pack(fill=tk.X, padx=20)
            if existing:
                num_entry.insert(0, existing[1])
            
            tk.Label(dialog, text="Capacity *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            cap_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            cap_entry.pack(fill=tk.X, padx=20)
            if existing:
                cap_entry.insert(0, existing[2])
            else:
                cap_entry.insert(0, '4')
            
            tk.Label(dialog, text="Location", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            loc_var = tk.StringVar(value=existing[4] if existing else 'Indoor')
            for loc in ['Indoor', 'Outdoor', 'VIP', 'Bar']:
                tk.Radiobutton(dialog, text=loc, variable=loc_var, value=loc,
                             bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent']).pack()
            
            status_var = tk.StringVar(value=existing[3] if existing else 'available')
            tk.Label(dialog, text="Status", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            for st in ['available', 'occupied', 'reserved', 'cleaning']:
                tk.Radiobutton(dialog, text=st.title(), variable=status_var, value=st,
                             bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent']).pack()
            
            def save():
                table_num = num_entry.get()
                capacity = int(cap_entry.get() or 4)
                location = loc_var.get()
                status = status_var.get()
                
                if not table_num:
                    messagebox.showerror("Error", "Table number is required")
                    return
                
                if table_id:
                    cursor.execute("""UPDATE tables SET table_number=?, capacity=?, location=?, status=? WHERE id=?""",
                                 (table_num, capacity, location, status, table_id))
                else:
                    try:
                        cursor.execute("""INSERT INTO tables (table_number, capacity, location, status)
                                        VALUES (?, ?, ?, ?)""",
                                     (table_num, capacity, location, status))
                    except sqlite3.IntegrityError:
                        messagebox.showerror("Error", "Table number already exists")
                        return
                
                conn.commit()
                dialog.destroy()
                self.show_page('tables')
            
            tk.Button(dialog, text="Save", command=save, bg=COLORS['accent'], fg='#000',
                      font=('Arial', 11, 'bold'), relief=tk.FLAT).pack(pady=20)
        
        tables_grid.update_idletasks()
        tables_canvas.configure(scrollregion=tables_canvas.bbox('all'))
    
    def show_staff_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Staff Management", "Manage employees")
        
        btn_bar = tk.Frame(main, bg=COLORS['bg_dark'])
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.create_styled_button(btn_bar, "+ Add Staff", lambda: staff_dialog(None),
                                 bg=COLORS['success']).pack(side=tk.LEFT, padx=5)
        
        conn, cursor = get_db_connection()
        
        tree_frame = tk.Frame(main, bg=COLORS['bg_medium'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Username', 'Full Name', 'Role', 'Email', 'Phone', 'Active')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        def load_staff():
            for item in tree.get_children():
                tree.delete(item)
            
            cursor.execute("SELECT id, username, full_name, role, email, phone, is_active FROM users")
            
            for row in cursor.fetchall():
                tree.insert('', tk.END, values=(row[0], row[1], row[2], row[3], row[4] or 'N/A', row[5] or 'N/A', 'Yes' if row[6] else 'No'))
        
        load_staff()
        
        def on_double_click(event):
            item = tree.selection()
            if item:
                values = tree.item(item)['values']
                staff_dialog(values[0])
        
        tree.bind('<Double-Button-1>', on_double_click)
        
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="Edit", command=lambda: staff_dialog(tree.selection()[0]) if tree.selection() else None)
        menu.add_command(label="Delete", command=lambda: delete_staff(tree.selection()[0]) if tree.selection() else None)
        
        def show_menu(event):
            menu.post(event.x_root, event.y_root)
        
        tree.bind('<Button-3>', show_menu)
        
        def staff_dialog(staff_id=None):
            dialog = tk.Toplevel(self)
            dialog.title("Edit Staff" if staff_id else "Add Staff")
            dialog.geometry("400x520")
            dialog.configure(bg=COLORS['bg_medium'])
            dialog.transient(self)
            dialog.grab_set()
            
            existing = None
            if staff_id:
                cursor.execute("SELECT * FROM users WHERE id = ?", (staff_id,))
                existing = cursor.fetchone()
            
            tk.Label(dialog, text="Username *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            username_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            username_entry.pack(fill=tk.X, padx=20)
            if existing:
                username_entry.insert(0, existing[1])
            
            if not staff_id:
                tk.Label(dialog, text="Password *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
                password_entry = tk.Entry(dialog, show='*', bg=COLORS['bg_lighter'], fg=COLORS['text'])
                password_entry.pack(fill=tk.X, padx=20)
            
            tk.Label(dialog, text="Full Name *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            name_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            name_entry.pack(fill=tk.X, padx=20)
            if existing:
                name_entry.insert(0, existing[3])
            
            tk.Label(dialog, text="Email", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            email_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            email_entry.pack(fill=tk.X, padx=20)
            if existing:
                email_entry.insert(0, existing[5] or '')
            
            tk.Label(dialog, text="Phone", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            phone_entry = tk.Entry(dialog, bg=COLORS['bg_lighter'], fg=COLORS['text'])
            phone_entry.pack(fill=tk.X, padx=20)
            if existing:
                phone_entry.insert(0, existing[6] or '')
            
            tk.Label(dialog, text="Role *", bg=COLORS['bg_medium'], fg=COLORS['text']).pack(pady=5)
            role_var = tk.StringVar(value=existing[4] if existing else 'server')
            role_frame = tk.Frame(dialog, bg=COLORS['bg_medium'])
            role_frame.pack()
            for role in ['admin', 'manager', 'server', 'counter', 'kitchen']:
                rb = tk.Radiobutton(role_frame, text=role.title(), variable=role_var, value=role,
                              bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent'])
                rb.pack(side=tk.LEFT, padx=5)
            
            active_var = tk.IntVar(value=1)
            if existing and not existing[7]:
                active_var.set(0)
            tk.Checkbutton(dialog, text="Account is active", variable=active_var,
                          bg=COLORS['bg_medium'], fg=COLORS['text'], selectcolor=COLORS['accent']).pack()
            
            def save():
                username = username_entry.get()
                full_name = name_entry.get()
                email = email_entry.get()
                phone = phone_entry.get()
                role = role_var.get()
                active = active_var.get()
                
                if not username or not full_name:
                    messagebox.showerror("Error", "Username and full name are required")
                    return
                
                if staff_id:
                    cursor.execute("""UPDATE users SET username=?, full_name=?, role=?, email=?, phone=?, is_active=? WHERE id=?""",
                                 (username, full_name, role, email, phone, active, staff_id))
                else:
                    password = password_entry.get()
                    if not password:
                        messagebox.showerror("Error", "Password is required")
                        return
                    try:
                        cursor.execute("""INSERT INTO users (username, password, full_name, role, email, phone, is_active)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                     (username, hash_password(password), full_name, role, email, phone, active))
                    except sqlite3.IntegrityError:
                        messagebox.showerror("Error", "Username already exists")
                        return
                
                conn.commit()
                dialog.destroy()
                load_staff()
            
            def delete_staff_user():
                if messagebox.askyesno("Confirm", "Delete this staff member?"):
                    cursor.execute("DELETE FROM users WHERE id = ?", (staff_id,))
                    conn.commit()
                    dialog.destroy()
                    load_staff()
            
            tk.Button(dialog, text="Save", command=save, bg=COLORS['accent'], fg='#000',
                      font=('Arial', 11, 'bold'), relief=tk.FLAT).pack(pady=20)
            
            if staff_id:
                tk.Button(dialog, text="Delete Staff", command=delete_staff_user, bg=COLORS['danger'], fg='#fff',
                         relief=tk.FLAT).pack(pady=5)
        
        def delete_staff(staff_id):
            if messagebox.askyesno("Confirm", "Delete this staff member?"):
                cursor.execute("DELETE FROM users WHERE id = ?", (staff_id,))
                conn.commit()
                load_staff()
    
    def show_reports_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        header = self.create_header(main, "Reports", "Business analytics")
        
        # Date filter frame
        filter_frame = tk.Frame(header, bg=COLORS['bg_lighter'])
        filter_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(filter_frame, text="Period:", bg=COLORS['bg_lighter'], fg=COLORS['text']).pack(side=tk.LEFT, padx=5)
        
        period_var = tk.StringVar(value='all')
        period_combo = ttk.Combobox(filter_frame, textvariable=period_var, state='readonly', width=12)
        period_combo['values'] = ['all', 'today', 'yesterday', 'this_week', 'this_month', 'last_30_days']
        period_combo.pack(side=tk.LEFT, padx=5)
        period_combo.bind('<<ComboboxSelected>>', lambda e: load_report())
        
        export_btn = tk.Button(filter_frame, text="📥 Export to Excel", command=self.export_reports_to_excel,
                              bg=COLORS['success'], fg='#000', relief=tk.FLAT, font=('Arial', 10, 'bold'),
                              padx=15, pady=5)
        export_btn.pack(side=tk.LEFT, padx=20)
        
        conn, cursor = get_db_connection()
        currency = get_currency()
        
        summary_frame = tk.Frame(main, bg=COLORS['bg_dark'])
        summary_frame.pack(fill=tk.X, pady=10)
        
        # Stats cards
        stats_frames = {}
        
        def load_report():
            period = period_var.get()
            
            # Calculate date filter
            date_filter = ""
            if period == 'today':
                date_filter = "WHERE date(created_at) = date('now')"
            elif period == 'yesterday':
                date_filter = "WHERE date(created_at) = date('now', '-1 day')"
            elif period == 'this_week':
                date_filter = "WHERE date(created_at) >= date('now', '-7 days')"
            elif period == 'this_month':
                date_filter = "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
            elif period == 'last_30_days':
                date_filter = "WHERE date(created_at) >= date('now', '-30 days')"
            
            # Clear previous stats
            for widget in summary_frame.winfo_children():
                widget.destroy()
            
            # Query with date filter
            if date_filter:
                cursor.execute(f"SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders {date_filter} AND status = 'completed'")
                order_count, total_sales = cursor.fetchone()
                
                cursor.execute(f"SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments {date_filter.replace('created_at', 'created_at').replace('orders', 'payments')} AND status = 'paid'")
                payment_count, total_payments = cursor.fetchone()
            else:
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE status = 'completed'")
                order_count, total_sales = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status = 'paid'")
                payment_count, total_payments = cursor.fetchone()
            
            stats = [
                ("Orders", str(order_count)),
                ("Sales", f"{currency}{total_sales:.2f}"),
                ("Payments", str(payment_count)),
            ]
            
            for label, value in stats:
                card = tk.Frame(summary_frame, bg=COLORS['bg_medium'], relief=tk.RAISED, borderwidth=1)
                card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
                
                tk.Label(card, text=label, bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
                        font=('Arial', 10)).pack(pady=(10, 5))
                tk.Label(card, text=value, bg=COLORS['bg_medium'], fg=COLORS['accent'],
                        font=('Arial', 18, 'bold')).pack(pady=(0, 10))
        
        load_report()
        
        recent_frame = tk.LabelFrame(main, text="Recent Orders", bg=COLORS['bg_dark'], fg=COLORS['text'])
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tree = ttk.Treeview(recent_frame, columns=('Order #', 'Type', 'Total', 'Status', 'Date'), show='headings')
        
        for col in ('Order #', 'Type', 'Total', 'Status', 'Date'):
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        cursor.execute("SELECT order_number, order_type, total, status, created_at FROM orders ORDER BY created_at DESC LIMIT 50")
        
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=(row[0], row[1], f"{currency}{row[2]:.2f}", row[3], row[4]))
    
    def export_reports_to_excel(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"POS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if not file_path:
                return
            
            conn, cursor = get_db_connection()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(['POS System Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE status = 'completed'")
                order_count, total_sales = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status = 'paid'")
                payment_count, total_payments = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users")
                staff_count = cursor.fetchone()[0]
                
                writer.writerow(['SUMMARY'])
                writer.writerow(['Total Orders', order_count])
                writer.writerow(['Total Sales', f'{get_currency()}{total_sales:.2f}'])
                writer.writerow(['Total Payments', payment_count])
                writer.writerow(['Products', product_count])
                writer.writerow(['Staff Members', staff_count])
                writer.writerow([])
                
                writer.writerow(['ORDERS'])
                writer.writerow(['Order #', 'Type', 'Table', 'Server', 'Status', 'Total', 'Date'])
                cursor.execute("""SELECT o.order_number, o.order_type, t.table_number, u.full_name, o.status, o.total, o.created_at
                                 FROM orders o LEFT JOIN tables t ON o.table_id = t.id
                                 LEFT JOIN users u ON o.server_id = u.id ORDER BY o.created_at DESC""")
                for row in cursor.fetchall():
                    writer.writerow([row[0], row[1], row[2] or 'N/A', row[3] or 'N/A', row[4], f'{get_currency()}{row[5]:.2f}', row[6]])
                
                writer.writerow([])
                
                writer.writerow(['PAYMENTS'])
                writer.writerow(['Payment #', 'Order #', 'Amount', 'Method', 'Status', 'Date'])
                cursor.execute("SELECT payment_number, order_id, amount, method, status, created_at FROM payments ORDER BY created_at DESC")
                for row in cursor.fetchall():
                    writer.writerow([row[0], row[1], f'{get_currency()}{row[2]:.2f}', row[3], row[4], row[5]])
                
                writer.writerow([])
                
                writer.writerow(['PRODUCTS'])
                writer.writerow(['ID', 'Name', 'Category', 'Price', 'Available'])
                cursor.execute("""SELECT p.id, p.name, c.name, p.price, p.is_available
                                 FROM products p LEFT JOIN categories c ON p.category_id = c.id""")
                for row in cursor.fetchall():
                    writer.writerow([row[0], row[1], row[2] or 'N/A', f'{get_currency()}{row[3]:.2f}', 'Yes' if row[4] else 'No'])
            
            messagebox.showinfo("Success", f"Report exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def show_settings_page(self):
        main = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.create_header(main, "Settings", "System configuration")
        
        conn, cursor = get_db_connection()
        
        settings_frame = tk.LabelFrame(main, text="System Settings", bg=COLORS['bg_dark'], fg=COLORS['text'])
        settings_frame.pack(fill=tk.X, pady=10)
        
        cursor.execute("SELECT key, value, description FROM settings")
        settings = cursor.fetchall()
        
        for i, (key, value, desc) in enumerate(settings):
            row = tk.Frame(settings_frame, bg=COLORS['bg_dark'])
            row.pack(fill=tk.X, pady=5, padx=10)
            
            tk.Label(row, text=desc or key, bg=COLORS['bg_dark'], fg=COLORS['text'],
                    width=25, anchor=tk.W).pack(side=tk.LEFT)
            
            entry = tk.Entry(row, bg=COLORS['bg_medium'], fg=COLORS['text'])
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Button(row, text="Save", bg=COLORS['accent'], fg='#000', font=('Arial', 8),
                     relief=tk.FLAT, command=lambda k=key, e=entry: save_setting(k, e)).pack(side=tk.LEFT, padx=5)
        
        def save_setting(key, entry):
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (entry.get(), key))
            conn.commit()
            self.refresh_title()
            messagebox.showinfo("Success", f"{key} updated!")

if __name__ == "__main__":
    app = POSApplication()
    app.mainloop()
