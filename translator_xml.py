import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from deep_translator import GoogleTranslator
from lxml import etree as ET
import codecs

parser = ET.XMLParser(remove_blank_text=True)
tree = None
root = None
translations = {}

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

def load_translations():
    global translations
    try:
        tree = ET.parse('translations.xml')
        root = tree.getroot()
        for text in root.findall('text'):
            translations[text.get('id')] = text.text
    except Exception as e:
        messagebox.showerror("Error", f"Could not load translations: {e}")

def _(text_id, **kwargs):
    text = translations.get(text_id, text_id)
    try:
        return text.format(**kwargs)
    except KeyError as e:
        print(f"Missing key in translations: {e}")
        return text

def load_xml():
    global tree, root
    file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            tree = ET.XML(content, parser)
            root = tree

            if not validate_xml_structure(root):
                return
            
            messagebox.showinfo(title=_("title"), message=_("success_load"))
        except Exception as e:
            messagebox.showerror(title=_("title"), message=_("error_load").format(error=e))

def save_xml():
    if tree is None:
        messagebox.showerror(title=_("title"), message=_("error_no_file"))
        return

    output_language = output_language_var.get()
    root.attrib['language'] = output_language
    root.attrib['translatedname'] = VALID_LANGUAGES[output_language]

    file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if file_path:
        try:
            with open(file_path, 'wb') as f:
                f.write(codecs.BOM_UTF8)
                ET.ElementTree(tree).write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)
            messagebox.showinfo(title=_("title"), message=_("success_save"))
        except Exception as e:
            messagebox.showerror(title=_("title"), message=_("error_save").format(error=e))

def translate_text():
    if root is None:
        messagebox.showerror(title=_("title"), message=_("error_no_file_translate"))
        return

    language = root.attrib.get("language")
    if language not in GOOGLE_TRANSLATE_LANGUAGES:
        messagebox.showerror(title=_("title"), message=_("error_invalid_language").format(language=language))
        return

    source_lang = GOOGLE_TRANSLATE_LANGUAGES[language]
    target_lang = GOOGLE_TRANSLATE_LANGUAGES.get(output_language_var.get(), 'es')

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    try:
        for elem in root.iter():
            if isinstance(elem, ET._Element) and elem.text and elem.text.strip():
                translated_text = translator.translate(elem.text)
                elem.text = translated_text
        messagebox.showinfo(title=_("title"), message=_("success_translate"))
    except Exception as e:
        messagebox.showerror(title=_("title"), message=_("error_translate").format(error=e))

def validate_xml_structure(root):
    if root.tag != "infotexts":
        messagebox.showerror(title=_("title"), message=_("error_invalid_structure"))
        return False

    language = root.attrib.get("language")
    translatedname = root.attrib.get("translatedname")
    
    if language not in VALID_LANGUAGES:
        messagebox.showerror(title=_("title"), message=_("error_invalid_language").format(language=language))
        return False
    
    correct_translatedname = VALID_LANGUAGES[language]
    if translatedname != correct_translatedname:
        response = messagebox.askyesno(title=_("title"), 
                                       message=_("change_translatedname").format(language=language, translatedname=translatedname, correct_translatedname=correct_translatedname))
        if response:
            root.attrib['translatedname'] = correct_translatedname
            messagebox.showinfo(title=_("title"), message=_("info_translatedname_changed").format(correct_translatedname=correct_translatedname))
        else:
            return False
    
    return True

app = tk.Tk()
load_translations()
app.title(_("title"))
app.geometry("400x200")

frame = tk.Frame(app)
frame.pack(pady=20)

load_button = tk.Button(frame, text=_("load_button"), command=load_xml)
load_button.grid(row=0, column=0, padx=10)

translate_button = tk.Button(frame, text=_("translate_button"), command=translate_text)
translate_button.grid(row=0, column=1, padx=10)

save_button = tk.Button(frame, text=_("save_button"), command=save_xml)
save_button.grid(row=0, column=2, padx=10)

# Selección de idioma de salida
output_language_var = tk.StringVar(app)
output_language_var.set("Castilian Spanish")  # Valor por defecto

output_language_label = tk.Label(frame, text=_("output_language_label"))
output_language_label.grid(row=1, column=0, padx=10, pady=10)

output_language_menu = ttk.Combobox(frame, textvariable=output_language_var, values=list(GOOGLE_TRANSLATE_LANGUAGES.keys()))
output_language_menu.grid(row=1, column=1, padx=10, pady=10)

app.mainloop()
