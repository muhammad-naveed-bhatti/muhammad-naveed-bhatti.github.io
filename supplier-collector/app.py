import argparse
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import webbrowser

from collector import Client, DEMO_HTML, FIELDS, VERSION, export_csv, extract, web_url


class App:
    def __init__(self, root):
        self.root = root
        self.rows = []
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.busy = False
        root.title(f'Supplier Catalogue Collector {VERSION} | Muhammad Naveed')
        root.geometry('1100x720')
        root.minsize(800, 580)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f2f5fa')
        style.configure('TLabel', background='#f2f5fa', foreground='#152c49', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 23, 'bold'))
        style.configure('TButton', padding=(12, 8), font=('Segoe UI', 10))
        style.configure('Treeview', rowheight=29, font=('Segoe UI', 10))
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Supplier Catalogue Collector', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Public product pages → reviewable records → Excel-ready CSV  |  Muhammad Naveed').pack(anchor='w', pady=(4, 16))
        ttk.Label(frame, text='Website URLs — one per line, up to 25. Supports Product JSON-LD and Books to Scrape.').pack(anchor='w')
        self.urls = tk.Text(frame, height=4, font=('Segoe UI', 10), wrap='word')
        self.urls.pack(fill='x', pady=6)
        self.urls.insert('1.0', 'https://books.toscrape.com/')
        settings = ttk.Frame(frame)
        settings.pack(fill='x', pady=6)
        ttk.Label(settings, text='Supplier label (optional)').pack(side='left')
        self.supplier = ttk.Entry(settings, width=28)
        self.supplier.pack(side='left', padx=8)
        ttk.Label(settings, text='Max pages (1–25)').pack(side='left', padx=(12, 4))
        self.limit = ttk.Spinbox(settings, from_=1, to=25, width=5)
        self.limit.set('3')
        self.limit.pack(side='left')
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=(8, 12))
        self.start_btn = ttk.Button(buttons, text='Collect products', command=self.start)
        self.start_btn.pack(side='left')
        self.demo_btn = ttk.Button(buttons, text='Load offline demo', command=self.demo)
        self.demo_btn.pack(side='left', padx=8)
        self.stop_btn = ttk.Button(buttons, text='Stop', command=self.stop.set, state='disabled')
        self.stop_btn.pack(side='left')
        self.export_btn = ttk.Button(buttons, text='Export CSV', command=self.export, state='disabled')
        self.export_btn.pack(side='right')
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill='both', expand=True)
        columns = ('product', 'sku', 'price', 'currency', 'availability', 'supplier')
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.table.heading(col, text=col.replace('_', ' ').title())
            self.table.column(col, width=250 if col == 'product' else 110, minwidth=65)
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=self.table.xview)
        self.table.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky='nsew')
        scroll.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.table.bind('<Double-1>', self.open_source)
        self.status = tk.StringVar(value='Ready. Try the offline demo or collect the live practice catalogue.')
        ttk.Label(frame, textvariable=self.status, wraplength=1000).pack(anchor='w', pady=(12, 6))
        self.log = tk.Text(frame, height=3, state='disabled', font=('Segoe UI', 9), wrap='word')
        self.log.pack(fill='x')
        ttk.Label(frame, text='Double-click a row to open its source. Missing fields remain blank. Listed prices are not supplier quotations.', wraplength=1000).pack(anchor='w', pady=(8, 0))
        root.after(100, self.poll)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def note(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def set_rows(self, rows):
        self.rows = rows
        self.table.delete(*self.table.get_children())
        for i, row in enumerate(rows):
            self.table.insert('', 'end', iid=str(i), values=[row[k] for k in self.table['columns']])
        self.export_btn.configure(state='normal' if rows else 'disabled')

    def demo(self):
        self.set_rows(extract(DEMO_HTML, 'https://example.com/demo', 'Demo supplier — fictional')[0])
        self.status.set('3 fictional sample records. No website was contacted.')

    def start(self):
        try:
            urls = list(dict.fromkeys(web_url(u.strip()) for u in self.urls.get('1.0', 'end').splitlines() if u.strip()))
            limit = int(self.limit.get())
            if not urls or len(urls) > 25 or not 1 <= limit <= 25:
                raise ValueError('Enter 1–25 URLs and a page limit from 1 to 25.')
        except ValueError as exc:
            messagebox.showerror('Check input', str(exc))
            return
        if self.rows and not messagebox.askyesno('Start new collection?', 'Replace current results? Export CSV first if you want to keep them.'):
            return
        self.set_rows([])
        self.stop.clear()
        self.busy = True
        self.start_btn.configure(state='disabled')
        self.demo_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.status.set('Collecting…')
        threading.Thread(target=self.worker, args=(urls, limit, self.supplier.get().strip()), daemon=True).start()

    def worker(self, urls, limit, supplier):
        client = Client(self.stop)
        rows, seen, keys = [], set(), set()
        try:
            while urls and len(seen) < limit and not self.stop.is_set():
                url = urls.pop(0)
                if url in seen:
                    continue
                seen.add(url)
                try:
                    html, final_url = client.get(url)
                    extracted, next_url = extract(html, final_url, supplier)
                    for row in extracted:
                        key = tuple(row[k] for k in ('supplier', 'product', 'sku', 'price', 'currency', 'product_url'))
                        if key not in keys:
                            keys.add(key)
                            rows.append(row)
                    self.events.put(('note', f'{len(extracted)} products: {url}' if extracted else f'No supported product data: {url}. JavaScript-only pages need a separate adapter.'))
                    if next_url and next_url not in seen:
                        urls.append(next_url)
                except InterruptedError:
                    break
                except Exception as exc:
                    self.events.put(('note', f'Skipped {url}: {exc}'))
            self.events.put(('done', (rows, len(seen), bool(urls))))
        finally:
            client.session.close()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'note':
                    self.note(value)
                elif kind == 'done':
                    rows, pages, remaining = value
                    self.set_rows(rows)
                    state = 'Stopped' if self.stop.is_set() else 'Finished'
                    self.status.set(f'{state}: {len(rows)} records from {pages} attempted pages.' + (' Page limit reached or URLs remain.' if remaining else ''))
                    self.busy = False
                    self.start_btn.configure(state='normal')
                    self.demo_btn.configure(state='normal')
                    self.stop_btn.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='supplier-catalogue.csv', filetypes=[('CSV files', '*.csv')])
        if path:
            try:
                export_csv(path, self.rows)
                self.status.set(f'Saved {len(self.rows)} records: {path}')
            except OSError as exc:
                messagebox.showerror('Could not save', str(exc))

    def open_source(self, event=None):
        selected = self.table.selection()
        if selected:
            row = self.rows[int(selected[0])]
            webbrowser.open(row['product_url'] or row['source_url'])

    def close(self):
        self.stop.set()
        self.root.destroy()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', metavar='RESULT_JSON')
    args = parser.parse_args()
    root = tk.Tk()
    app = App(root)
    if args.smoke_test:
        root.withdraw()
        app.demo()
        root.update()
        assert len(app.rows) == 3 and len(app.table.get_children()) == 3
        Path(args.smoke_test).write_text(json.dumps({'version': VERSION, 'gui': 'passed', 'rows': len(app.rows)}), encoding='utf-8')
        root.destroy()
    else:
        root.mainloop()
