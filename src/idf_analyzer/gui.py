"""Tkinter desktop interface for the HIDRONEXO IDF Analyzer prototype."""
from __future__ import annotations

import csv
import json
import math
import statistics
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "HIDRONEXO | IDF Analyzer"
GAMMA = 0.5772156649015329


def parse_number(value: str) -> float:
    return float(value.strip().replace(',', '.'))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace('Z', '+00:00'))


def read_series(path: Path, time_column: str, rain_column: str):
    records = []
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        sample = stream.read(4096)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(stream, dialect=dialect)
        if not reader.fieldnames or time_column not in reader.fieldnames or rain_column not in reader.fieldnames:
            raise ValueError('No se encuentran las columnas seleccionadas en el CSV.')
        for line, row in enumerate(reader, 2):
            if not row.get(time_column) or not row.get(rain_column):
                continue
            try:
                timestamp = parse_time(row[time_column])
                rainfall = parse_number(row[rain_column])
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Fila {line}: fecha o precipitación inválida ({exc}).') from exc
            if not math.isfinite(rainfall) or rainfall < 0:
                raise ValueError(f'Fila {line}: la precipitación debe ser un número finito ≥ 0.')
            records.append((timestamp, rainfall))
    records.sort(key=lambda item: item[0])
    if len(records) < 10:
        raise ValueError('Se necesitan al menos 10 registros válidos.')
    if len({t for t, _ in records}) != len(records):
        raise ValueError('Hay marcas de tiempo duplicadas. Corrija el CSV antes de analizarlo.')
    return records


def annual_maxima(records, step_minutes: int, duration_hours: float):
    window = duration_hours * 60 / step_minutes
    n = round(window)
    if n < 1 or abs(window - n) > 1e-8:
        raise ValueError(f'La duración {duration_hours:g} h no es múltiplo del intervalo {step_minutes} min.')
    if len(records) < n:
        raise ValueError(f'No hay registros suficientes para una ventana de {duration_hours:g} h.')
    expected = step_minutes * 60
    for index in range(1, len(records)):
        seconds = (records[index][0] - records[index - 1][0]).total_seconds()
        if abs(seconds - expected) > 1e-6:
            raise ValueError(f'La serie no es regular: el intervalo entre las filas {index} y {index + 1} no es {step_minutes} min. Revise huecos, duplicados y zona horaria.')
    sums = []
    running = 0.0
    for i, (_, value) in enumerate(records):
        running += value
        if i >= n:
            running -= records[i - n][1]
        if i >= n - 1:
            sums.append((records[i][0], running))
    years = {}
    for timestamp, depth in sums:
        year = timestamp.year
        years[year] = max(years.get(year, float('-inf')), depth)
    if len(years) < 3:
        raise ValueError(f'Solo hay {len(years)} años con datos; se requieren al menos 3 para un ajuste preliminar.')
    return sorted(years.values()), len(years)


def gumbel_quantile(sample, return_period):
    mean = statistics.mean(sample)
    sd = statistics.stdev(sample)
    if sd <= 0:
        raise ValueError('La serie anual no presenta variabilidad suficiente para ajustar Gumbel.')
    beta = sd * math.sqrt(6) / math.pi
    location = mean - GAMMA * beta
    reduced_variate = -math.log(-math.log(1 - 1 / return_period))
    return location + beta * reduced_variate


def fit_sherman(durations, intensities):
    """Fit i=a/(t+b)^n by log-linear least squares and a small grid over b."""
    if len(durations) < 3:
        return None
    best = None
    for k in range(301):
        b = max(durations) * k / 100
        xs = [math.log(t + b) for t in durations]
        ys = [math.log(i) for i in intensities]
        xbar, ybar = statistics.mean(xs), statistics.mean(ys)
        denom = sum((x - xbar) ** 2 for x in xs)
        if denom == 0:
            continue
        slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
        intercept = ybar - slope * xbar
        error = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
        if best is None or error < best[0]:
            best = (error, math.exp(intercept), b, -slope)
    return best[1:] if best else None


class IDFApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1120x760')
        self.minsize(900, 620)
        self.configure(bg='#f3f6f8')
        self.records = None
        self.columns = []
        self.results = []
        self._style()
        self._build()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#f3f6f8')
        style.configure('Card.TFrame', background='white')
        style.configure('TLabel', background='#f3f6f8', foreground='#19324a', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI Semibold', 21), foreground='#102b46')
        style.configure('Sub.TLabel', foreground='#61758a', font=('Segoe UI', 10))
        style.configure('Card.TLabel', background='white', foreground='#19324a')
        style.configure('CardHead.TLabel', background='white', foreground='#102b46', font=('Segoe UI Semibold', 11))
        style.configure('Accent.TButton', font=('Segoe UI Semibold', 10), padding=(14, 9), background='#087e8b', foreground='white')
        style.map('Accent.TButton', background=[('active', '#066b76')])
        style.configure('Treeview', rowheight=27, font=('Segoe UI', 9), background='white', fieldbackground='white')
        style.configure('Treeview.Heading', font=('Segoe UI Semibold', 9))

    def _build(self):
        root = ttk.Frame(self, padding=24)
        root.pack(fill='both', expand=True)
        ttk.Label(root, text='IDF Analyzer', style='Title.TLabel').pack(anchor='w')
        ttk.Label(root, text='Análisis preliminar de frecuencia de precipitación · HIDRONEXO', style='Sub.TLabel').pack(anchor='w', pady=(2, 18))
        top = ttk.Frame(root)
        top.pack(fill='x')
        self._input_card(top)
        self._params_card(top)
        results_card = ttk.Frame(root, style='Card.TFrame', padding=14)
        results_card.pack(fill='both', expand=True, pady=(14, 0))
        head = ttk.Frame(results_card, style='Card.TFrame')
        head.pack(fill='x')
        ttk.Label(head, text='Curvas intensidad–duración–frecuencia', style='CardHead.TLabel').pack(side='left')
        ttk.Button(head, text='Exportar CSV', command=self.export_csv).pack(side='right', padx=(6, 0))
        ttk.Button(head, text='Exportar JSON', command=self.export_json).pack(side='right')
        body = ttk.Frame(results_card, style='Card.TFrame')
        body.pack(fill='both', expand=True, pady=(10, 0))
        left = ttk.Frame(body, style='Card.TFrame')
        left.pack(side='left', fill='both', expand=True)
        cols = ('duration', 'years') + tuple(f't{t:g}' for t in self.return_periods())
        self.table = ttk.Treeview(left, columns=cols, show='headings', height=12)
        labels = ['Duración (h)', 'Años'] + [f'T={t:g} a (mm/h)' for t in self.return_periods()]
        for col, label in zip(cols, labels):
            self.table.heading(col, text=label)
            self.table.column(col, width=105, anchor='center')
        self.table.pack(fill='both', expand=True)
        self.chart = tk.Canvas(body, width=360, height=300, bg='white', highlightthickness=0)
        self.chart.pack(side='right', fill='both', expand=True, padx=(12, 0))
        self.status = tk.StringVar(value='Carga un CSV para comenzar. Formato esperado: fecha/hora ISO y lluvia por intervalo en mm.')
        ttk.Label(root, textvariable=self.status, style='Sub.TLabel', wraplength=1000).pack(anchor='w', pady=(10, 0))

    def _input_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=14)
        card.pack(side='left', fill='both', expand=True, padx=(0, 8))
        ttk.Label(card, text='1 · Datos de precipitación', style='CardHead.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
        self.path_var = tk.StringVar(value='Sin archivo seleccionado')
        ttk.Label(card, textvariable=self.path_var, style='Card.TLabel').grid(row=1, column=0, columnspan=2, sticky='w')
        ttk.Button(card, text='Abrir CSV…', command=self.load_csv).grid(row=1, column=2, sticky='e')
        ttk.Label(card, text='Columna temporal', style='Card.TLabel').grid(row=2, column=0, sticky='w', pady=(12, 3))
        self.time_box = ttk.Combobox(card, state='readonly', width=20)
        self.time_box.grid(row=2, column=1, columnspan=2, sticky='ew', pady=(12, 3))
        ttk.Label(card, text='Columna lluvia (mm/intervalo)', style='Card.TLabel').grid(row=3, column=0, sticky='w', pady=3)
        self.rain_box = ttk.Combobox(card, state='readonly', width=20)
        self.rain_box.grid(row=3, column=1, columnspan=2, sticky='ew', pady=3)
        ttk.Label(card, text='Intervalo de registro (min)', style='Card.TLabel').grid(row=4, column=0, sticky='w', pady=(3, 0))
        self.step_var = tk.StringVar(value='60')
        ttk.Entry(card, textvariable=self.step_var, width=9).grid(row=4, column=1, sticky='w', pady=(3, 0))
        card.columnconfigure(1, weight=1)

    def _params_card(self, parent):
        card = ttk.Frame(parent, style='Card.TFrame', padding=14)
        card.pack(side='right', fill='both', expand=True, padx=(8, 0))
        ttk.Label(card, text='2 · Parámetros', style='CardHead.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        ttk.Label(card, text='Duraciones (horas)', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4)
        self.durations_var = tk.StringVar(value='1, 2, 3, 6, 12, 24')
        ttk.Entry(card, textvariable=self.durations_var, width=27).grid(row=1, column=1, sticky='ew', pady=4)
        ttk.Label(card, text='Períodos de retorno (años)', style='Card.TLabel').grid(row=2, column=0, sticky='w', pady=4)
        self.returns_var = tk.StringVar(value='2, 5, 10, 25, 50, 100')
        ttk.Entry(card, textvariable=self.returns_var, width=27).grid(row=2, column=1, sticky='ew', pady=4)
        ttk.Label(card, text='Muestreo: AMS · Distribución: Gumbel (momentos)', style='Card.TLabel', wraplength=300).grid(row=3, column=0, columnspan=2, sticky='w', pady=(8, 10))
        ttk.Button(card, text='Calcular curvas IDF', style='Accent.TButton', command=self.calculate).grid(row=4, column=0, columnspan=2, sticky='ew')
        card.columnconfigure(1, weight=1)

    def return_periods(self):
        try:
            return [parse_number(x) for x in self.returns_var.get().split(',') if x.strip()]
        except ValueError:
            return [2, 5, 10]

    def load_csv(self):
        filename = filedialog.askopenfilename(title='Seleccionar serie de precipitación', filetypes=[('CSV', '*.csv'), ('Todos los archivos', '*.*')])
        if not filename:
            return
        try:
            with open(filename, 'r', encoding='utf-8-sig', newline='') as stream:
                sample = stream.read(4096)
                stream.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(stream, dialect=dialect)
                columns = next(reader)
            self.columns = columns
            self.time_box['values'] = columns
            self.rain_box['values'] = columns
            self.time_box.set(next((c for c in columns if any(s in c.lower() for s in ('time', 'fecha', 'date', 'hora'))), columns[0]))
            self.rain_box.set(next((c for c in columns if any(s in c.lower() for s in ('rain', 'precip', 'lluv', 'mm'))), columns[-1]))
            self.path_var.set(Path(filename).name)
            self.file_path = Path(filename)
            self.status.set(f'CSV seleccionado: {len(columns)} columnas. Revise los campos e intervalo antes de calcular.')
        except Exception as exc:
            messagebox.showerror('No se pudo abrir el CSV', str(exc))

    def calculate(self):
        if not hasattr(self, 'file_path'):
            messagebox.showinfo('Faltan datos', 'Seleccione primero un archivo CSV.')
            return
        try:
            step = int(self.step_var.get())
            if step <= 0:
                raise ValueError('El intervalo debe ser mayor que cero.')
            self.records = read_series(self.file_path, self.time_box.get(), self.rain_box.get())
            durations = sorted(set(parse_number(x) for x in self.durations_var.get().split(',') if x.strip()))
            returns = sorted(set(parse_number(x) for x in self.returns_var.get().split(',') if x.strip()))
            if not durations or any(t <= 0 for t in durations):
                raise ValueError('Indique duraciones positivas en horas.')
            if not returns or any(t <= 1 for t in returns):
                raise ValueError('Los períodos de retorno deben ser mayores de 1 año.')
            self.return_periods = lambda: returns
            self.results = []
            samples = {}
            for duration in durations:
                values, years = annual_maxima(self.records, step, duration)
                samples[duration] = (values, years)
            self.table.configure(columns=('duration', 'years') + tuple(f't{t:g}' for t in returns))
            for col, label in zip(self.table['columns'], ['Duración (h)', 'Años'] + [f'T={t:g} a (mm/h)' for t in returns]):
                self.table.heading(col, text=label)
            self.table.delete(*self.table.get_children())
            for duration, (values, years) in samples.items():
                depths = [gumbel_quantile(values, t) for t in returns]
                intensities = [depth / duration for depth in depths]
                self.results.append({'duration_hours': duration, 'years': years, 'depth_mm': depths, 'intensity_mm_h': intensities})
                self.table.insert('', 'end', values=(f'{duration:g}', years, *[f'{i:.3f}' for i in intensities]))
            self.sherman = {}
            for j, ret in enumerate(returns):
                fit = fit_sherman(durations, [row['intensity_mm_h'][j] for row in self.results])
                if fit:
                    self.sherman[str(ret)] = {'a': fit[0], 'b_hours': fit[1], 'n': fit[2]}
            self._draw_chart(returns)
            self.status.set(f'Análisis completado: {len(self.records):,} registros, {len(self.results)} duraciones. AMS anual · Gumbel por momentos. Revise advertencias del README antes de interpretar.')
        except Exception as exc:
            messagebox.showerror('No se pudo calcular', str(exc))

    def _draw_chart(self, returns):
        c = self.chart
        c.delete('all')
        w, h = max(c.winfo_width(), 360), max(c.winfo_height(), 280)
        left, right, top, bottom = 55, w - 20, 20, h - 42
        c.create_text(12, 10, anchor='nw', text='Intensidad (mm/h)', fill='#53697e', font=('Segoe UI', 9))
        c.create_line(left, top, left, bottom, fill='#9aabba')
        c.create_line(left, bottom, right, bottom, fill='#9aabba')
        if not self.results:
            c.create_text(w / 2, h / 2, text='Los resultados aparecerán aquí', fill='#8a9aaa')
            return
        ymax = max(max(r['intensity_mm_h']) for r in self.results) * 1.12
        xmax = max(r['duration_hours'] for r in self.results)
        colors = ['#087e8b', '#e07a35', '#7357a6', '#3d8a5a', '#c64c61', '#5578b8']
        for j, ret in enumerate(returns):
            pts = []
            for row in self.results:
                x = left + (math.log(row['duration_hours']) / math.log(xmax) if xmax > 1 else 0.5) * (right - left)
                y = bottom - row['intensity_mm_h'][j] / ymax * (bottom - top)
                pts.extend((x, y))
            color = colors[j % len(colors)]
            if len(pts) >= 4:
                c.create_line(*pts, fill=color, width=2, smooth=True)
            for x, y in zip(pts[::2], pts[1::2]):
                c.create_oval(x-3, y-3, x+3, y+3, fill=color, outline='')
            c.create_text(right - 4, top + 12 * j, anchor='ne', text=f'T={ret:g} a', fill=color, font=('Segoe UI', 8, 'bold'))
        for tick in range(5):
            y = bottom - tick * (bottom - top) / 4
            c.create_line(left, y, right, y, fill='#e7edf1')
            c.create_text(left - 7, y, anchor='e', text=f'{ymax*tick/4:.0f}', fill='#718397', font=('Segoe UI', 8))
        c.create_text((left+right)/2, h-12, text='Duración (h, escala logarítmica)', fill='#53697e', font=('Segoe UI', 9))

    def export_csv(self):
        if not self.results:
            messagebox.showinfo('Sin resultados', 'Calcule las curvas antes de exportar.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')], initialfile='idf_resultados.csv')
        if not path:
            return
        returns = self.return_periods()
        with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.writer(stream)
            writer.writerow(['duration_hours', 'annual_years', *[f'intensity_T{t:g}_mm_h' for t in returns]])
            for row in self.results:
                writer.writerow([row['duration_hours'], row['years'], *row['intensity_mm_h']])
        self.status.set(f'Resultados CSV guardados en {path}')

    def export_json(self):
        if not self.results:
            messagebox.showinfo('Sin resultados', 'Calcule las curvas antes de exportar.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')], initialfile='idf_resultados.json')
        if not path:
            return
        payload = {'application': 'HIDRONEXO idf_analyzer GUI prototype', 'method': {'sampling': 'AMS', 'distribution': 'Gumbel', 'estimation': 'moments'}, 'input_file': str(self.file_path), 'interval_minutes': int(self.step_var.get()), 'return_periods_years': self.return_periods(), 'idf': self.results, 'sherman_fit': self.sherman}
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        self.status.set(f'Resultados JSON guardados en {path}')


if __name__ == '__main__':
    IDFApp().mainloop()

