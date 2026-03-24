import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", placeholder_color="grey", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg_color = self["fg"] if "fg" in self.config() else "black"
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color

    def _on_focus_in(self, event):
        if self._is_placeholder():
            self.delete(0, "end")
            self["fg"] = self.default_fg_color

    def _on_focus_out(self, event):
        if not self.get():
            self._show_placeholder()

    def _is_placeholder(self):
        return self["fg"] == self.placeholder_color

    def get_value(self):
        if self._is_placeholder():
            return ""
        return self.get()

class DrinkEntry(ttk.Frame):
    DRINK_TYPES = ("Coffee", "Energy Drink")
    COFFEE_TYPES = {
        "Espresso": 75,  # mg per shot
        "Vietnamese Coffee": 33,  # mg per oz
        "Pour-Over": 16,
        "Cold Brew": 12.5,
        "French Press": 15,
        "Regular Coffee": 11.5,
        "Instant Coffee": 9,
        "Decaffeinated Coffee": 0.45
    }
    ENERGY_DRINK_TYPES = {
        "Monster": 160,  # mg per serving
        "5-hour Energy Regular Strength": 200,
        "5-hour Energy Extra Strength": 230,
        "Prime": 200,
        "Coca-Cola": 34
    }

    def __init__(self, parent, day_frame):
        super().__init__(parent)
        self.day_frame = day_frame

        drink_type_label = ttk.Label(self, text="Drink Type:")
        drink_type_label.pack(side=tk.LEFT)
        self.drink_type_combo = ttk.Combobox(self, values=self.DRINK_TYPES, state="readonly")
        self.drink_type_combo.pack(side=tk.LEFT, padx=5)
        self.drink_type_combo.bind("<<ComboboxSelected>>", self.update_drink_options)

        self.drink_option_combo = ttk.Combobox(self, state="readonly")
        self.drink_option_combo.pack(side=tk.LEFT, padx=5)

        self.amount_entry = PlaceholderEntry(self, placeholder="Enter amount")
        self.amount_entry.pack(side=tk.LEFT, padx=5)

    def update_drink_options(self, event=None):
        drink_type = self.drink_type_combo.get()
        if drink_type == "Coffee":
            self.drink_option_combo["values"] = list(self.COFFEE_TYPES.keys())
        elif drink_type == "Energy Drink":
            self.drink_option_combo["values"] = list(self.ENERGY_DRINK_TYPES.keys())
        self.update_placeholder()

    def update_placeholder(self):
        drink_option = self.drink_option_combo.get()

        if drink_option == "Espresso":
            placeholder = "Enter number of shots"
        elif drink_option == ["Monster", "5-hour Energy Regular Strength", "5-hour Energy Extra Strength", "Prime", "Coca-Cola"]:
            placeholder = "Enter number of servings"
        else:
            placeholder = "Enter the volume in mL"
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.placeholder = placeholder
        self.amount_entry._show_placeholder()

    def calculate_caffeine(self):
        drink_type = self.drink_type_combo.get()
        drink_option = self.drink_option_combo.get()
        try:
            amount = float(self.amount_entry.get_value())
        except ValueError:
            return 0

        if drink_type == "Coffee":
            caffeine_per_unit = self.COFFEE_TYPES[drink_option]
            if drink_option == "Espresso":
                return amount * caffeine_per_unit
            else:
                return round((amount * caffeine_per_unit) / 29.5735)
        elif drink_type == "Energy Drink":
            caffeine_per_unit = self.ENERGY_DRINK_TYPES[drink_option]
            return amount * caffeine_per_unit
        return 0

class MultiStepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sleep vs Productivity Questionnaire Form")
        self.geometry("500x400")

        self.age = tk.StringVar()
        self.gender = tk.StringVar(value="Male")
        self.num_days = tk.IntVar(value=1)

        self.person_id = tk.StringVar()
        self.health_data_file = tk.StringVar()
        self.day_data = []
        self.step = 0

        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.frames = {}
        for F in (BasicInfoFrame,):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(BasicInfoFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

    def init_day_data_frames(self):
        for f_class in list(self.frames.keys()):
            if f_class not in (BasicInfoFrame,):
                frm = self.frames.pop(f_class, None)
                if frm is not None:
                    frm.destroy()

        self.day_data = []
        for _ in range(self.num_days.get()):
            self.day_data.append({
                "date": None,
                "caffeine_intake": 0,
                "work_hours": "",
                "productivity": "",
                "mood": "",
                "stress": "",
                "sleep_quality": "",
                "exercise_minutes": "",
                "screen_time_minutes": ""
            })

        for day_index in range(self.num_days.get()):
            frame_class = type(f"DayFrame_{day_index+1}", (DayFrame,), {})
            frame_instance = frame_class(self.container, self, day_index)
            self.frames[frame_class] = frame_instance
            frame_instance.grid(row=0, column=0, sticky="nsew")

        final_class = type("FinalFrame", (FinalFrame,), {})
        final_instance = final_class(self.container, self)
        self.frames[final_class] = final_instance
        final_instance.grid(row=0, column=0, sticky="nsew")

    def go_to_day_frame(self, day_index):
        frame_class = None
        for cls in self.frames:
            if cls.__name__ == f"DayFrame_{day_index+1}":
                frame_class = cls
                break
        if frame_class:
            self.show_frame(frame_class)

    def go_to_final_frame(self):
        for cls in self.frames:
            if cls.__name__ == "FinalFrame":
                self.show_frame(cls)
                break

    def submit_all(self):
        info = {
            "age": self.age.get(),
            "gender": self.gender.get(),
            "person_id": self.person_id.get(),
            "num_days": self.num_days.get(),
            "day_data": self.day_data,
            "health_data_file": self.health_data_file.get()
        }
        print(info)
        messagebox.showinfo("Submitted", "Form data has been submitted to the console.")

class BasicInfoFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Basic Information", font=("TkDefaultFont", 16, "bold"))
        title.pack(pady=10)

        age_label = ttk.Label(self, text="Age:")
        age_label.pack(anchor="w", padx=20)
        age_entry = ttk.Entry(self, textvariable=self.controller.age)
        age_entry.pack(padx=20, pady=5, fill="x")

        gender_label = ttk.Label(self, text="Gender:")
        gender_label.pack(anchor="w", padx=20)
        gender_combo = ttk.Combobox(self, textvariable=self.controller.gender, state="readonly")
        gender_combo["values"] = ("Male", "Female", "Other/Prefer not to say")
        gender_combo.pack(padx=20, pady=5, fill="x")

        person_id_label = ttk.Label(self, text="Person ID:")
        person_id_label.pack(anchor="w", padx=20)
        person_id_entry = ttk.Entry(self, textvariable=self.controller.person_id)
        person_id_entry.pack(padx=20, pady=5, fill="x")

        days_label = ttk.Label(self, text="Number of Days Participating:")
        days_label.pack(anchor="w", padx=20)
        days_spinbox = ttk.Spinbox(
            self,
            from_=1,
            to=365,
            textvariable=self.controller.num_days,
            width=5
        )
        days_spinbox.pack(padx=20, pady=5)

        next_btn = ttk.Button(self, text="Next", command=self.on_next)
        next_btn.pack(pady=20)

    def validate_basic_info(self):
        try:
            age = int(self.controller.age.get())
            if age < 0:
                raise ValueError("Age must be a non-negative integer.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a non-negative integer for age.")
            return False

        try:
            person_id = int(self.controller.person_id.get())
            if not (1000 <= person_id <= 9999):
                raise ValueError("Person ID must be a 4-digit number between 1000 and 9999.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter the four-digit ID we have provided.")
            return False

        return True

    def on_next(self):
        if self.validate_basic_info():
            self.controller.init_day_data_frames()
            self.controller.go_to_day_frame(0)

class DayFrame(ttk.Frame):
    def __init__(self, parent, controller, day_index):
        super().__init__(parent)
        self.controller = controller
        self.day_index = day_index

        title = ttk.Label(self, text=f"Day {day_index+1} of {self.controller.num_days.get()}",
                          font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        date_frame = ttk.Frame(self)
        date_frame.pack(anchor="w", padx=20, pady=5)
        date_label = ttk.Label(date_frame, text="Date: ")
        date_label.pack(side=tk.LEFT)
        self.year_entry = PlaceholderEntry(date_frame, placeholder="YYYY", width=6)
        self.year_entry.pack(side=tk.LEFT, padx=2)
        dash1 = ttk.Label(date_frame, text="-")
        dash1.pack(side=tk.LEFT)
        self.month_entry = PlaceholderEntry(date_frame, placeholder="MM", width=4)
        self.month_entry.pack(side=tk.LEFT, padx=2)
        dash2 = ttk.Label(date_frame, text="-")
        dash2.pack(side=tk.LEFT)
        self.day_entry = PlaceholderEntry(date_frame, placeholder="DD", width=4)
        self.day_entry.pack(side=tk.LEFT, padx=2)

        caffeine_label = ttk.Label(self, text="Caffeine Intake:")
        caffeine_label.pack(anchor="w", padx=20, pady=(10, 0))
        self.caffeine_frame = ttk.Frame(self)
        self.caffeine_frame.pack(fill="x", padx=20)
        self.drink_entries = []

        add_delete_frame = ttk.Frame(self)
        add_delete_frame.pack(anchor="w", padx=20, pady=5)
        add_drink_btn = ttk.Button(add_delete_frame, text="Add Drink", command=self.add_drink)
        add_drink_btn.pack(side=tk.LEFT, padx=5)
        delete_drink_btn = ttk.Button(add_delete_frame, text="Delete Drink", command=self.delete_drink)
        delete_drink_btn.pack(side=tk.LEFT, padx=5)

        sleep_label = ttk.Label(self, text="Sleep Quality (1-10):")
        sleep_label.pack(anchor="w", padx=20)
        self.sleep_entry = ttk.Entry(self)
        self.sleep_entry.pack(padx=20, pady=5, fill="x")

        exercise_label = ttk.Label(self, text="Exercise (mins):")
        exercise_label.pack(anchor="w", padx=20)
        self.exercise_entry = ttk.Entry(self)
        self.exercise_entry.pack(padx=20, pady=5, fill="x")

        screen_label = ttk.Label(self, text="Screen Time Before Bed (mins):")
        screen_label.pack(anchor="w", padx=20)
        self.screen_entry = ttk.Entry(self)
        self.screen_entry.pack(padx=20, pady=5, fill="x")

        wh_label = ttk.Label(self, text="Work Hours (hours):")
        wh_label.pack(anchor="w", padx=20)
        self.wh_entry = ttk.Entry(self)
        self.wh_entry.pack(padx=20, pady=5, fill="x")

        prod_label = ttk.Label(self, text="Productivity Score (1-10):")
        prod_label.pack(anchor="w", padx=20)
        self.prod_entry = ttk.Entry(self)
        self.prod_entry.pack(padx=20, pady=5, fill="x")

        mood_label = ttk.Label(self, text="Mood Score (1-10):")
        mood_label.pack(anchor="w", padx=20)
        self.mood_entry = ttk.Entry(self)
        self.mood_entry.pack(padx=20, pady=5, fill="x")

        stress_label = ttk.Label(self, text="Stress Level (1-10):")
        stress_label.pack(anchor="w", padx=20)
        self.stress_entry = ttk.Entry(self)
        self.stress_entry.pack(padx=20, pady=5, fill="x")

        nav_frame = ttk.Frame(self)
        nav_frame.pack(pady=10)

        if day_index > 0:
            prev_btn = ttk.Button(nav_frame, text="Previous", command=self.on_previous)
            prev_btn.pack(side=tk.LEFT, padx=5)
        if day_index < self.controller.num_days.get() - 1:
            next_btn = ttk.Button(nav_frame, text="Next", command=self.on_next)
            next_btn.pack(side=tk.LEFT, padx=5)
        else:
            finish_btn = ttk.Button(nav_frame, text="Finish", command=self.on_finish)
            finish_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_fields_from_data()

    def add_drink(self):
        drink_entry = DrinkEntry(self.caffeine_frame, self)
        drink_entry.pack(fill="x", pady=2)
        self.drink_entries.append(drink_entry)

    def delete_drink(self):
        if self.drink_entries:
            drink_entry = self.drink_entries.pop()
            drink_entry.destroy()

    def refresh_fields_from_data(self):
        day_info = self.controller.day_data[self.day_index]

        if day_info["date"]:
            date = day_info["date"]
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, str(date.year))
            self.year_entry["fg"] = self.year_entry.default_fg_color

            self.month_entry.delete(0, tk.END)
            self.month_entry.insert(0, str(date.month))
            self.month_entry["fg"] = self.month_entry.default_fg_color

            self.day_entry.delete(0, tk.END)
            self.day_entry.insert(0, str(date.day))
            self.day_entry["fg"] = self.day_entry.default_fg_color
        else:
            self.year_entry.delete(0, tk.END)
            self.year_entry._show_placeholder()

            self.month_entry.delete(0, tk.END)
            self.month_entry._show_placeholder()

            self.day_entry.delete(0, tk.END)
            self.day_entry._show_placeholder()

        self.sleep_entry.delete(0, tk.END)
        self.sleep_entry.insert(0, day_info["sleep_quality"])

        self.exercise_entry.delete(0, tk.END)
        self.exercise_entry.insert(0, day_info["exercise_minutes"])

        self.screen_entry.delete(0, tk.END)
        self.screen_entry.insert(0, day_info["screen_time_minutes"])

        self.wh_entry.delete(0, tk.END)
        self.wh_entry.insert(0, day_info["work_hours"])

        self.prod_entry.delete(0, tk.END)
        self.prod_entry.insert(0, day_info["productivity"])

        self.mood_entry.delete(0, tk.END)
        self.mood_entry.insert(0, day_info["mood"])

        self.stress_entry.delete(0, tk.END)
        self.stress_entry.insert(0, day_info["stress"])

    def save_data_to_controller(self):
        day_info = self.controller.day_data[self.day_index]

        year = self.year_entry.get_value()
        month = self.month_entry.get_value()
        day = self.day_entry.get_value()

        try:
            day_info["date"] = datetime.date(int(year), int(month), int(day))
        except ValueError:
            day_info["date"] = None

        day_info["caffeine_intake"] = self.calculate_total_caffeine()

        day_info["sleep_quality"] = self.sleep_entry.get()
        day_info["exercise_minutes"] = self.exercise_entry.get()
        day_info["screen_time_minutes"] = self.screen_entry.get()
        day_info["work_hours"] = self.wh_entry.get()
        day_info["productivity"] = self.prod_entry.get()
        day_info["mood"] = self.mood_entry.get()
        day_info["stress"] = self.stress_entry.get()

    def calculate_total_caffeine(self):
        total_caffeine = 0
        for drink_entry in self.drink_entries:
            total_caffeine += drink_entry.calculate_caffeine()
        return total_caffeine

    def validate_day_data(self):
        try:
            year = int(self.year_entry.get_value())
            month = int(self.month_entry.get_value())
            day = int(self.day_entry.get_value())
            date = datetime.date(year, month, day)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid date.")
            return False

        try:
            work_hours = float(self.wh_entry.get())
            if work_hours < 0:
                raise ValueError("Work hours must be a non-negative number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid non-negative number for work hours.")
            return False

        try:
            screen_time = int(self.screen_entry.get())
            if screen_time < 0:
                raise ValueError("Screen time must be a non-negative integer.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid non-negative integer for screen time.")
            return False

        for field_name, field_entry in [
            ("Sleep Quality", self.sleep_entry),
            ("Productivity Score", self.prod_entry),
            ("Mood Score", self.mood_entry),
            ("Stress Level", self.stress_entry),
        ]:
            try:
                value = int(field_entry.get())
                if not (1 <= value <= 10):
                    raise ValueError(f"{field_name} must be between 1 and 10.")
            except ValueError:
                messagebox.showerror("Invalid Input", f"Please enter a valid integer (1-10) for {field_name}.")
                return False

        return True

    def on_previous(self):
        self.save_data_to_controller()
        self.controller.go_to_day_frame(self.day_index - 1)

    def on_next(self):
        if self.validate_day_data():
            self.save_data_to_controller()
            self.controller.go_to_day_frame(self.day_index + 1)

    def on_finish(self):
        if self.validate_day_data():
            self.save_data_to_controller()
            self.controller.go_to_final_frame()

class FinalFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ttk.Label(self, text="All Set!", font=("TkDefaultFont", 14, "bold"))
        label.pack(pady=10)

        upload_label = ttk.Label(self, text="Please upload your health data file here and submit the form:")
        upload_label.pack(pady=5)

        self.file_label = ttk.Label(self, textvariable=self.controller.health_data_file)
        self.file_label.pack(pady=2)

        upload_btn = ttk.Button(self, text="Browse XML File", command=self.browse_file)
        upload_btn.pack(pady=5)

        submit_btn = ttk.Button(self, text="Submit", command=self.controller.submit_all)
        submit_btn.pack(pady=20)

        back_btn = ttk.Button(self, text="Back", command=self.go_back)
        back_btn.pack()

    def browse_file(self):
        path = filedialog.askopenfilename(
            filetypes=[('XML Files', '*.xml'), ('All Files', '*.*')],
            title="Select an XML file"
        )
        if path:
            self.controller.health_data_file.set(path)

    def go_back(self):
        self.controller.go_to_day_frame(self.controller.num_days.get() - 1)

if __name__ == "__main__":
    app = MultiStepApp()
    app.mainloop()