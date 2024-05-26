import tkinter as tk
from tkinter import filedialog, messagebox
from deep_translator import GoogleTranslator
from lxml import etree as ET
import codecs

parser = ET.XMLParser(remove_blank_text=True)
tree = None
root = None

VALID_LANGUAGES = {
    "Brazilian Portuguese": "Português brasileiro",
    "Castilian Spanish": "Castellano",
    "English": "English",
    "French": "Français",
    "German": "Deutsch",
    "Japanese": "日本語",
    "Korean": "한국어",
    "Latinamerican Spanish": "Español Latinoamericano",
    "Polish": "Polski",
    "Russian": "Русский",
    "Simplified Chinese": "中文(简体)",
    "Traditional Chinese": "中文(繁體)",
    "Turkish": "Türkçe"
}

def load_xml():
    global tree, root
    file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            tree = ET.XML(content, parser)
            root = tree

            # Validar estructura del XML
            if not validate_xml_structure(root):
                return
            
            messagebox.showinfo("Success", "Archivo XML cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo XML: {e}")

def save_xml():
    if tree is None:
        messagebox.showerror("Error", "No hay archivo XML cargado para guardar.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            with open(file_path, 'wb') as f:
                f.write(codecs.BOM_UTF8)
                ET.ElementTree(tree).write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)
            messagebox.showinfo("Success", "Archivo XML guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo XML: {e}")

def translate_text():
    if root is None:
        messagebox.showerror("Error", "Primero carga un archivo XML.")
        return

    translator = GoogleTranslator(source='en', target='es')
    try:
        for elem in root.iter():
            if isinstance(elem, ET._Element) and elem.text and elem.text.strip():
                translated_text = translator.translate(elem.text)
                elem.text = translated_text
        messagebox.showinfo("Success", "Traducción completada.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo completar la traducción: {e}")

def validate_xml_structure(root):
    if root.tag != "infotexts":
        messagebox.showerror("Error", "El archivo XML debe comenzar con la etiqueta <infotexts>.")
        return False

    language = root.attrib.get("language")
    translatedname = root.attrib.get("translatedname")
    
    if language not in VALID_LANGUAGES:
        messagebox.showerror("Error", f"El valor de 'language' no es válido: {language}.")
        return False
    
    if translatedname != VALID_LANGUAGES[language]:
        messagebox.showerror("Error", f"El valor de 'translatedname' no es válido para el idioma '{language}': {translatedname}.")
        return False
    
    return True

app = tk.Tk()
app.title("Traductor XML")
app.geometry("400x200")

frame = tk.Frame(app)
frame.pack(pady=20)

load_button = tk.Button(frame, text="Cargar XML", command=load_xml)
load_button.grid(row=0, column=0, padx=10)

translate_button = tk.Button(frame, text="Traducir", command=translate_text)
translate_button.grid(row=0, column=1, padx=10)

save_button = tk.Button(frame, text="Guardar XML", command=save_xml)
save_button.grid(row=0, column=2, padx=10)

app.mainloop()
