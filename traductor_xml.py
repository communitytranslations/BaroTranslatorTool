import tkinter as tk
from tkinter import filedialog, messagebox
from googletrans import Translator
import xml.etree.ElementTree as ET

def load_xml():
    file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            global tree, root
            tree = ET.parse(file_path)
            root = tree.getroot()
            messagebox.showinfo("Success", "Archivo XML cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo XML: {e}")

def save_xml():
    file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "Archivo XML guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo XML: {e}")

def translate_text():
    if not root:
        messagebox.showerror("Error", "Primero carga un archivo XML.")
        return

    translator = Translator()
    for elem in root.iter():
        if elem.text:
            translated = translator.translate(elem.text, src='en', dest='es')
            elem.text = translated.text
    
    messagebox.showinfo("Success", "Traducción completada.")

root = tk.Tk()
root.title("Traductor XML")
root.geometry("400x200")

frame = tk.Frame(root)
frame.pack(pady=20)

load_button = tk.Button(frame, text="Cargar XML", command=load_xml)
load_button.grid(row=0, column=0, padx=10)

translate_button = tk.Button(frame, text="Traducir", command=translate_text)
translate_button.grid(row=0, column=1, padx=10)

save_button = tk.Button(frame, text="Guardar XML", command=save_xml)
save_button.grid(row=0, column=2, padx=10)

root.mainloop()
