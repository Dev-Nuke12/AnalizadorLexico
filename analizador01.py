import re
from collections import Counter
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from tkinter import font as tkfont

def analizadorLexico(line):
    # Mantengo la función original
    tokens = {
        'PALABRA CLAVE': r'\b(if|else|while|for|return|int|float|def|char|void)\b',
        'IDENTIFICADOR': r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
        'NUMERO': r'\b\d+(\.\d+)?\b',
        'OPERADOR': r'[+\-*/=<>!]+',
        'DELIMITADOR': r'[;,.(){}\[\]]',
        'STRING': r'".*?"',
        'COMENTARIO': r'\/\/.|\/\[\s\S]?\\/'
    }
    
    results = []
    token_counts = Counter()
    
    while line:
        match_found = False
        
        for token_type, pattern in tokens.items():
            match = re.match(pattern, line)
            if match:
                lexeme = match.group(0)
                results.append((lexeme, token_type))
                token_counts[token_type] += 1
                line = line[len(lexeme):].lstrip()
                match_found = True
                break
        
        if not match_found:
            # Si hay un carácter no reconocido, lo marcamos como ERROR
            if line:
                results.append((line[0], "ERROR"))
                token_counts["ERROR"] += 1
            line = line[1:].lstrip()
    
    return results, token_counts

def syntax_analyzer(tokens):
    # Mantengo la función original
    if not tokens:
        return "No hay tokens para analizar."
    
    errors = []
    i = 0
    
    while i < len(tokens):
        lexeme, token_type = tokens[i]
        
        # Verificar estructuras de control
        if token_type == "PALABRA CLAVE" and lexeme in {"if", "while", "for"}:
            # Buscar paréntesis de apertura
            if i + 1 < len(tokens):
                next_lexeme, next_type = tokens[i + 1]
                if next_lexeme != "(":
                    errors.append(f"Error: Se esperaba '(' después de '{lexeme}' en posición {i+1}")
            else:
                errors.append(f"Error: Expresión incompleta después de '{lexeme}'")
            
            # Buscar paréntesis de cierre (buscar próximo paréntesis de cierre)
            found_closing = False
            j = i + 1
            while j < len(tokens):
                if tokens[j][0] == ")":
                    found_closing = True
                    break
                j += 1
            
            if not found_closing:
                errors.append(f"Error: Falta ')' para cerrar la condición de '{lexeme}'")
            
            # Buscar llaves de apertura después del paréntesis de cierre
            if found_closing and j + 1 < len(tokens):
                if tokens[j + 1][0] != "{":
                    errors.append(f"Error: Se esperaba '{{' después de la condición en '{lexeme}'")
        
        # Verificar declaraciones de variables
        if token_type == "PALABRA CLAVE" and lexeme in {"int", "float", "char", "void"}:
            if i + 1 < len(tokens):
                next_lexeme, next_type = tokens[i + 1]
                # Si es una función (tiene paréntesis después del identificador)
                if next_type == "IDENTIFICADOR" and i + 2 < len(tokens) and tokens[i + 2][0] == "(":
                    pass  # Es una declaración de función, no procesamos ahora
                # Si es una variable
                elif next_type == "IDENTIFICADOR":
                    # Buscar punto y coma
                    found_semicolon = False
                    j = i + 2
                    while j < len(tokens):
                        if tokens[j][0] == ";":
                            found_semicolon = True
                            break
                        j += 1
                    
                    if not found_semicolon:
                        errors.append(f"Error: Falta ';' al final de la declaración de '{next_lexeme}'")
                else:
                    errors.append(f"Error: Se esperaba un identificador después de '{lexeme}'")
            else:
                errors.append(f"Error: Declaración incompleta después de '{lexeme}'")
        
        # Verificar asignaciones
        if token_type == "IDENTIFICADOR" and i + 1 < len(tokens) and tokens[i + 1][0] == "=":
            # Buscar punto y coma después de la asignación
            found_semicolon = False
            j = i + 2
            while j < len(tokens):
                if tokens[j][0] == ";":
                    found_semicolon = True
                    break
                j += 1
            
            if not found_semicolon:
                errors.append(f"Error: Falta ';' al final de la asignación de '{lexeme}'")
        
        i += 1
    
    return "El análisis sintáctico no encontró errores." if not errors else "\n".join(errors)

