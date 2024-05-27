import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from deep_translator import GoogleTranslator
from lxml import etree as ET
import codecs

# Parser para XML
parser = ET.XMLParser(remove_blank_text=True)
tree = None
root = None
translations = {}
db_modified = False
xml_modified = False  # Para verificar si se ha realizado una traducción

# Diccionarios de lenguajes válidos y soporte para Google Translator
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

GOOGLE_TRANSLATE_LANGUAGES = {
    "Brazilian Portuguese": "pt",
    "Castilian Spanish": "es",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Korean": "ko",
    "Latinamerican Spanish": "es",
    "Polish": "pl",
    "Russian": "ru",
    "Simplified Chinese": "zh-CN",
    "Traditional Chinese": "zh-TW",
    "Turkish": "tr"
}

# Clase para gestión de proyectos
class XMLProjectManager:
    def __init__(self):
        self.proyecto_id = None
        self.db_path = None
        self.language = "Idioma original"  # Valor predeterminado

    def crear_proyecto(self, nombre_proyecto):
        # Crear carpeta y base de datos
        os.makedirs(nombre_proyecto, exist_ok=True)
        self.db_path = os.path.join(nombre_proyecto, 'proyecto.db')
        self._crear_base_datos()

        # Insertar el nuevo proyecto en la tabla Proyectos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Proyectos (nombre, ruta_carpeta) VALUES (?, ?)", (nombre_proyecto, nombre_proyecto))
        self.proyecto_id = cursor.lastrowid
        conn.commit()
        conn.close()

    def abrir_proyecto(self, db_path):
        # Abrir base de datos existente
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_load").format(error="La base de datos no existe en la ruta seleccionada."))
            return

        # Comprobar existencia de tablas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proyectos'")
        if not cursor.fetchone():
            messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_load").format(error="La base de datos no contiene las tablas necesarias."))
            conn.close()
            return
        
        # Obtener ID del proyecto
        cursor.execute("SELECT id FROM Proyectos")
        proyecto = cursor.fetchone()
        if proyecto is None:
            messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_load").format(error="No se encontró el proyecto en la base de datos."))
        else:
            self.proyecto_id = proyecto[0]
        conn.close()

    def _crear_base_datos(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ruta_carpeta TEXT NOT NULL
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            etiqueta_principal TEXT,
            variable TEXT,
            texto TEXT,
            language TEXT,
            FOREIGN KEY (proyecto_id) REFERENCES Proyectos(id)
        )""")
        conn.commit()
        conn.close()

    def cargar_xml(self, archivo_xml):
        global db_modified
        parser_with_comments = ET.XMLParser(remove_blank_text=False, strip_cdata=False, ns_clean=False, recover=True, encoding='utf-8')
        tree = ET.parse(archivo_xml, parser=parser_with_comments)
        root = tree.getroot()
        self.language = root.get("language") or "Idioma original"  # Obtener el idioma del archivo original
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for elem in root.iter():
            if isinstance(elem.tag, str):  # Asegurarse de que elem.tag es una cadena
                tag_parts = elem.tag.split('.')
                etiqueta_principal = tag_parts[0]
                variable = tag_parts[1] if len(tag_parts) > 1 else ''
                cursor.execute("SELECT id, texto FROM Etiquetas WHERE proyecto_id=? AND etiqueta_principal=? AND variable=?", 
                               (self.proyecto_id, etiqueta_principal, variable))
                result = cursor.fetchone()
                if result:
                    # Actualizar si el texto ha cambiado
                    if result[1] != elem.text:
                        cursor.execute("UPDATE Etiquetas SET texto=? WHERE id=?", (elem.text, result[0]))
                        db_modified = True
                else:
                    cursor.execute("""
                    INSERT INTO Etiquetas (proyecto_id, etiqueta_principal, variable, texto, language)
                    VALUES (?, ?, ?, ?, ?)""", (self.proyecto_id, etiqueta_principal, variable, elem.text, self.language))
                    db_modified = True
        
        conn.commit()
        conn.close()
        return tree, root

    def obtener_etiquetas(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, etiqueta_principal, variable, texto, language FROM Etiquetas WHERE proyecto_id=?", (self.proyecto_id,))
        etiquetas = cursor.fetchall()
        conn.close()
        return etiquetas

    def actualizar_etiqueta(self, id, texto_traducido):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE Etiquetas SET texto=? WHERE id=?", (texto_traducido, id))
        conn.commit()
        conn.close()

def load_translations():
    global translations
    try:
        tree = ET.parse('translations.xml')
        root = tree.getroot()
        for text in root.findall('text'):
            translations[text.get('id')] = text.text
    except Exception as e:
        messagebox.showerror("Error", f"Could not load translations: {e}")

def translate_text_id(text_id, **kwargs):
    text = translations.get(text_id, text_id)
    try:
        return text.format(**kwargs)
    except KeyError as e:
        print(f"Missing key in translations: {e}")
        return text
    except AttributeError:
        return text

def translate_text():
    global db_modified, xml_modified
    if not manager.proyecto_id:
        messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_no_file_translate"))
        return

    etiquetas = manager.obtener_etiquetas()
    output_language = output_language_var.get()
    target_lang = GOOGLE_TRANSLATE_LANGUAGES.get(output_language, 'es')

    translator = GoogleTranslator(source='auto', target=target_lang)
    try:
        for etiqueta in etiquetas:
            id, etiqueta_principal, variable, texto, _ = etiqueta
            translated_text = translator.translate(texto)
            manager.actualizar_etiqueta(id, translated_text)
        db_modified = True
        xml_modified = True
        messagebox.showinfo(translate_text_id("window_title"), translate_text_id("success_translate"))
    except Exception as e:
        messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_translate").format(error=e))

def save_xml():
    global xml_modified, tree, root
    if not manager.proyecto_id:
        messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_no_file"))
        return

    if root is None:
        messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_save").format(error="No XML file loaded."))
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            if xml_modified:
                etiquetas = manager.obtener_etiquetas()
                root.set("language", output_language_var.get())
                root.set("translatedname", VALID_LANGUAGES[output_language_var.get()])

                for etiqueta in etiquetas:
                    _, etiqueta_principal, variable, texto, _ = etiqueta
                    tag = f"{etiqueta_principal}.{variable}" if variable else etiqueta_principal
                    elem = root.find(f".//{tag}")
                    if elem is not None:
                        elem.text = texto

                tree = ET.ElementTree(root)
                with open(file_path, 'wb') as f:
                    f.write(codecs.BOM_UTF8)
                    tree.write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)
                xml_modified = False
            else:
                with open(file_path, 'wb') as f:
                    f.write(codecs.BOM_UTF8)
                    tree.write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)
            messagebox.showinfo(translate_text_id("window_title"), translate_text_id("success_save"))
        except Exception as e:
            messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_save").format(error=e))

def save_database():
    global db_modified
    if db_modified:
        messagebox.showinfo(translate_text_id("window_title"), translate_text_id("success_save_db"))
        db_modified = False
    else:
        messagebox.showinfo(translate_text_id("window_title"), translate_text_id("No changes to save"))

def on_closing():
    if db_modified:
        if messagebox.askokcancel(translate_text_id("window_title"), translate_text_id("desea salir sin guardar base de datos?")):
            app.destroy()
    else:
        app.destroy()

def visualizar_base_datos():
    if not manager.proyecto_id:
        messagebox.showerror(translate_text_id("window_title"), translate_text_id("error_no_file"))
        return

    etiquetas = manager.obtener_etiquetas()

    # Crear una nueva ventana para mostrar la base de datos
    db_window = tk.Toplevel(app)
    db_window.title(translate_text_id("view_db_title"))
    db_window.geometry("800x600")

    treeview = ttk.Treeview(db_window, columns=("etiqueta_principal", "variable", manager.language), show='headings')
    treeview.heading("etiqueta_principal", text=translate_text_id("Etiqueta Principal"))
    treeview.heading("variable", text=translate_text_id("Variable"))
    treeview.heading(manager.language, text=manager.language)

    # Añadir scrollbars
    vsb = ttk.Scrollbar(db_window, orient="vertical", command=treeview.yview)
    hsb = ttk.Scrollbar(db_window, orient="horizontal", command=treeview.xview)
    treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    treeview.pack(fill=tk.BOTH, expand=True)

    for etiqueta in etiquetas:
        treeview.insert("", "end", values=(etiqueta[1], etiqueta[2], etiqueta[3]))

def cargar_y_procesar_xml():
    global tree, root, xml_modified
    archivo_xml = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if archivo_xml:
        tree, root = manager.cargar_xml(archivo_xml)
        xml_modified = False

def main():
    global manager, output_language_var, app
    manager = XMLProjectManager()

    app = tk.Tk()
    app.withdraw()  # Ocultar ventana principal

    # Diálogo inicial
    respuesta = messagebox.askquestion(translate_text_id("window_title"), translate_text_id("¿Qué deseas hacer?"), icon='question', type='yesnocancel', default='yes', 
                                       detail=translate_text_id("Yes: Crear nuevo proyecto\nNo: Abrir proyecto existente"))
    if respuesta == 'yes':
        nombre_proyecto = simpledialog.askstring(translate_text_id("Nombre del proyecto"), translate_text_id("Introduce el nombre del nuevo proyecto:"))
        if nombre_proyecto:
            manager.crear_proyecto(nombre_proyecto)
        else:
            app.destroy()
            return
    elif respuesta == 'no':
        db_path = filedialog.askopenfilename(title=translate_text_id("Selecciona la base de datos del proyecto"), filetypes=[("Database files", "*.db")])
        if db_path:
            manager.abrir_proyecto(db_path)
        else:
            app.destroy()
            return
    else:
        app.destroy()
        return

    app.deiconify()
    app.title(translate_text_id("window_title"))
    app.geometry("400x200")

    app.protocol("WM_DELETE_WINDOW", on_closing)

    frame = tk.Frame(app)
    frame.pack(pady=20)

    load_button = tk.Button(frame, text=translate_text_id("load_button"), command=cargar_y_procesar_xml)
    load_button.grid(row=0, column=0, padx=10)

    translate_button = tk.Button(frame, text=translate_text_id("translate_button"), command=translate_text)
    translate_button.grid(row=0, column=1, padx=10)

    save_button = tk.Button(frame, text=translate_text_id("save_button"), command=save_xml)
    save_button.grid(row=0, column=2, padx=10)

    save_db_button = tk.Button(frame, text=translate_text_id("save_db_button"), command=save_database)
    save_db_button.grid(row=1, column=0, columnspan=3, pady=10)

    view_db_button = tk.Button(frame, text=translate_text_id("view_db_button"), command=visualizar_base_datos)
    view_db_button.grid(row=2, column=0, columnspan=3, pady=10)

    # Selección de idioma de salida
    output_language_var = tk.StringVar(app)
    output_language_var.set("Castilian Spanish")  # Valor por defecto

    output_language_label = tk.Label(frame, text=translate_text_id("output_language_label"))
    output_language_label.grid(row=3, column=0, padx=10, pady=10)

    output_language_menu = ttk.Combobox(frame, textvariable=output_language_var, values=list(GOOGLE_TRANSLATE_LANGUAGES.keys()))
    output_language_menu.grid(row=3, column=1, padx=10, pady=10)

    app.mainloop()

if __name__ == "__main__":
    load_translations()
    main()
