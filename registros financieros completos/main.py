import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
from fpdf import FPDF
import os

class Registro:
    def __init__(self, descripcion, monto, categoria, nota, fecha=None):
        self.descripcion = descripcion
        self.monto = monto
        self.categoria = categoria
        self.nota = nota
        self.fecha = fecha or datetime.now().strftime("%Y-%m-%d")

class Cliente:
    def __init__(self, nombre):
        self.nombre = nombre
        self.registros = []
        self.saldo = 0
        self.cargar_registros()

    def cargar_registros(self):
        """Cargar registros desde un archivo JSON si existe."""
        archivo = f"{self.nombre}_registros.json"
        if os.path.exists(archivo):
            with open(archivo, 'r') as f:
                datos = json.load(f)
                for reg in datos:
                    self.registros.append(Registro(**reg))
                    self.saldo += reg['monto']

    def guardar_registros(self):
        """Guardar los registros en un archivo JSON."""
        datos = [r.__dict__ for r in self.registros]
        with open(f"{self.nombre}_registros.json", 'w') as f:
            json.dump(datos, f, indent=4)

    def agregar_registro(self, descripcion, monto, categoria, nota):
        registro = Registro(descripcion, monto, categoria, nota)
        self.registros.append(registro)
        self.saldo += monto
        self.guardar_registros()  # Guardar automáticamente los registros

    def calcular_resumen(self):
        ingresos = sum(r.monto for r in self.registros if r.monto > 0)
        gastos = sum(-r.monto for r in self.registros if r.monto < 0)
        return ingresos, gastos, self.saldo

    def exportar_csv(self, ruta):
        with open(ruta, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Descripción", "Monto", "Categoría", "Nota"])
            for r in self.registros:
                writer.writerow([r.fecha, r.descripcion, r.monto, r.categoria, r.nota])

    def exportar_pdf(self, ruta):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Resumen financiero - {self.nombre}", ln=True, align='C')
        pdf.ln(10)
        for r in self.registros:
            pdf.cell(200, 10, txt=f"{r.fecha} - {r.descripcion} - {r.monto} ({r.categoria}): {r.nota}", ln=True)
        pdf.output(ruta)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor Financiero de Clientes")
        self.clientes = {}
        self.cliente_actual = None

        self.inicio_frame = ttk.Frame(root, padding=10)
        self.inicio_frame.pack(fill=BOTH, expand=True)
        self.titulo = ttk.Label(self.inicio_frame, text="Bienvenido al Gestor Financiero", font=("Helvetica", 18))
        self.titulo.pack(pady=10)

        self.nombre_entry = ttk.Entry(self.inicio_frame)
        self.nombre_entry.pack(pady=5)
        ttk.Button(self.inicio_frame, text="Ingresar", command=self.iniciar_cliente).pack(pady=10)

    def iniciar_cliente(self):
        nombre = self.nombre_entry.get()
        if not nombre:
            messagebox.showerror("Error", "Debe ingresar un nombre")
            return
        if nombre not in self.clientes:
            self.clientes[nombre] = Cliente(nombre)  # Cargar registros desde JSON
        self.cliente_actual = self.clientes[nombre]
        self.inicio_frame.destroy()
        self.mostrar_interfaz()

    def mostrar_interfaz(self):
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(fill=BOTH, expand=True)

        ttk.Label(self.frame, text=f"Cliente: {self.cliente_actual.nombre}", font=("Helvetica", 14)).pack()

        ttk.Button(self.frame, text="Agregar Registro", command=self.agregar_registro).pack(pady=5)
        ttk.Button(self.frame, text="Ver Gráficos", command=self.mostrar_grafico).pack(pady=5)
        ttk.Button(self.frame, text="Exportar CSV", command=self.exportar_csv).pack(pady=5)
        ttk.Button(self.frame, text="Exportar PDF", command=self.exportar_pdf).pack(pady=5)

        self.lista = tk.Listbox(self.frame, height=15)
        self.lista.pack(fill=BOTH, expand=True)
        self.actualizar_lista()

    def agregar_registro(self):
        descripcion = simpledialog.askstring("Descripción", "¿Qué deseas registrar?")
        if not descripcion:
            return
        try:
            monto = float(simpledialog.askstring("Monto", "¿Cuál es el monto?"))
        except:
            messagebox.showerror("Error", "Monto inválido")
            return
        categoria = simpledialog.askstring("Categoría", "¿Cuál es la categoría? (ej. Salario, Comida, etc.)") or "General"
        nota = simpledialog.askstring("Nota", "¿Deseas agregar una nota?") or ""

        self.cliente_actual.agregar_registro(descripcion, monto, categoria, nota)
        self.actualizar_lista()

    def actualizar_lista(self):
        self.lista.delete(0, tk.END)
        for r in self.cliente_actual.registros:
            self.lista.insert(tk.END, f"{r.fecha} - {r.descripcion} ({r.categoria}): {r.monto}")
        ingresos, gastos, saldo = self.cliente_actual.calcular_resumen()
        self.lista.insert(tk.END, f"\nResumen mensual - Ingresos: {ingresos}, Gastos: {gastos}, Saldo: {saldo}")

    def mostrar_grafico(self):
        ingresos, gastos, saldo = self.cliente_actual.calcular_resumen()
        fig, ax = plt.subplots()
        ax.bar(['Ingresos', 'Gastos', 'Saldo'], [ingresos, gastos, saldo], color=['green', 'red', 'blue'])
        ax.set_title('Resumen Financiero')
        ax.set_ylabel('Monto')

        grafico_window = tk.Toplevel(self.root)
        grafico_window.title("Gráfico Financiero")
        canvas = FigureCanvasTkAgg(fig, master=grafico_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def exportar_csv(self):
        ruta = f"{self.cliente_actual.nombre}_finanzas.csv"
        self.cliente_actual.exportar_csv(ruta)
        messagebox.showinfo("Exportado", f"Registros exportados a {ruta}")

    def exportar_pdf(self):
        ruta = f"{self.cliente_actual.nombre}_finanzas.pdf"
        self.cliente_actual.exportar_pdf(ruta)
        messagebox.showinfo("Exportado", f"Registros exportados a {ruta}")

if __name__ == '__main__':
    app = ttk.Window(themename="journal")
    App(app)
    app.mainloop()
