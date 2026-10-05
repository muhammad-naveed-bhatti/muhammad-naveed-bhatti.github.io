"""Build-time UI preview; Pillow is not needed to run the app."""
import tkinter as tk
from PIL import ImageGrab
from app import App
root = tk.Tk()
app = App(root)
app.demo()
root.update()
root.after(1500, root.quit)
root.mainloop()
assert app.footer.winfo_ismapped(), 'Footer must be visible'
assert app.footer.winfo_rooty() + app.footer.winfo_height() <= root.winfo_rooty() + root.winfo_height(), 'Footer must fit in window'
x,y = root.winfo_rootx(),root.winfo_rooty()
ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save('app-preview.png')
root.destroy()