def semantic_analyzer(tokens):
    if not tokens:
        return "No hay tokens para analizar."
    
    declared_variables = set()
    initialized_variables = set()
    declared_functions = set()
    used_variables = set()
    errors = []
    
    # Primero identificamos todos los strings y comentarios
    string_and_comment_ranges = []
    start_index = None
    in_multiline_comment = False
    
    for i, (lexeme, token_type) in enumerate(tokens):
        if token_type == "COMENTARIO":
            if lexeme.startswith('/*'):
                in_multiline_comment = True
                start_index = i
            elif lexeme.startswith('*/') and in_multiline_comment:
                string_and_comment_ranges.append((start_index, i))
                in_multiline_comment = False
            elif lexeme.startswith('//'):
                string_and_comment_ranges.append((i, i))
        elif token_type == "STRING":
            string_and_comment_ranges.append((i, i))
    
    # Función para verificar si un índice está dentro de un string o comentario
    def is_in_string_or_comment(index):
        for start, end in string_and_comment_ranges:
            if start <= index <= end:
                return True
        return False
    
    i = 0
    while i < len(tokens):
        lexeme, token_type = tokens[i]
        
        # Verificar declaraciones de variables
        if token_type == "PALABRA CLAVE" and lexeme in {"int", "float", "char"}:
            if i + 1 < len(tokens) and tokens[i + 1][1] == "IDENTIFICADOR":
                var_name = tokens[i + 1][0]
                
                # Verificar si es función (tiene paréntesis después)
                if i + 2 < len(tokens) and tokens[i + 2][0] == "(":
                    declared_functions.add(var_name)
                else:
                    # Es una variable
                    if var_name in declared_variables:
                        errors.append(f"Error: La variable '{var_name}' ya ha sido declarada.")
                    
                    declared_variables.add(var_name)
                    
                    # Verificar si está inicializada
                    j = i + 2
                    while j < len(tokens) and tokens[j][0] != ";":
                        if tokens[j][0] == "=":
                            initialized_variables.add(var_name)
                            break
                        j += 1
        
        # Verificar usos de variables
        elif token_type == "IDENTIFICADOR" and not is_in_string_or_comment(i):
            var_name = lexeme
            # Si no es parte de una declaración
            is_declaration = False
            if i > 0 and tokens[i-1][1] == "PALABRA CLAVE" and tokens[i-1][0] in {"int", "float", "char", "void"}:
                is_declaration = True
            
            # Si es un uso de variable (no declaración y no llamada a función)
            if not is_declaration and (i+1 >= len(tokens) or tokens[i+1][0] != "("):
                used_variables.add(var_name)
                if var_name not in declared_variables and var_name not in declared_functions:
                    # Solo marcar como error si no es una palabra clave reservada
                    if not (lexeme in ["if", "else", "while", "for", "return", "int", "float", "def", "char", "void"]):
                        errors.append(f"Error: La variable '{var_name}' se usa sin haber sido declarada.")
                elif var_name not in initialized_variables:
                    errors.append(f"Advertencia: La variable '{var_name}' se usa posiblemente sin inicializar.")
        
        i += 1
    
    # Verificar variables no utilizadas
    unused_vars = declared_variables - used_variables
    for var in unused_vars:
        errors.append(f"Advertencia: La variable '{var}' está declarada pero no se utiliza.")
    
    return "El análisis semántico no encontró errores." if not errors else "\n".join(errors)

def generate_syntax_tree(tokens):
    """
    Genera un árbol sintáctico básico basado en los tokens.
    """
    tree = []
    stack = []
    
    for lexeme, token_type in tokens:
        if token_type in {"PALABRA CLAVE", "IDENTIFICADOR", "NUMERO", "OPERADOR"}:
            tree.append((lexeme, token_type))
        elif lexeme == "(":
            stack.append(lexeme)
        elif lexeme == ")":
            while stack and stack[-1] != "(":
                tree.append((stack.pop(), "OPERADOR"))
            stack.pop()  # Eliminar el paréntesis de apertura
        else:
            stack.append(lexeme)
    
    while stack:
        tree.append((stack.pop(), "OPERADOR"))
    
    return tree

