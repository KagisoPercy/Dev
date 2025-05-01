import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
import mysql.connector
import os
import datetime
from email.message import EmailMessage
import smtplib

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Login")
        self.root.geometry("400x350")

        self.db_type = tk.StringVar(value="PostgreSQL")
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="5432")
        self.user = tk.StringVar()
        self.password = tk.StringVar()
        self.database = tk.StringVar()

        self.build_login_form()

    def build_login_form(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="DB Type:").grid(row=0, column=0, sticky=tk.W)
        db_combo = ttk.Combobox(frame, textvariable=self.db_type, values=["PostgreSQL", "Redshift", "MySQL"], state="readonly")
        db_combo.grid(row=0, column=1)

        ttk.Label(frame, text="Host:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.host).grid(row=1, column=1)

        ttk.Label(frame, text="Port:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.port).grid(row=2, column=1)

        ttk.Label(frame, text="User:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.user).grid(row=3, column=1)

        ttk.Label(frame, text="Password:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.password, show="*").grid(row=4, column=1)

        ttk.Label(frame, text="Database:").grid(row=5, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.database).grid(row=5, column=1)

        ttk.Button(frame, text="Connect", command=self.connect_to_db).grid(row=6, column=0, columnspan=2, pady=20)

    def connect_to_db(self):
        db_type = self.db_type.get()
        host = self.host.get()
        port = self.port.get()
        user = self.user.get()
        password = self.password.get()
        database = self.database.get()

        try:
            if db_type in ['PostgreSQL', 'Redshift']:
                conn = psycopg2.connect(
                    host=host, port=port, user=user,
                    password=password, dbname=database
                )
            elif db_type == 'MySQL':
                conn = mysql.connector.connect(
                    host=host, port=port, user=user,
                    password=password, database=database
                )
            else:
                raise ValueError("Unsupported DB type")

            messagebox.showinfo("Success", f"Connected to {db_type}!")
            self.open_delete_records_window(conn)

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def open_delete_records_window(self, conn):
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Records")
        delete_window.geometry("500x600")

        frame = ttk.Frame(delete_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Schema:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.schema_combo = ttk.Combobox(frame, width=30)
        self.schema_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Table:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.table_combo = ttk.Combobox(frame, width=30)
        self.table_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Column:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.column_combo = ttk.Combobox(frame, width=30)
        self.column_combo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Record IDs (comma-separated):").grid(row=3, column=0, sticky=tk.W, pady=5)
        record_ids = ttk.Entry(frame, width=30)
        record_ids.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Manager Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        manager_email = ttk.Entry(frame, width=30)
        manager_email.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Reason for Deletion:").grid(row=5, column=0, sticky=tk.W, pady=5)
        reason_entry = ttk.Entry(frame, width=30)
        reason_entry.grid(row=5, column=1, padx=5, pady=5)

        def load_schemas():
            try:
                cursor = conn.cursor()
                if self.db_type.get() in ['PostgreSQL', 'Redshift']:
                    cursor.execute("SELECT schema_name FROM information_schema.schemata")
                elif self.db_type.get() == 'MySQL':
                    cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA")
                schemas = [row[0] for row in cursor.fetchall()]
                self.schema_combo['values'] = schemas
                if 'public' in schemas:
                    self.schema_combo.set('public')
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load schemas: {str(e)}")

        def load_tables(event=None):
            try:
                cursor = conn.cursor()
                schema = self.schema_combo.get()
                if not schema:
                    return
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (schema,))
                tables = [row[0] for row in cursor.fetchall()]
                self.table_combo['values'] = tables
                if tables:
                    self.table_combo.set(tables[0])
                    load_columns()
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load tables: {str(e)}")

        def load_columns(event=None):
            try:
                cursor = conn.cursor()
                schema = self.schema_combo.get()
                table = self.table_combo.get()
                if not table:
                    return
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                """, (schema, table))
                columns = [row[0] for row in cursor.fetchall()]
                self.column_combo['values'] = columns
                if columns:
                    self.column_combo.set(columns[0])
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load columns: {str(e)}")

        def send_email(recipient, subject, body):
            try:
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = 'your_email@gmail.com'
                msg['To'] = recipient
                msg.set_content(body)
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login('your_email@gmail.com', 'your_app_password')
                    smtp.send_message(msg)
            except Exception as e:
                messagebox.showwarning("Email Failed", f"Email sending failed: {str(e)}")

        def delete_records():
            try:
                email = manager_email.get().strip()
                reason = reason_entry.get().strip()
                if not email or "@" not in email:
                    messagebox.showerror("Input Error", "Valid manager email is required before deletion.")
                    return

                schema = self.schema_combo.get()
                table = self.table_combo.get()
                column = self.column_combo.get()
                ids = [id.strip() for id in record_ids.get().split(',') if id.strip()]
                if not ids:
                    messagebox.showerror("Input Error", "Record IDs cannot be empty.")
                    return

                confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(ids)} record(s)?")
                if not confirm:
                    return

                cursor = conn.cursor()
                placeholders = ','.join(['%s'] * len(ids))
                if self.db_type.get() == 'MySQL':
                    fetch_query = f"SELECT * FROM `{schema}`.`{table}` WHERE `{column}` IN ({placeholders})"
                else:
                    fetch_query = f'SELECT * FROM "{schema}"."{table}" WHERE "{column}" IN ({placeholders})'
                cursor.execute(fetch_query, ids)
                records = cursor.fetchall()
                colnames = [desc[0] for desc in cursor.description]

                # Archive deleted records
                archive_dir = filedialog.askdirectory(initialdir=os.path.join(os.path.expanduser("~"), "Documents"))
                if not archive_dir:
                    return
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = os.path.join(archive_dir, f"deleted_{table}_{now}.sql")

                with open(archive_path, 'w') as f:
                    for row in records:
                        values = [f"'{str(v).replace("'", "''")}'" if v is not None else "NULL" for v in row]
                        f.write(f"INSERT INTO {schema}.{table} ({', '.join(colnames)}) VALUES ({', '.join(values)});\n")
                    f.write(f"-- Reason: {reason}\n-- Deleted by: {email} on {now}\n")

                # Delete records
                if self.db_type.get() == 'MySQL':
                    del_query = f"DELETE FROM `{schema}`.`{table}` WHERE `{column}` IN ({placeholders})"
                else:
                    del_query = f'DELETE FROM "{schema}"."{table}" WHERE "{column}" IN ({placeholders})'
                cursor.execute(del_query, ids)
                conn.commit()
                deleted = cursor.rowcount
                cursor.close()

                messagebox.showinfo("Deleted", f"{deleted} records deleted. Archive saved. Email sent.")

                send_email(email, f"{deleted} Record(s) Deleted", f"{deleted} record(s) from {schema}.{table} were deleted.\nReason: {reason}")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        self.schema_combo.bind("<<ComboboxSelected>>", load_tables)
        self.table_combo.bind("<<ComboboxSelected>>", load_columns)

        load_schemas()

        ttk.Button(frame, text="Delete Records", command=delete_records).grid(row=6, column=0, columnspan=2, pady=20)

# Launcher
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
import mysql.connector
import os
import datetime
from email.message import EmailMessage
import smtplib

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Login")
        self.root.geometry("400x350")

        self.db_type = tk.StringVar(value="PostgreSQL")
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="5432")
        self.user = tk.StringVar()
        self.password = tk.StringVar()
        self.database = tk.StringVar()

        self.build_login_form()

    def build_login_form(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="DB Type:").grid(row=0, column=0, sticky=tk.W)
        db_combo = ttk.Combobox(frame, textvariable=self.db_type, values=["PostgreSQL", "Redshift", "MySQL"], state="readonly")
        db_combo.grid(row=0, column=1)

        ttk.Label(frame, text="Host:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.host).grid(row=1, column=1)

        ttk.Label(frame, text="Port:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.port).grid(row=2, column=1)

        ttk.Label(frame, text="User:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.user).grid(row=3, column=1)

        ttk.Label(frame, text="Password:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.password, show="*").grid(row=4, column=1)

        ttk.Label(frame, text="Database:").grid(row=5, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.database).grid(row=5, column=1)

        ttk.Button(frame, text="Connect", command=self.connect_to_db).grid(row=6, column=0, columnspan=2, pady=20)

    def connect_to_db(self):
        db_type = self.db_type.get()
        host = self.host.get()
        port = self.port.get()
        user = self.user.get()
        password = self.password.get()
        database = self.database.get()

        try:
            if db_type in ['PostgreSQL', 'Redshift']:
                conn = psycopg2.connect(
                    host=host, port=port, user=user,
                    password=password, dbname=database
                )
            elif db_type == 'MySQL':
                conn = mysql.connector.connect(
                    host=host, port=port, user=user,
                    password=password, database=database
                )
            else:
                raise ValueError("Unsupported DB type")

            messagebox.showinfo("Success", f"Connected to {db_type}!")
            self.open_delete_records_window(conn)

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def open_delete_records_window(self, conn):
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Records")
        delete_window.geometry("500x600")

        frame = ttk.Frame(delete_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Schema:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.schema_combo = ttk.Combobox(frame, width=30)
        self.schema_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Table:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.table_combo = ttk.Combobox(frame, width=30)
        self.table_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Column:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.column_combo = ttk.Combobox(frame, width=30)
        self.column_combo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Record IDs (comma-separated):").grid(row=3, column=0, sticky=tk.W, pady=5)
        record_ids = ttk.Entry(frame, width=30)
        record_ids.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Manager Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        manager_email = ttk.Entry(frame, width=30)
        manager_email.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Reason for Deletion:").grid(row=5, column=0, sticky=tk.W, pady=5)
        reason_entry = ttk.Entry(frame, width=30)
        reason_entry.grid(row=5, column=1, padx=5, pady=5)

        def load_schemas():
            try:
                cursor = conn.cursor()
                if self.db_type.get() in ['PostgreSQL', 'Redshift']:
                    cursor.execute("SELECT schema_name FROM information_schema.schemata")
                elif self.db_type.get() == 'MySQL':
                    cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA")
                schemas = [row[0] for row in cursor.fetchall()]
                self.schema_combo['values'] = schemas
                if 'public' in schemas:
                    self.schema_combo.set('public')
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load schemas: {str(e)}")

        def load_tables(event=None):
            try:
                cursor = conn.cursor()
                schema = self.schema_combo.get()
                if not schema:
                    return
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (schema,))
                tables = [row[0] for row in cursor.fetchall()]
                self.table_combo['values'] = tables
                if tables:
                    self.table_combo.set(tables[0])
                    load_columns()
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load tables: {str(e)}")

        def load_columns(event=None):
            try:
                cursor = conn.cursor()
                schema = self.schema_combo.get()
                table = self.table_combo.get()
                if not table:
                    return
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                """, (schema, table))
                columns = [row[0] for row in cursor.fetchall()]
                self.column_combo['values'] = columns
                if columns:
                    self.column_combo.set(columns[0])
                cursor.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load columns: {str(e)}")

        def send_email(recipient, subject, body):
            try:
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = 'your_email@gmail.com'
                msg['To'] = recipient
                msg.set_content(body)
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login('your_email@gmail.com', 'your_app_password')
                    smtp.send_message(msg)
            except Exception as e:
                messagebox.showwarning("Email Failed", f"Email sending failed: {str(e)}")

        def delete_records():
            try:
                email = manager_email.get().strip()
                reason = reason_entry.get().strip()
                if not email or "@" not in email:
                    messagebox.showerror("Input Error", "Valid manager email is required before deletion.")
                    return

                schema = self.schema_combo.get()
                table = self.table_combo.get()
                column = self.column_combo.get()
                ids = [id.strip() for id in record_ids.get().split(',') if id.strip()]
                if not ids:
                    messagebox.showerror("Input Error", "Record IDs cannot be empty.")
                    return

                confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(ids)} record(s)?")
                if not confirm:
                    return

                cursor = conn.cursor()
                placeholders = ','.join(['%s'] * len(ids))
                if self.db_type.get() == 'MySQL':
                    fetch_query = f"SELECT * FROM `{schema}`.`{table}` WHERE `{column}` IN ({placeholders})"
                else:
                    fetch_query = f'SELECT * FROM "{schema}"."{table}" WHERE "{column}" IN ({placeholders})'
                cursor.execute(fetch_query, ids)
                records = cursor.fetchall()
                colnames = [desc[0] for desc in cursor.description]

                # Archive deleted records
                archive_dir = filedialog.askdirectory(initialdir=os.path.join(os.path.expanduser("~"), "Documents"))
                if not archive_dir:
                    return
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = os.path.join(archive_dir, f"deleted_{table}_{now}.sql")

                with open(archive_path, 'w') as f:
                    for row in records:
                        values = [f"'{str(v).replace("'", "''")}'" if v is not None else "NULL" for v in row]
                        f.write(f"INSERT INTO {schema}.{table} ({', '.join(colnames)}) VALUES ({', '.join(values)});\n")
                    f.write(f"-- Reason: {reason}\n-- Deleted by: {email} on {now}\n")

                # Delete records
                if self.db_type.get() == 'MySQL':
                    del_query = f"DELETE FROM `{schema}`.`{table}` WHERE `{column}` IN ({placeholders})"
                else:
                    del_query = f'DELETE FROM "{schema}"."{table}" WHERE "{column}" IN ({placeholders})'
                cursor.execute(del_query, ids)
                conn.commit()
                deleted = cursor.rowcount
                cursor.close()

                messagebox.showinfo("Deleted", f"{deleted} records deleted. Archive saved. Email sent.")

                send_email(email, f"{deleted} Record(s) Deleted", f"{deleted} record(s) from {schema}.{table} were deleted.\nReason: {reason}")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        self.schema_combo.bind("<<ComboboxSelected>>", load_tables)
        self.table_combo.bind("<<ComboboxSelected>>", load_columns)

        load_schemas()

        ttk.Button(frame, text="Delete Records", command=delete_records).grid(row=6, column=0, columnspan=2, pady=20)

# Launcher
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
