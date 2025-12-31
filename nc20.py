#!/usr/bin/env python3
import wx
import socket
import json
import os
import threading
import tempfile
import shutil

# --------------- Config and constants ---------------
CONFIG_FILE = "nc20_config.json"
BUF_SIZE = 64 * 1024

LABELS = {
    "en": {
        "title": "nc20 Toolbox",
        "menu_file": "File",
        "menu_about": "About",
        "menu_exit": "Exit",
        "about_title": "About nc20 Toolbox",
        "about_text": (
            "Created by: Abolfazl Ebrahimi\n"
            "License: GPLv3\n\n"
            "This software is open-source and released under GNU GPL version 3."
        ),
        "help": "❓ Help",
        "help_title": "Help",
        "help_text": (
            "Help:\n\n"
            "Send File/Folder:\n"
            "- Enter destination IP, port, and pick a file or folder.\n"
            "- Click 'Send' to transfer. Folders are zipped automatically.\n\n"
            "Receive File/Folder:\n"
            "- Enter port. Pick a save folder (optional). Click 'Receive'.\n"
            "- Your default IP is shown to share with the sender.\n\n"
            "Accessibility:\n"
            "- All logs and help texts are ReadOnly.\n"
            "- Press Escape to close any dialog.\n"
        ),
        "log_main": "Program Log (ReadOnly):",
        "send": "📤 Send file/folder",
        "receive": "📥 Receive file/folder",
        "chat_server": "💬 Chat server",
        "chat_client": "🔗 Chat client",
        "ip": "Destination IP:",
        "port": "Port:",
        "path": "Selected path:",
        "choose_file": "Choose file",
        "choose_dir": "Choose folder",
        "send_btn": "Send",
        "save_dir": "Save folder (optional):",
        "choose_save_dir": "Choose save folder",
        "receive_btn": "Receive",
        "conn_info": "Connection info (ReadOnly):",
        "default_ip": "Default IP",
        "suggested_port": "Suggested port",
        "share_with_sender": "Share these with the sender.",
        "choose_language": "Choose language / زبان را انتخاب کنید:",
        "first_run": "First Run",
        "english": "English",
        "farsi": "فارسی",
        "errors": {
            "enter_all": "Please enter IP, port, and path.",
            "invalid_path": "Invalid path.",
            "invalid_port": "Invalid port number.",
            "no_save_yet": "No file saved yet.",
            "open_path_failed": "Failed to open save path: "
        },
        "info": {
            "listening": "Listening on port ",
            "connected": "Connected from ",
            "received_done": "Receive complete. Saved to: ",
            "send_progress": "Send: ",
            "recv_progress": "Receive: ",
            "send_done": "Send complete.",
        }
    },
    "fa": {
        "title": "جعبه ابزار nc20",
        "menu_file": "فایل",
        "menu_about": "درباره",
        "menu_exit": "خروج",
        "about_title": "درباره جعبه ابزار nc20",
        "about_text": (
            "ساخته شده توسط: ابوالفضل ابراهیمی\n"
            "لایسنس: GPLv3\n\n"
            "این نرم‌افزار متن‌باز است و تحت مجوز GNU GPL نسخه 3 منتشر شده."
        ),
        "help": "❓ راهنما",
        "help_title": "راهنما",
        "help_text": (
            "راهنما:\n\n"
            "ارسال فایل/فولدر:\n"
            "- IP مقصد، پورت را وارد کنید و فایل یا فولدر را انتخاب کنید.\n"
            "- دکمه «ارسال» را بزنید. فولدرها به‌صورت ZIP ارسال می‌شوند.\n\n"
            "دریافت فایل/فولدر:\n"
            "- پورت را وارد کنید. فولدر ذخیره اختیاری است. «دریافت» را بزنید.\n"
            "- آی‌پی دیفالت شما نشان داده می‌شود تا به ارسال‌کننده بدهید.\n\n"
            "دسترس‌پذیری:\n"
            "- همه‌ی لاگ‌ها و متن‌های راهنما ReadOnly هستند.\n"
            "- با Escape هر دیالوگ بسته می‌شود.\n"
        ),
        "log_main": "لاگ برنامه (ReadOnly):",
        "send": "📤 ارسال فایل/فولدر",
        "receive": "📥 دریافت فایل/فولدر",
        "chat_server": "💬 چت سرور",
        "chat_client": "🔗 چت کلاینت",
        "ip": "IP مقصد:",
        "port": "پورت:",
        "path": "مسیر انتخاب‌شده:",
        "choose_file": "انتخاب فایل",
        "choose_dir": "انتخاب فولدر",
        "send_btn": "ارسال",
        "save_dir": "فولدر ذخیره (اختیاری):",
        "choose_save_dir": "انتخاب فولدر ذخیره",
        "receive_btn": "دریافت",
        "conn_info": "اطلاعات اتصال (ReadOnly):",
        "default_ip": "آی‌پی دیفالت",
        "suggested_port": "پورت پیشنهادی",
        "share_with_sender": "این‌ها را به ارسال‌کننده بدهید.",
        "choose_language": "Choose language / زبان را انتخاب کنید:",
        "first_run": "اجرای اولیه",
        "english": "English",
        "farsi": "فارسی",
        "errors": {
            "enter_all": "لطفاً IP، پورت و مسیر را وارد کنید.",
            "invalid_path": "مسیر معتبر نیست.",
            "invalid_port": "مقدار پورت صحیح نیست.",
            "no_save_yet": "هنوز فایلی ذخیره نشده.",
            "open_path_failed": "خطا در باز کردن مسیر: "
        },
        "info": {
            "listening": "در حال گوش دادن روی پورت ",
            "connected": "اتصال از ",
            "received_done": "دریافت کامل شد. ذخیره در: ",
            "send_progress": "ارسال: ",
            "recv_progress": "دریافت: ",
            "send_done": "ارسال کامل شد.",
        }
    }
}

