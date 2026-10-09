# ghost_node.py // NGrok & WAN Uyumlu Dinamik Port Sürümü
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from cryptography.fernet import Fernet
import os
import urllib.request

# --- VIBE & TEMA AYARLARI ---
BG_COLOR = "#0a0a0f"
FG_COLOR = "#00ffcc"
ACCENT_COLOR = "#1a1a24"
FONT_MAIN = ("Consolas", 10)
DEFAULT_PORT = 5050

class GhostNode:
    def __init__(self, root):
        self.root = root
        self.root.title("GHOST NODE // NGrok TUNNEL READY")
        self.root.geometry("680x650")
        self.root.configure(bg=BG_COLOR)
        
        self.conn = None
        self.cipher = None
        self.build_ui()

    def build_ui(self):
        # -- ÜST PANEL --
        top_frame = tk.Frame(self.root, bg=BG_COLOR, pady=15)
        top_frame.pack(fill=tk.X, padx=10)

        tk.Label(top_frame, text="Hedef IP:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_MAIN).grid(row=0, column=0, padx=2, sticky="e")
        self.ip_entry = tk.Entry(top_frame, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, insertbackground=FG_COLOR, width=15, relief=tk.FLAT)
        self.ip_entry.grid(row=0, column=1, padx=2, ipady=3)
        
        tk.Label(top_frame, text="Port:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_MAIN).grid(row=0, column=2, padx=2, sticky="e")
        self.port_entry = tk.Entry(top_frame, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, insertbackground=FG_COLOR, width=6, relief=tk.FLAT)
        self.port_entry.grid(row=0, column=3, padx=2, ipady=3)
        self.port_entry.insert(0, str(DEFAULT_PORT)) # Varsayılan Port

        tk.Label(top_frame, text="Gizli Key:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_MAIN).grid(row=0, column=4, padx=2, sticky="e")
        self.key_entry = tk.Entry(top_frame, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, insertbackground=FG_COLOR, width=22, relief=tk.FLAT)
        self.key_entry.grid(row=0, column=5, padx=2, ipady=3)

        tk.Button(top_frame, text="[ HOST OL (5050) ]", bg="#330066", fg="white", font=FONT_MAIN, relief=tk.FLAT, command=self.start_host).grid(row=1, column=1, columnspan=2, pady=15, sticky="we")
        tk.Button(top_frame, text="[ BAĞLAN ]", bg="#006633", fg="white", font=FONT_MAIN, relief=tk.FLAT, command=self.connect_to_host).grid(row=1, column=4, columnspan=2, pady=15, sticky="we")

        # -- ORTA PANEL --
        self.chat_display = scrolledtext.ScrolledText(self.root, bg=BG_COLOR, fg=FG_COLOR, font=FONT_MAIN, state=tk.DISABLED, relief=tk.FLAT, pady=5, padx=5)
        self.chat_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # -- ALT PANEL --
        bottom_frame = tk.Frame(self.root, bg=BG_COLOR, pady=10)
        bottom_frame.pack(fill=tk.X, padx=10)

        self.msg_entry = tk.Entry(bottom_frame, bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, insertbackground=FG_COLOR, relief=tk.FLAT)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        tk.Button(bottom_frame, text="GÖNDER", bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT_MAIN, relief=tk.FLAT, command=self.send_message).pack(side=tk.LEFT, padx=5, ipady=2)
        tk.Button(bottom_frame, text="DOSYA", bg=ACCENT_COLOR, fg="#ffcc00", font=FONT_MAIN, relief=tk.FLAT, command=self.send_file).pack(side=tk.LEFT, ipady=2)

        self.log_gui("[Sistem]: Ters Tünelleme (Ngrok) desteği aktif. Modeme ihtiyaç yok.")

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def start_host(self):
        key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, key.decode('utf-8'))
        local_ip = self.get_local_ip()
        
        def setup_server():
            self.log_gui(f"\n--- HOST BAŞLATILDI ---")
            self.log_gui(f"Dinlenen Port: {DEFAULT_PORT}")
            self.log_gui(f"Eğer modeme erişemiyorsanız, arkada 'ngrok tcp 5050' komutunu çalıştırın.")
            self.log_gui("Ngrok'un verdiği Adresi (örn: 0.tcp.ngrok.io) ve Port'u arkadaşınıza verin.\n")
            
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.bind(('0.0.0.0', DEFAULT_PORT))
                server.listen(1)
                self.conn, addr = server.accept()
                self.log_gui(f"\n[!] BİRİ BAĞLANDI! Şifreli tünel kuruldu: {addr}")
                threading.Thread(target=self.listen_for_data, daemon=True).start()
            except Exception as e:
                self.log_gui(f"Sunucu hatası: {e}")

        threading.Thread(target=setup_server, daemon=True).start()

    def connect_to_host(self):
        target_ip = self.ip_entry.get().strip()
        target_port = self.port_entry.get().strip()
        key_str = self.key_entry.get().strip()
        
        if not target_ip or not target_port or not key_str:
            messagebox.showerror("Hata", "Lütfen Hedef IP, Port ve Gizli Key girin.")
            return

        try:
            port_num = int(target_port)
            self.cipher = Fernet(key_str.encode('utf-8'))
        except Exception:
            messagebox.showerror("Hata", "Geçersiz Port veya Key formatı!")
            return

        def connect_thread():
            try:
                self.log_gui(f"Bağlanılıyor: {target_ip}:{port_num}...")
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.connect((target_ip, port_num))
                self.log_gui("\n[!] BAĞLANTI KURULDU! E2EE Tünel Aktif.")
                threading.Thread(target=self.listen_for_data, daemon=True).start()
            except Exception as e:
                self.log_gui(f"Bağlantı başarısız: {e}")

        threading.Thread(target=connect_thread, daemon=True).start()

    def send_data(self, data_type, content_bytes):
        if not self.conn or not self.cipher: return
        header = f"{data_type}".encode('utf-8')
        payload = header + b"|||" + content_bytes
        encrypted_data = self.cipher.encrypt(payload)
        msg_length = f"{len(encrypted_data):<10}".encode('utf-8')
        try:
            self.conn.sendall(msg_length + encrypted_data)
        except Exception as e:
            self.log_gui(f"Bağlantı koptu: {e}")

    def listen_for_data(self):
        while True:
            try:
                length_b = self.conn.recv(10)
                if not length_b: break
                length = int(length_b.decode('utf-8').strip())
                data = b""
                while len(data) < length:
                    chunk = self.conn.recv(min(4096, length - len(data)))
                    if not chunk: break
                    data += chunk
                decrypted = self.cipher.decrypt(data)
                header_bytes, content = decrypted.split(b"|||", 1)
                header = header_bytes.decode('utf-8')
                
                if header == "MSG":
                    self.log_gui(f" >> {content.decode('utf-8')}")
                elif header.startswith("FILE:"):
                    filename = header.split(":", 1)[1]
                    self.root.after(0, self.prompt_save_file, filename, content)
            except Exception:
                self.log_gui("\n[!] Bağlantı koptu veya karşı taraf çıktı.")
                self.conn = None
                break

    def send_message(self):
        text = self.msg_entry.get().strip()
        if text and self.conn:
            self.log_gui(f" Sen: {text}")
            self.msg_entry.delete(0, tk.END)
            threading.Thread(target=self.send_data, args=("MSG", text.encode('utf-8')), daemon=True).start()

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath and self.conn:
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            self.log_gui(f"[*] Gönderiliyor: {filename}...")
            threading.Thread(target=self.send_data, args=(f"FILE:{filename}", file_bytes), daemon=True).start()

    def prompt_save_file(self, filename, content_bytes):
        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(content_bytes)
            self.log_gui(f"[+] Kaydedildi: {save_path}")

    def log_gui(self, text):
        def update():
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, text + "\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        self.root.after(0, update)

if __name__ == "__main__":
    root = tk.Tk()
    app = GhostNode(root)
    root.mainloop()