import tkinter as tk

root = tk.Tk()

# Ẩn tiêu đề và thanh viền của cửa sổ
root.overrideredirect(True)

# Lấy kích thước của màn hình
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Tạo một frame để chứa label, sử dụng để có thể thiết lập nền trong suốt
frame = tk.Frame(root, bg="white", width=screen_width, height=screen_height)
frame.pack(fill="both", expand=True)

# Tạo một label để hiển thị nội dung
label_text = "Your label content"
label = tk.Label(frame, text=label_text, bg="white", fg="black", font=("Arial", 18))
label.place(relx=0.5, rely=0.5, anchor="center")

# Thiết lập cửa sổ để nền trong suốt
root.attributes("-alpha", 0)

# Thiết lập kích thước và vị trí của cửa sổ
root.geometry(f"{screen_width}x{screen_height}+0+0")

root.mainloop()