# --------------- Utilities ---------------
def get_default_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unknown"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def make_send_path(path):
    """Return (send_path, tmp_dir_to_cleanup). Zip folder if needed."""
    if os.path.isdir(path):
        base = os.path.basename(os.path.abspath(path))
        tmp_dir = tempfile.mkdtemp(prefix="nc20_")
        zip_base = os.path.join(tmp_dir, base)
        shutil.make_archive(zip_base, 'zip', path)
        return zip_base + ".zip", tmp_dir
    return path, None

# --------------- Accessible dialog base ---------------
class EscClosableDialog(wx.Dialog):
    def __init__(self, parent, title, size=(600, 400)):
        super().__init__(parent, title=title, size=size, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char)
    def _on_char(self, e):
        if e.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            e.Skip()

# --------------- Main application frame ---------------
class Nc20Main(wx.Frame):
    def __init__(self, lang):
        self.lang = lang
        super().__init__(None, title=LABELS[lang]["title"], size=(780, 460))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Menu
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        about_item = file_menu.Append(wx.ID_ABOUT, LABELS[lang]["menu_about"])
        exit_item = file_menu.Append(wx.ID_EXIT, LABELS[lang]["menu_exit"])
        menubar.Append(file_menu, LABELS[lang]["menu_file"])
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)

        # Buttons row
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_send = wx.Button(panel, label=LABELS[lang]["send"], size=(220, 46))
        btn_recv = wx.Button(panel, label=LABELS[lang]["receive"], size=(220, 46))
        btn_help = wx.Button(panel, label=LABELS[lang]["help"], size=(160, 46))
        for b in [btn_send, btn_recv, btn_help]:
            btn_row.Add(b, 0, wx.ALL, 8)
        vbox.Add(btn_row, 0, wx.ALL | wx.CENTER, 8)

        # ReadOnly main log
        vbox.Add(wx.StaticText(panel, label=LABELS[lang]["log_main"]), 0, wx.ALL, 6)
        self.status_log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(740, 280))
        vbox.Add(self.status_log, 1, wx.EXPAND | wx.ALL, 6)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

        # Bind actions
        btn_send.Bind(wx.EVT_BUTTON, self.on_send)
        btn_recv.Bind(wx.EVT_BUTTON, self.on_recv)
        btn_help.Bind(wx.EVT_BUTTON, self.on_help)

    # -------- Menu: About --------
    def on_about(self, evt):
        wx.MessageDialog(
            self,
            LABELS[self.lang]["about_text"],
            LABELS[self.lang]["about_title"],
            wx.OK | wx.ICON_INFORMATION
        ).ShowModal()

    # -------- Help (ReadOnly) --------
    def on_help(self, evt):
        dlg = EscClosableDialog(self, LABELS[self.lang]["help_title"], size=(760, 560))
        p = wx.Panel(dlg)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.StaticText(p, label=LABELS[self.lang]["help_title"]), 0, wx.ALL, 8)
        txt = wx.TextCtrl(p, value=LABELS[self.lang]["help_text"], style=wx.TE_MULTILINE | wx.TE_READONLY, size=(720, 460))
        s.Add(txt, 1, wx.EXPAND | wx.ALL, 8)
        p.SetSizer(s)
        dlg.ShowModal()
        dlg.Destroy()

    # -------- Send dialog: IP, Port, Path, Pickers, Send --------
    def on_send(self, evt):
        L = LABELS[self.lang]
        dlg = EscClosableDialog(self, L["send"], size=(760, 600))
        p = wx.Panel(dlg)
        s = wx.BoxSizer(wx.VERTICAL)

        # Editable fields
        s.Add(wx.StaticText(p, label=L["ip"]), 0, wx.ALL, 6)
        ip_txt = wx.TextCtrl(p, value="")
        s.Add(ip_txt, 0, wx.EXPAND | wx.ALL, 6)

        s.Add(wx.StaticText(p, label=L["port"]), 0, wx.ALL, 6)
        port_txt = wx.TextCtrl(p, value="9000")
        s.Add(port_txt, 0, wx.EXPAND | wx.ALL, 6)

        s.Add(wx.StaticText(p, label=L["path"]), 0, wx.ALL, 6)
        path_txt = wx.TextCtrl(p, value="")
        s.Add(path_txt, 0, wx.EXPAND | wx.ALL, 6)

        # Pickers and action
        row = wx.BoxSizer(wx.HORIZONTAL)
        btn_file = wx.Button(p, label=L["choose_file"])
        btn_dir = wx.Button(p, label=L["choose_dir"])
        btn_do = wx.Button(p, label=L["send_btn"])
        row.Add(btn_file, 0, wx.ALL, 4)
        row.Add(btn_dir, 0, wx.ALL, 4)
        row.Add(btn_do, 0, wx.ALL, 4)
        s.Add(row, 0, wx.ALL, 6)

        # ReadOnly log
        s.Add(wx.StaticText(p, label=L["log_main"]), 0, wx.ALL, 6)
        log = wx.TextCtrl(p, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(720, 340))
        s.Add(log, 1, wx.EXPAND | wx.ALL, 6)

        p.SetSizer(s)

        def pick_file(e):
            with wx.FileDialog(dlg, L["choose_file"], wildcard="All files (*.*)|*.*",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
                if fd.ShowModal() == wx.ID_OK:
                    path_txt.SetValue(fd.GetPath())

        def pick_dir(e):
            with wx.DirDialog(dlg, L["choose_dir"]) as dd:
                if dd.ShowModal() == wx.ID_OK:
                    path_txt.SetValue(dd.GetPath())

        btn_file.Bind(wx.EVT_BUTTON, pick_file)
        btn_dir.Bind(wx.EVT_BUTTON, pick_dir)

        def start_send(e):
            ip = ip_txt.GetValue().strip()
            port_s = port_txt.GetValue().strip()
            path = path_txt.GetValue().strip()

            if not ip or not port_s or not path:
                log.AppendText(L["errors"]["enter_all"] + "\n")
                return
            if not os.path.exists(path):
                log.AppendText(L["errors"]["invalid_path"] + "\n")
                return
            try:
                port = int(port_s)
            except:
                log.AppendText(L["errors"]["invalid_port"] + "\n")
                return

            threading.Thread(
                target=self._send_impl,
                args=(ip, port, path, log, L),
                daemon=True
            ).start()

        btn_do.Bind(wx.EVT_BUTTON, start_send)

        dlg.ShowModal()
        dlg.Destroy()

    def _send_impl(self, ip, port, path, log, L):
        send_path, tmp_dir = make_send_path(path)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            size = os.path.getsize(send_path)
            header = f"{os.path.basename(send_path)}|{size}\n".encode()
            s.sendall(header)

            sent = 0
            with open(send_path, "rb") as f:
                while True:
                    chunk = f.read(BUF_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)
                    sent += len(chunk)
                    pct = int((sent * 100) / size) if size else 100
                    wx.CallAfter(log.AppendText, f"{L['info']['send_progress']}{pct}%\n")

            s.close()
            wx.CallAfter(log.AppendText, L["info"]["send_done"] + "\n")
        except Exception as e:
            wx.CallAfter(log.AppendText, f"Error: {e}\n")
        finally:
            if tmp_dir and os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    # -------- Receive dialog: Port, Optional save folder, Receive --------
    def on_recv(self, evt):
        L = LABELS[self.lang]
        dlg = EscClosableDialog(self, L["receive"], size=(760, 640))
        p = wx.Panel(dlg)
        s = wx.BoxSizer(wx.VERTICAL)

        # Connection info (ReadOnly)
        ip = get_default_ip()
        info_text = (
            f"{L['conn_info']}\n"
            f"{L['default_ip']}: {ip}\n{L['suggested_port']}: 9000\n"
            f"{L['share_with_sender']}"
        )
        info = wx.TextCtrl(p, value=info_text, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(720, 120))
        s.Add(info, 0, wx.EXPAND | wx.ALL, 8)

        # Inputs
        s.Add(wx.StaticText(p, label=L["port"]), 0, wx.ALL, 6)
        port_txt = wx.TextCtrl(p, value="9000")
        s.Add(port_txt, 0, wx.EXPAND | wx.ALL, 6)

        s.Add(wx.StaticText(p, label=L["save_dir"]), 0, wx.ALL, 6)
        out_txt = wx.TextCtrl(p, value="")
        s.Add(out_txt, 0, wx.EXPAND | wx.ALL, 6)

        row = wx.BoxSizer(wx.HORIZONTAL)
        btn_choose = wx.Button(p, label=L["choose_save_dir"])
        btn_recv = wx.Button(p, label=L["receive_btn"])
        btn_open = wx.Button(p, label=("Open save folder" if self.lang == "en" else "باز کردن فولدر ذخیره"))
        row.Add(btn_choose, 0, wx.ALL, 4)
        row.Add(btn_recv, 0, wx.ALL, 4)
        row.Add(btn_open, 0, wx.ALL, 4)
        s.Add(row, 0, wx.ALL, 6)

        # ReadOnly log
        s.Add(wx.StaticText(p, label=L["log_main"]), 0, wx.ALL, 6)
        log = wx.TextCtrl(p, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(720, 360))
        s.Add(log, 1, wx.EXPAND | wx.ALL, 8)

        p.SetSizer(s)

        state = {"last_outpath": ""}

        def pick_save(e):
            with wx.DirDialog(dlg, L["choose_save_dir"]) as dd:
                if dd.ShowModal() == wx.ID_OK:
                    out_txt.SetValue(dd.GetPath())

        def start_recv(e):
            port_s = port_txt.GetValue().strip()
            outdir = out_txt.GetValue().strip() or "."
            try:
                port = int(port_s)
            except:
                log.AppendText(L["errors"]["invalid_port"] + "\n")
                return

            threading.Thread(
                target=self._recv_impl,
                args=(port, outdir, log, state, L),
                daemon=True
            ).start()

        def open_last(e):
            outpath = state["last_outpath"]
            if not outpath:
                log.AppendText(L["errors"]["no_save_yet"] + "\n")
                return
            folder = os.path.dirname(outpath) if os.path.isfile(outpath) else outpath
            try:
                if wx.Platform == "__WXMSW__":
                    os.startfile(folder)
                elif wx.Platform == "__WXMAC__":
                    import subprocess
                    subprocess.call(["open", folder])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", folder])
            except Exception as ex:
                log.AppendText(L["errors"]["open_path_failed"] + str(ex) + "\n")

        btn_choose.Bind(wx.EVT_BUTTON, pick_save)
        btn_recv.Bind(wx.EVT_BUTTON, start_recv)
        btn_open.Bind(wx.EVT_BUTTON, open_last)

        dlg.ShowModal()
        dlg.Destroy()

    def _recv_impl(self, port, outdir, log, state, L):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("", port))
            srv.listen(1)
            wx.CallAfter(log.AppendText, L["info"]["listening"] + f"{port}...\n")
            conn, addr = srv.accept()
            wx.CallAfter(log.AppendText, L["info"]["connected"] + f"{addr[0]}\n")

            # Read header "name|size\n"
            header = b""
            while b"\n" not in header:
                chunk = conn.recv(64)
                if not chunk:
                    break
                header += chunk
            if b"\n" not in header:
                raise RuntimeError("Header not received.")

            name, size_s = header.decode().strip().split("|", 1)
            size = int(size_s)
            outpath = os.path.join(outdir, name)

            # Receive body
            recvd = 0
            with open(outpath, "wb") as f:
                while recvd < size:
                    data = conn.recv(BUF_SIZE)
                    if not data:
                        break
                    f.write(data)
                    recvd += len(data)
                    pct = int((recvd * 100) / size) if size else 100
                    wx.CallAfter(log.AppendText, f"{L['info']['recv_progress']}{pct}%\n")

            conn.close()
            srv.close()
            state["last_outpath"] = outpath
            wx.CallAfter(log.AppendText, L["info"]["received_done"] + outpath + "\n")
        except Exception as e:
            wx.CallAfter(log.AppendText, f"Error: {e}\n")

# --------------- Bootstrap: language selection on first run ---------------
if __name__ == "__main__":
    app = wx.App(False)
    cfg = load_config()
    if not cfg or "language" not in cfg:
        dlg = wx.SingleChoiceDialog(
            None,
            LABELS["en"]["choose_language"],
            LABELS["en"]["first_run"],
            [LABELS["en"]["english"], LABELS["en"]["farsi"]],
        )
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetStringSelection()
        else:
            sel = LABELS["en"]["english"]
        dlg.Destroy()
        lang = "fa" if sel == LABELS["en"]["farsi"] else "en"
        save_config({"language": lang})
        Nc20Main(lang)
    else:
        Nc20Main(cfg["language"])
    app.MainLoop()