def generate_polish_notation(tokens):
    """
    Genera la notación polaca (postfija) basada en los tokens.
    """
    output = []
    operators = []
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '=': 0}
    
    for lexeme, token_type in tokens:
        if token_type in {"IDENTIFICADOR", "NUMERO"}:  # Incluir números
            output.append(lexeme)
        elif token_type == "OPERADOR":
            while (operators and operators[-1] != "(" and
                   precedence.get(operators[-1], 0) >= precedence.get(lexeme, 0)):
                output.append(operators.pop())
            operators.append(lexeme)
        elif lexeme == "(":
            operators.append(lexeme)
        elif lexeme == ")":
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            operators.pop()  # Eliminar el paréntesis de apertura
    
    while operators:
        output.append(operators.pop())
    
    return " ".join(output)

def generate_reverse_polish_notation(tokens):
    """
    Genera la notación polaca inversa (postfija) basada en los tokens.
    """
    output = []
    operators = []
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '=': 0}
    
    for lexeme, token_type in tokens:
        if token_type in {"IDENTIFICADOR", "NUMERO"}:  # Aceptar identificadores y números como operandos
            output.append(lexeme)
        elif token_type == "OPERADOR":
            while (operators and operators[-1] != "(" and
                   precedence.get(operators[-1], 0) >= precedence.get(lexeme, 0)):
                output.append(operators.pop())
            operators.append(lexeme)
        elif lexeme == "(":
            operators.append(lexeme)
        elif lexeme == ")":
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            operators.pop()  # Eliminar el paréntesis de apertura
    
    while operators:
        output.append(operators.pop())
    
    return " ".join(output)

def parse_expression_to_tree(tokens):
    """
    Convierte una expresión en tokens a un árbol sintáctico.
    """
    stack = []
    operators = []
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '=': 0}

    for lexeme, token_type in tokens:
        if token_type in {"IDENTIFICADOR", "NUMERO"}:  # Incluir números
            stack.append([lexeme])  # Cada operando es una hoja
        elif token_type == "OPERADOR":
            while (operators and operators[-1] != "(" and
                   precedence.get(operators[-1], 0) >= precedence.get(lexeme, 0)):
                op = operators.pop()
                right = stack.pop()
                left = stack.pop()
                stack.append([op, left, right])  # Crear subárbol
            operators.append(lexeme)
        elif lexeme == "(":
            operators.append(lexeme)
        elif lexeme == ")":
            while operators and operators[-1] != "(":
                op = operators.pop()
                right = stack.pop()
                left = stack.pop()
                stack.append([op, left, right])  # Crear subárbol
            operators.pop()  # Eliminar el paréntesis de apertura

    while operators:
        op = operators.pop()
        right = stack.pop()
        left = stack.pop()
        stack.append([op, left, right])  # Crear subárbol

    return stack[0] if stack else None

class CodeAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Léxico")
        self.root.geometry("1100x750")
        self.root.configure(bg="#000000")  # Fondo negro
        
        # Configuración de estilos
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#000000")  # Fondo negro
        self.style.configure("TButton", font=("Consolas", 10), background="#2E86C1", foreground="#000000")
        self.style.configure("TRadiobutton", font=("Consolas", 10), background="#000000", foreground="#FFFFFF")
        self.style.configure("TLabel", font=("Consolas", 11), background="#000000", foreground="#FFFFFF")
        self.style.configure("Header.TLabel", font=("Consolas", 16, "bold"), background="#000000", foreground="#FFFFFF")
      
        
        # Variables
        self.analysis_type_var = tk.StringVar(value="Léxico")
        self.current_tokens = []
        self.current_token_counts = {}
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root, style="TFrame")
        header_frame.pack(fill="x", pady=(10, 5))
        
    
        ttk.Label(header_frame, text="Analizador Léxico.", style="Header.TLabel").pack(anchor="center", pady=10)
        
        # Main content frame
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel (input)
        left_frame = ttk.Frame(main_frame, style="TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Analysis type selection
        ttk.Label(left_frame, text="Tipo de Análisis:", style="TLabel").pack(anchor="w", pady=(0, 5))
        
        # Buttons frame
        button_frame = ttk.Frame(left_frame, style="TFrame")
        button_frame.pack(fill="x", pady=5)
        
        self.lexico_button = ttk.Button(button_frame, text="Análisis Léxico", 
                                        command=lambda: self.run_analysis("Léxico"))
        self.lexico_button.pack(side="left", padx=(0, 5))
        
        self.sintactico_button = ttk.Button(button_frame, text="Análisis Sintáctico", 
                                           command=lambda: self.run_analysis("Sintáctico"))
        self.sintactico_button.pack(side="left", padx=5)
        
        self.semantico_button = ttk.Button(button_frame, text="Análisis Semántico", 
                                          command=lambda: self.run_analysis("Semántico"))
        self.semantico_button.pack(side="left", padx=5)
        
        # Botones adicionales para el árbol y la notación polaca
        ttk.Button(button_frame, text="Árbol Sintáctico", command=self.show_syntax_tree_window).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Notación Polaca", command=self.show_polish_notation_window).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Notación Polaca Inversa", command=self.show_reverse_polish_notation_window).pack(side="left", padx=5)
        
        # Code input
        ttk.Label(left_frame, text="Código a Analizar:", style="TLabel").pack(anchor="w", pady=(10, 5))
        
        self.code_input = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, 
                                                  font=("Consolas", 11),
                                                  width=40, height=20,
                                                  bg="#666666", fg="#FFFFFF")  # Fondo negro, texto blanco
        self.code_input.pack(fill="both", expand=True, pady=5)
        
        # Clear button
        ttk.Button(left_frame, text="Limpiar Código", command=self.clear_code).pack(pady=10)
        
        # Right panel (results)
        right_frame = ttk.Frame(main_frame, style="TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Resultados:", style="TLabel").pack(anchor="w", pady=(0, 5))
        
        # Notebook para los resultados
        self.result_notebook = ttk.Notebook(right_frame)
        self.result_notebook.pack(fill="both", expand=True)
        
        # Pestañas para diferentes resultados
        self.token_frame = ttk.Frame(self.result_notebook)
        self.counts_frame = ttk.Frame(self.result_notebook)
        self.errors_frame = ttk.Frame(self.result_notebook)
        
        self.result_notebook.add(self.token_frame, text="Tokens")
        self.result_notebook.add(self.counts_frame, text="Conteo")
        self.result_notebook.add(self.errors_frame, text="Errores")
        
        # Configurar los widgets de resultados
        # 1. Tabla de tokens
        self.token_tree = ttk.Treeview(self.token_frame, columns=("lexema", "tipo"), show="headings")
        self.token_tree.heading("lexema", text="Lexema")
        self.token_tree.heading("tipo", text="Tipo de Token")
        self.token_tree.column("lexema", width=150)
        self.token_tree.column("tipo", width=150)
        
        token_scroll = ttk.Scrollbar(self.token_frame, orient="vertical", command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=token_scroll.set)
        
        self.token_tree.pack(side="left", fill="both", expand=True)
        token_scroll.pack(side="right", fill="y")
        
        # 2. Tabla de conteo
        self.count_tree = ttk.Treeview(self.counts_frame, columns=("tipo", "cantidad"), show="headings")
        self.count_tree.heading("tipo", text="Tipo de Token")
        self.count_tree.heading("cantidad", text="Cantidad")
        self.count_tree.column("tipo", width=150)
        self.count_tree.column("cantidad", width=100)
        
        count_scroll = ttk.Scrollbar(self.counts_frame, orient="vertical", command=self.count_tree.yview)
        self.count_tree.configure(yscrollcommand=count_scroll.set)
        
        self.count_tree.pack(side="left", fill="both", expand=True)
        count_scroll.pack(side="right", fill="y")
        
        # 3. Texto para errores
        self.error_text = scrolledtext.ScrolledText(self.errors_frame, wrap=tk.WORD, 
                                                  font=("Consolas", 11),
                                                  bg="#666666", fg="#FFFFFF")  # Fondo negro, texto blanco
        self.error_text.pack(fill="both", expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Listo")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
    
    def clear_code(self):
        self.code_input.delete("1.0", tk.END)
        self.clear_results()
        self.status_var.set("Listo")
    
    def clear_results(self):
        # Limpiar tabla de tokens
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
            
        # Limpiar tabla de conteo
        for item in self.count_tree.get_children():
            self.count_tree.delete(item)
            
        # Limpiar texto de errores
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.config(state="disabled")
    
    def draw_syntax_tree(self, canvas, tree, x, y, x_offset, y_offset):
        """
        Dibuja el árbol sintáctico en un canvas.
        """
        if not tree:
            return

        node = tree[0]
        children = tree[1:] if len(tree) > 1 else []

        canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill="lightblue")
        canvas.create_text(x, y, text=node, font=("Arial", 10, "bold"))

        child_x = x - x_offset * (len(children) - 1) // 2
        for child in children:
            canvas.create_line(x, y + 20, child_x, y + y_offset - 20)
            self.draw_syntax_tree(canvas, child, child_x, y + y_offset, x_offset // 2, y_offset)
            child_x += x_offset

    def show_syntax_tree_window(self):
        # Crear una nueva ventana para mostrar el árbol sintáctico
        tree_window = tk.Toplevel(self.root)
        tree_window.title("Árbol Sintáctico")
        tree_window.geometry("800x600")

        canvas = tk.Canvas(tree_window, bg="white", width=800, height=600)
        canvas.pack(fill="both", expand=True)

        # Generar el árbol sintáctico dinámicamente
        syntax_tree = parse_expression_to_tree(self.current_tokens)
        if syntax_tree:
            self.draw_syntax_tree(canvas, syntax_tree, 400, 50, 200, 100)
        else:
            canvas.create_text(400, 300, text="No se pudo generar el árbol sintáctico.", font=("Arial", 14, "bold"))

    def show_polish_notation_window(self):
        # Crear una nueva ventana para mostrar la notación polaca
        polish_window = tk.Toplevel(self.root)
        polish_window.title("Notación Polaca")
        polish_window.geometry("600x400")

        polish_notation = generate_polish_notation(self.current_tokens)

        polish_text = scrolledtext.ScrolledText(polish_window, wrap=tk.WORD, font=("Consolas", 11), bg="#FFFFFF")
        polish_text.pack(fill="both", expand=True, padx=10, pady=10)
        polish_text.insert("1.0", polish_notation)
        polish_text.config(state="disabled")

    def show_reverse_polish_notation_window(self):
        # Crear una nueva ventana para mostrar la notación polaca inversa
        rpn_window = tk.Toplevel(self.root)
        rpn_window.title("Notación Polaca Inversa")
        rpn_window.geometry("600x400")

        reverse_polish_notation = generate_reverse_polish_notation(self.current_tokens)

        rpn_text = scrolledtext.ScrolledText(rpn_window, wrap=tk.WORD, font=("Consolas", 11), bg="#FFFFFF")
        rpn_text.pack(fill="both", expand=True, padx=10, pady=10)
        rpn_text.insert("1.0", reverse_polish_notation)
        rpn_text.config(state="disabled")

    def run_analysis(self, analysis_type):
        code = self.code_input.get("1.0", tk.END).strip()
        if not code:
            messagebox.showerror("Error", "Por favor, ingresa el código a analizar.")
            return

        self.status_var.set(f"Realizando análisis {analysis_type.lower()}...")
        self.clear_results()

        # Realizar análisis léxico siempre primero
        self.current_tokens, self.current_token_counts = analizadorLexico(code)

        # Mostrar resultados según el tipo de análisis
        if analysis_type == "Léxico":
            self.show_lexical_results()
            self.result_notebook.select(0)  # Mostrar pestaña de tokens
        elif analysis_type == "Sintáctico":
            self.show_lexical_results()  # Mostrar también los tokens
            self.show_syntax_results()
            self.result_notebook.select(2)  # Mostrar pestaña de errores
        elif analysis_type == "Semántico":
            self.show_lexical_results()  # Mostrar también los tokens
            self.show_semantic_results()
            self.result_notebook.select(2)  # Mostrar pestaña de errores

        self.status_var.set(f"Análisis {analysis_type.lower()} completado")
    
    def show_lexical_results(self):
        # Mostrar tokens
        for token in self.current_tokens:
            lexeme, token_type = token
            self.token_tree.insert("", "end", values=(lexeme, token_type))
        
        # Mostrar conteo
        for token_type, count in self.current_token_counts.items():
            self.count_tree.insert("", "end", values=(token_type, count))
    
    def show_syntax_results(self):
        # Analizar sintaxis y mostrar errores
        syntax_result = syntax_analyzer(self.current_tokens)
        
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.insert("1.0", "ANÁLISIS SINTÁCTICO\n\n" + syntax_result)
        self.error_text.config(state="disabled")
    
    def show_semantic_results(self):
        # Analizar semántica y mostrar errores
        semantic_result = semantic_analyzer(self.current_tokens)
        
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.insert("1.0", "ANÁLISIS SEMÁNTICO\n\n" + semantic_result)
        self.error_text.config(state="disabled")

# Iniciar la aplicación
if __name__ == "__main__":
    tk_root = tk.Tk()
    app = CodeAnalyzerApp(tk_root)
    tk_root.mainloop()