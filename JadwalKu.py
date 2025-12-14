import tkinter as tk
from tkcalendar import Calendar
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk 
from datetime import datetime, timedelta
import threading
import csv
import random
import time

class Task:
    def __init__(self, name, time_str, description, category, priority):
        self._name = name
        self._time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        self._description = description
        self._category = category
        self._priority = priority
        self._completed = False
        self._motivational_quote = self._generate_quote()
        self._reminder_shown = False

    def get_name(self): return self._name
    def get_time(self): return self._time
    def get_description(self): return self._description
    def get_category(self): return self._category
    def get_priority(self): return self._priority
    def is_completed(self): return self._completed
    def mark_completed(self): self._completed = True
    def has_reminder_shown(self): return self._reminder_shown
    def mark_reminder_shown(self): self._reminder_shown = True

    def display_info(self):
        return (f"{self._name} ({self._priority}) - {self._time.strftime('%Y-%m-%d %H:%M')} "
                f"- {self._category}: {self._description}\nQuote: {self._motivational_quote}")

    def _generate_quote(self):
        quotes = {
            'Rendah': ["Santai saja, tapi tetap selesaikan!", "Langkah kecil menuju kesuksesan."],
            'Sedang': ["Kerjakan dengan fokus, hasilnya akan bagus!", "Konsistensi adalah kunci."],
            'Tinggi': ["Prioritaskan ini, kamu bisa!", "Jangan tunda, capai mimpi sekarang!"]
        }
        return random.choice(quotes.get(self._priority, ["Tetap semangat!"]))

class DailyTask(Task):
    def __init__(self, name, time_str, description, category, priority, reminder_minutes=10):
        super().__init__(name, time_str, description, category, priority)
        self._reminder_minutes = reminder_minutes

    def get_reminder_time(self):
        return self._time - timedelta(minutes=self._reminder_minutes)

    def display_info(self):
        return super().display_info() + f"\nReminder: {self._reminder_minutes} menit sebelumnya"

class RecurringTask(Task):
    def __init__(self, name, time_str, description, category, priority, recurrence_days):
        super().__init__(name, time_str, description, category, priority)
        self._recurrence_days = recurrence_days

    def display_info(self):
        return super().display_info() + f"\nBerulang: {', '.join(self._recurrence_days)}"

class SchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ JadwalKu ✨")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 600)

        # Warna tema
        self.colors = {
            'Kerja': '#ff6b6b',     # Merah coral
            'Belajar': '#4ecdc4',   # Teal
            'Pribadi': '#95e1d3',   # Mint hijau
            'bg': '#f8f9fa',
            'accent': '#6c5ce7'     # Ungu aksen
        }

        self.tasks = []

        self.create_background()
        self.create_widgets()

        # Thread reminder
        self.reminder_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.reminder_thread.start()

    def create_background(self):
        # Canvas untuk gradient background
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)
        
        # Gradient sederhana (biru-ungu ke putih)
        self.canvas.create_rectangle(0, 0, 1100, 750, fill="#dfe6ff", outline="")
        self.canvas.create_rectangle(0, 0, 1100, 300, fill="#c0d4ff", outline="")
        
        # Judul besar
        self.canvas.create_text(550, 80, text="JadwalKu", font=("Segoe UI", 48, "bold"), fill="#6c5ce7")
        self.canvas.create_text(550, 130, text="Atur tugasmu dengan rapi & semangat!", 
                                font=("Segoe UI", 16), fill="#555")

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('arc')  # Tema modern: arc, equilux, breeze, atau clearlooks

        # Configure custom styles
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#6c5ce7")
        style.configure("Custom.TButton", font=("Segoe UI", 10, "bold"), padding=10)

        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.place(relx=0.02, rely=0.22, relwidth=0.96, relheight=0.76)

        # Left panel - Input
        left_panel = ttk.LabelFrame(main_frame, text="Tambah Tugas Baru", padding="10")
        left_panel.grid(row=0, column=0, padx=(0,20), sticky="nsew")

        fields = [
            ("Nama Tugas:", "name_entry"),
            ("Waktu (YYYY-MM-DD HH:MM):", "time_entry"),
            ("Deskripsi:", "desc_entry"),
        ]

        self.entries = {}
        for i, (label, attr) in enumerate(fields):
            ttk.Label(left_panel, text=label, font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=8)
            entry = ttk.Entry(left_panel, width=40, font=("Segoe UI", 10))
            entry.grid(row=i, column=1, pady=8, sticky="ew")
            self.entries[attr] = entry

        # Combobox
        row = len(fields)
        for label, values, attr in [
            ("Kategori:", ['Kerja', 'Belajar', 'Pribadi'], "category_combo"),
            ("Prioritas:", ['Rendah', 'Sedang', 'Tinggi'], "priority_combo"),
            ("Tipe Tugas:", ['Harian', 'Berulang'], "type_combo")
        ]:
            ttk.Label(left_panel, text=label).grid(row=row, column=0, sticky="w", pady=8)
            combo = ttk.Combobox(left_panel, values=values, width=37, state="readonly")
            combo.grid(row=row, column=1, pady=8, sticky="ew")
            setattr(self, attr, combo)
            row += 1

        # Hari berulang
        ttk.Label(left_panel, text="Hari Berulang (pisah koma):").grid(row=row, column=0, sticky="w", pady=8)
        self.recurrence_entry = ttk.Entry(left_panel, width=40)
        self.recurrence_entry.grid(row=row, column=1, pady=8, sticky="ew")

        # Buttons dengan warna custom
        btn_frame = ttk.Frame(left_panel)
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="➕ Tambah Tugas", command=self.add_task, 
                   style="Custom.TButton").pack(side="left", padx=10)
        ttk.Button(btn_frame, text="✅ Tandai Selesai", command=self.mark_completed).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="💾 Ekspor CSV", command=self.export_to_csv).pack(side="left", padx=10)

        # Treeview dengan stripe dan warna kategori
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, pady=20, sticky="nsew")

        self.task_tree = ttk.Treeview(tree_frame, columns=('Nama', 'Waktu', 'Kategori', 'Prioritas', 'Status'), 
                                     show='headings', height=12)
        self.task_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.task_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # Header
        headers = ['Nama Tugas', 'Waktu', 'Kategori', 'Prioritas', 'Status']
        widths = [300, 150, 120, 100, 100]
        for col, text, w in zip(self.task_tree["columns"], headers, widths):
            self.task_tree.heading(col, text=text)
            self.task_tree.column(col, width=w, anchor="center" if col != 'Nama' else "w")

        # Tag warna
        self.task_tree.tag_configure('Kerja', background='#ffebee', foreground='#d63031')
        self.task_tree.tag_configure('Belajar', background='#e3f2fd', foreground='#0984e3')
        self.task_tree.tag_configure('Pribadi', background='#e8f5e9', foreground='#00b894')

        # Progress bar cantik
        prog_frame = ttk.Frame(main_frame)
        prog_frame.grid(row=2, column=0, pady=15, sticky="ew")
        ttk.Label(prog_frame, text="Progress Penyelesaian:", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.progress_bar = ttk.Progressbar(prog_frame, length=500, mode='determinate', style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(side="left", padx=20, fill="x", expand=True)

        style.configure("Custom.Horizontal.TProgressbar", thickness=20, background=self.colors['accent'])

        # Kalender di kanan
        right_panel = ttk.LabelFrame(main_frame, text="Kalender", padding="15")
        right_panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(20,0))

        self.cal = Calendar(right_panel, selectmode='day', background='white', foreground='black')
        self.cal.pack(pady=10)

        ttk.Button(right_panel, text="Gunakan Tanggal Ini", command=self.set_date_from_cal).pack(pady=10)

        # Grid configuration
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        self.update_task_list()
        self.update_progress()

    def animate_progress(self, target):
        current = self.progress_bar['value']
        if abs(current - target) < 1:
            self.progress_bar['value'] = target
            return
        step = (target - current) / 10
        self.progress_bar['value'] += step
        self.root.after(50, lambda: self.animate_progress(target))

    def add_task(self):
        try:
            name = self.entries['name_entry'].get().strip()
            time_str = self.entries['time_entry'].get().strip()
            desc = self.entries['desc_entry'].get().strip()
            category = self.category_combo.get()
            priority = self.priority_combo.get()
            task_type = self.type_combo.get()

            if not all([name, time_str, desc, category, priority, task_type]):
                raise ValueError("Semua field wajib diisi!")

            datetime.strptime(time_str, "%Y-%m-%d %H:%M")

            if task_type == 'Harian':
                task = DailyTask(name, time_str, desc, category, priority)
            else:
                recurrence = [d.strip() for d in self.recurrence_entry.get().split(',') if d.strip()]
                if not recurrence:
                    raise ValueError("Isi hari berulang untuk tugas Berulang!")
                task = RecurringTask(name, time_str, desc, category, priority, recurrence)

            self.tasks.append(task)
            self.update_task_list()
            
            # Animasi progress
            completed = sum(1 for t in self.tasks if t.is_completed())
            target = (completed / len(self.tasks)) * 100 if self.tasks else 0
            self.animate_progress(target)

            messagebox.showinfo("🎉 Sukses!", f"Tugas '{name}' berhasil ditambahkan!\n\n{task._motivational_quote}")

            # Clear inputs
            for entry in self.entries.values():
                entry.delete(0, tk.END)
            self.recurrence_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def set_date_from_cal(self):
        selected = self.cal.get_date()
        try:
            dt = datetime.strptime(selected, '%m/%d/%y')
        except:
            dt = datetime.strptime(selected, '%d/%m/%y')

        formatted = dt.strftime('%Y-%m-%d')
        current = self.entries['time_entry'].get()
        time_part = " 09:00" if not ' ' in current else " " + current.split(' ')[1]
        
        self.entries['time_entry'].delete(0, tk.END)
        self.entries['time_entry'].insert(0, formatted + time_part)

    def mark_completed(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Pilih dulu!", "Klik salah satu tugas di tabel")
            return
        item = selected[0]
        index = self.task_tree.index(item)
        self.tasks[index].mark_completed()
        self.update_task_list()
        
        completed = sum(1 for t in self.tasks if t.is_completed())
        target = (completed / len(self.tasks)) * 100
        self.animate_progress(target)

    def update_task_list(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for task in sorted(self.tasks, key=lambda t: t.get_time()):
            status = "✅ Selesai" if task.is_completed() else "⏳ Belum"
            tag = task.get_category()
            self.task_tree.insert('', 'end', values=(
                task.get_name(),
                task.get_time().strftime('%Y-%m-%d %H:%M'),
                task.get_category(),
                task.get_priority(),
                status
            ), tags=(tag,))

    def update_progress(self):
        if self.tasks:
            completed = sum(1 for t in self.tasks if t.is_completed())
            target = (completed / len(self.tasks)) * 100
            self.animate_progress(target)

    def check_reminders(self):
        while True:
            now = datetime.now()
            for task in self.tasks[:]:
                if isinstance(task, DailyTask) and not task.is_completed() and not task.has_reminder_shown():
                    if task.get_reminder_time() <= now < task.get_time():
                        self.root.after(0, lambda t=task: (
                            messagebox.showinfo("⏰ Reminder!", 
                                f"Tugas '{t.get_name()}' sebentar lagi!\n\n💪 {t._motivational_quote}"),
                            t.mark_reminder_shown()
                        ))
            time.sleep(30)

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Nama', 'Waktu', 'Deskripsi', 'Kategori', 'Prioritas', 'Status'])
                for task in self.tasks:
                    status = "Selesai" if task.is_completed() else "Belum"
                    writer.writerow([task.get_name(), task.get_time(), task.get_description(),
                                     task.get_category(), task.get_priority(), status])
            messagebox.showinfo("✅ Sukses", "Data tugas berhasil diekspor!")

# === Jalankan Aplikasi ===
if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # Bisa ganti: "equilux" (dark mode), "breeze", "clearlooks"
    app = SchedulerApp(root)
    root.mainloop()                       