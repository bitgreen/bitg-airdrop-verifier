import sys
import os
from sys import exit
from tkinter import ttk
from tkmacosx import Button
from utils import rpc_module, library, walletlib
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
from mnemonic import Mnemonic
import click
import requests
from dotenv import load_dotenv
import webbrowser
import threading

extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))

try:
    import tkinter as tk  # python 3
    from tkinter import font as tkfont  # python 3
except ImportError:
    import Tkinter as tk  # python 2
    import tkFont as tkfont  # python 2

rpc = rpc_module.Rpc()


class Signer:
    def __init__(self):
        self.address_list = {}

    def get_addresses(self):
        for addr in rpc.listaddressgroupings():
            if len(addr) > 1:
                for addr in addr:
                    address_data = rpc.getaddrinfo(addr[0])
                    self.address_list.update({address_data['scriptPubKey']: {
                        'addr': addr[0],
                        'pubkey': address_data['pubkey'],
                        'sig': ''
                    }
                    })
            else:
                address_data = rpc.getaddrinfo(addr[0][0])
                self.address_list.update({address_data['scriptPubKey']: {
                    'addr': addr[0][0],
                    'pubkey': address_data['pubkey'],
                    'sig': ''
                }
                })

    def private_keys(self):
        # iterate through each public key and dump the private key that corresponds
        # update dictionary 'address_list' with the private key inside ['sig'] to be later used when
        # signing a message proving ownership of address
        for key, value in self.address_list.items():
            self.address_list.update({key: {
                'addr': value['addr'],
                'pubkey': value['pubkey'],
                'sig': rpc.dumpprivkey(value['addr'])
            }
            })

    def signmessage(self, message):
        for key, value in self.address_list.items():
            self.address_list.update({key: {
                'addr': value['addr'],
                'pubkey': value['pubkey'],
                'sig': rpc.signmessagewithprivkey(value['sig'], message)
            }
            })


class Wallet:
    def __init__(self):
        self.directory = ''

    def isLocked(self):
        # check if wallet is unlocked
        wlock = rpc.isWalletlocked()

        if 'unlocked_until' in wlock:
            if wlock['unlocked_until'] == 0:
                # unlock wallet
                return True
            else:
                return False
        else:
            return False

    def unlock(self, passwd=None):
        if self.isLocked():
            if rpc.walletpassphrase(passwd, 900) is None:
                messagebox.showinfo('message', 'Wallet is locked, please unlock using passphrase.')
            else:
                return True
        else:
            return True


# Handle grayed out placeholders inside textfield.
def handle_focus_in(event, message, obj_txtfield):
    if obj_txtfield.get() == message:
        obj_txtfield.delete(0, tk.END)  # delete all the text in the entry
        if message == 'Wallet password':
            obj_txtfield.config(fg='black', show="*")
        obj_txtfield.insert(0, '')  # Insert blank for user input


def handle_focus_out(event, message, obj_txtfield):
    if obj_txtfield.get() == '':
        obj_txtfield.delete(0, tk.END)
        obj_txtfield.config(fg='gray', show="")
        obj_txtfield.insert(0, message)


def resourcePath(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relativePath)


class AirdropApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.operating_system = os.name

        if self.operating_system != 'posix':
            # Windows font specifications
            self.title_font = tkfont.Font(family='Calibri light', size=24, weight="normal")
            self.title_font_step = tkfont.Font(family='Calibri light', size=11, weight="bold")
            self.text_style = tkfont.Font(family='Calibri light', size=11, weight="normal")
            self.text_style_small = tkfont.Font(family='Calibri light', size=9, weight="normal")
            self.text_style_bold = tkfont.Font(family='Calibri Light', size=11, weight="bold")
        else:
            # Mac OS font specifications
            self.title_font = tkfont.Font(family='Calibri light', size=24, weight="normal")
            self.title_font_step = tkfont.Font(family='Calibri light', size=12, weight="bold")
            self.text_style = tkfont.Font(family='Calibri light', size=12, weight="normal")
            self.text_style_small = tkfont.Font(family='Calibri light', size=10, weight="normal")
            self.text_style_bold = tkfont.Font(family='Calibri Light', size=12, weight="bold")

        self.shared_data = {
            "key_pairs": [],
            "wallet_key_pairs": [],
            "directory": tk.StringVar(),
            "password": tk.StringVar(),
            "substrate-addr": tk.StringVar(),
            "seed-phrase": tk.StringVar(),
            "tos-accepted": tk.BooleanVar(),
            "user-ready": tk.BooleanVar()
        }

        self.operating_system = os.name

        # Application header
        header_img = Image.open(resourcePath('header.jpg'))
        header = ImageTk.PhotoImage(header_img)

        label = tk.Label(self, image=header, borderwidth=0, highlightthickness=0)
        label.image = header
        label.pack(side="top", fill="y", anchor=tk.NW)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=11)

        self.frames = {}
        for F in (StartPage, WalletData, SeedPhrase, VerifyOwnership, SubmitAirdrop, KYC, Finished):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.configure(bg='#FFFFFF')
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        frame = self.frames[page_name]
        frame.tkraise()

    def get_page(self, page_class):
        return self.frames[page_class]


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Airdrop logo
        airdrop_logo_img = Image.open(resourcePath('icons_BitGreen Airdrop.jpg'))
        airdrop_logo_img = airdrop_logo_img.resize((200, 200), Image.Resampling.LANCZOS)
        airdrop_logo = ImageTk.PhotoImage(airdrop_logo_img)

        # Call .jpg image into PhotoImage
        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.Resampling.LANCZOS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        airdrop_logo_lbl = tk.Label(self, image=airdrop_logo, borderwidth=0, highlightthickness=0)
        airdrop_logo_lbl.image = airdrop_logo
        airdrop_logo_lbl.pack(side="top", fill="y", anchor=tk.SW, padx=50, pady=45)

        if controller.operating_system != 'posix':
            # Start - WINDOWS
            self.start_btn = tk.Button(self, text="START", font=controller.text_style_bold,
                                       fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                       height=1, width=14, pady=4, relief=tk.GROOVE, border=0, cursor='hand2',
                                       bg='#9e04c4', highlightbackground='#9e04c4')
            self.start_btn.place(x=85, y=275)

            self.start_btn_fake = tk.Button(self, text="START", font=controller.text_style_bold, state=tk.DISABLED,
                                            fg='#FFFFFF', disabledforeground='#FFFFFF',
                                            height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                            bg='#7c7c7d', highlightbackground='#7c7c7d')
            self.start_btn_fake.place(x=85, y=275)
        else:
            # Start - POSIX
            self.start_btn = Button(self, text='START', font=controller.text_style_bold,
                                    fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                    height=40, width=130, pady=4, cursor='hand2',
                                    activebackground=('#9e04c4', '#9e04c4'),
                                    activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.start_btn.place(x=85, y=275)

            self.start_btn_fake = Button(self, text="START", font=controller.text_style_bold, state=tk.DISABLED,
                                         fg='#FFFFFF', disabledforeground='#FFFFFF',
                                         height=40, width=130, pady=4, border=0,
                                         activebackground='#7c7c7d',
                                         activeforeground='#FFFFFF', bg='#7c7c7d', borderless=True)
            self.start_btn_fake.place(x=85, y=275)

        self.startpage_pg01 = tk.Label(self, text="""This tool will guide you through the process of claiming the Bitgreen Airdrop. You will require the following:
        • wallet.dat from Bitcoin Green Desktop wallet and/or seed phrase from Mobile wallet
        • polkadot.js wallet extension (see Airdrop Announcement)
        • documents for Know Your Customer (KYC) processing
        """,
                                       font=controller.text_style, justify=tk.LEFT,
                                       wraplength=520, bg='#FFFFFF')
        self.startpage_pg01.place(x=265, y=15)

        self.announcement01 = tk.Label(self, text="Airdrop Announcement", bg='#FFFFFF',
                                       pady='0', padx='0',
                                       fg='#9e04c4', cursor="hand2", font=controller.text_style)
        self.announcement01.bind("<Button-1>",
                                 lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/ann"))
        if sys.platform == "linux":
            self.announcement01.place(x=582, y=91)
        elif sys.platform == "darwin":
            self.announcement01.place(x=490, y=61)
        else:
            self.announcement01.place(x=496, y=88)

        self.startpage_pg02 = tk.Label(self,
                                       text="""Note the snapshot date for address balances is block 483250 which occured on October 26th 2021. Only balances that were in mobile or the desktop wallet at this time can be considered for the airdrop. For additional information on this refert to the Airdrop Announcement.""",
                                       font=controller.text_style, justify=tk.LEFT,
                                       wraplength=520, bg='#FFFFFF', fg='#E80000')
        self.startpage_pg02.place(x=265, y=145)

        self.announcement02 = tk.Label(self, text="Airdrop Announcement", bg='#FFFFFF',
                                       fg='#850303', cursor="hand2", font=controller.text_style)
        self.announcement02.place(x=264, y=221)
        self.announcement02.bind("<Button-1>",
                                 lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/ann"))

        self.before_you_begin = tk.Label(self, text="Before you begin", fg='#9e04c4', bg='#FFFFFF',
                                         font=controller.title_font)
        self.before_you_begin.place(x=265, y=250)

        self.c1 = tk.Checkbutton(self, text='I acknowledge Bitgreen Airdrop Standard Terms and Conditions.',
                                 variable=controller.shared_data["tos-accepted"], command=self.agree_tos,
                                 onvalue=True, offvalue=False, font=controller.text_style, borderwidth=0,
                                 bg="#fff", activebackground="#fff",
                                 highlightthickness=0, relief=tk.GROOVE)
        self.c1.place(x=250, y=300)
        self.terms_and_conditions = tk.Label(self, text="Terms and Conditions", bg='#FFFFFF',
                                             fg='#9e04c4', cursor="hand2", font=controller.text_style)
        self.terms_and_conditions.bind("<Button-1>",
                                       lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/tos"))
        if sys.platform == "linux":
            self.terms_and_conditions.place(x=608, y=299)
        elif sys.platform == "darwin":
            self.terms_and_conditions.place(x=506, y=298)
        else:
            self.terms_and_conditions.place(x=516, y=299)

        self.c2 = tk.Checkbutton(self, text='I created a Substrate address and read the announcement.',
                                 variable=controller.shared_data["user-ready"], command=self.agree_tos,
                                 onvalue=True, offvalue=False, font=controller.text_style, borderwidth=0,
                                 bg="#fff", activebackground="#fff",
                                 highlightthickness=0, relief=tk.GROOVE)
        self.c2.place(x=250, y=330)
        self.announcement = tk.Label(self, text="announcement", bg='#FFFFFF',
                                     fg='#9e04c4', cursor="hand2", font=controller.text_style)
        self.announcement.bind("<Button-1>",
                               lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/ann"))
        if sys.platform == "linux":
            self.announcement.place(x=624, y=329)
        elif sys.platform == "darwin":
            self.announcement.place(x=514, y=328)
        else:
            self.announcement.place(x=524, y=329)

    def agree_tos(self):
        accepted = self.controller.shared_data["tos-accepted"].get()
        ready = self.controller.shared_data["user-ready"].get()

        if accepted and ready:
            self.start_btn_fake.place_forget()
        else:
            if self.controller.operating_system != 'posix':
                self.start_btn_fake.place(x=85, y=275)
            else:
                self.start_btn_fake.place(x=85, y=275)

def menu_items(self, controller, active_step):
    active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
    active_dot_img = active_dot_img.resize((30, 30), Image.Resampling.LANCZOS)
    active_dot_logo = ImageTk.PhotoImage(active_dot_img)

    dot_img = Image.open(resourcePath('icons_Dot.jpg'))
    dot_img = dot_img.resize((30, 30), Image.Resampling.LANCZOS)
    dot_logo = ImageTk.PhotoImage(dot_img)

    tick_img = Image.open(resourcePath('icons_Tick.jpg'))
    tick_img = tick_img.resize((30, 30), Image.Resampling.LANCZOS)
    tick_logo = ImageTk.PhotoImage(tick_img)

    wallet_data_lbl = tk.Label(self, text="Desktop Wallet", bg='#FFFFFF', font=controller.text_style)
    wallet_data_lbl.place(x=90, y=50)
    if active_step == 1:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 1:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=45)

    seed_phrase_lbl = tk.Label(self, text="Mobile Wallet", bg='#FFFFFF', font=controller.text_style)
    seed_phrase_lbl.place(x=90, y=100)
    if active_step == 2:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 2:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=95)

    verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='#FFFFFF', font=controller.text_style)
    verify_ownership_lbl.place(x=90, y=150)
    if active_step == 3:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 3:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=145)

    submit_to_airdrop_lbl = tk.Label(self, text="Sign and Submit", bg='#FFFFFF', font=controller.text_style)
    submit_to_airdrop_lbl.place(x=90, y=200)
    if active_step == 4:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 4:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=195)

    kyc_lbl = tk.Label(self, text="KYC", bg='#FFFFFF', font=controller.text_style)
    kyc_lbl.place(x=90, y=250)
    if active_step == 5:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 5:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=245)

    finished_lbl = tk.Label(self, text="Finished", bg='#FFFFFF', font=controller.text_style)
    finished_lbl.place(x=90, y=300)
    if active_step == 6:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 6:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=295)


class WalletData(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.wallet = Wallet()

        self.folder_path = tk.StringVar()
        self.entry_content = tk.StringVar()

        # Call .jpg image into PhotoImage
        icon_folder_img = Image.open(resourcePath('icons_Folder.jpg'))
        icon_folder_img = icon_folder_img.resize((30, 30), Image.Resampling.LANCZOS)
        icon_folder_logo = ImageTk.PhotoImage(icon_folder_img)

        # Call .jpg image into PhotoImage
        icon_key_img = Image.open(resourcePath('icons_Key.jpg'))
        icon_key_img = icon_key_img.resize((30, 30), Image.Resampling.LANCZOS)
        icon_key_logo = ImageTk.PhotoImage(icon_key_img)

        menu_items(self, controller, 1)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Wallet Data ############
        self.step_title = tk.Label(self, text="Desktop Wallet", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 1", fg='#9e04c4', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=80)
        self.step_title.place(x=270, y=40)
        ######################################

        self.walletdata_pg01 = tk.Label(self,
                                        text="""If you did not have a desktop wallet click next to skip this step.""",
                                        font=controller.text_style, justify=tk.LEFT,
                                        wraplength=500, bg='#FFFFFF', fg='#E80000')
        self.walletdata_pg01.place(x=270, y=110)

        self.walletdata_pg02 = tk.Label(self,
                                        text="""Please make a backup of your wallet.dat file before you continue to use for this process and copy it to a different location. You might have to activate hidden files to reach it.""",
                                        font=controller.text_style, justify=tk.LEFT,
                                        wraplength=500, bg='#FFFFFF')
        self.walletdata_pg02.place(x=270, y=155)

        if sys.platform == "linux":
            self.walletdata_pg03 = tk.Label(self,
                                            text="""Default path: ~/.bitgreen/""",
                                            font=controller.text_style_small, justify=tk.LEFT,
                                            wraplength=500, bg='#FFFFFF')
            self.walletdata_pg03.place(x=270, y=340)
        elif sys.platform == "darwin":
            self.walletdata_pg03 = tk.Label(self,
                                            text="""Default path: ~/Library/Application Support/Bitgreen/""",
                                            font=controller.text_style_small, justify=tk.LEFT,
                                            wraplength=500, bg='#FFFFFF')
            self.walletdata_pg03.place(x=270, y=340)
        else:
            self.walletdata_pg03 = tk.Label(self,
                                            text="""Go to Start -> Run and enter \"%APPDATA%\Bitgreen\"""",
                                            font=controller.text_style_small, justify=tk.LEFT,
                                            wraplength=500, bg='#FFFFFF')
            self.walletdata_pg03.place(x=270, y=340)

        icon_folder = tk.Label(self, image=icon_folder_logo, borderwidth=0, highlightthickness=0)
        icon_folder.image = icon_folder_logo
        icon_folder.place(x=270, y=235)

        self.walletdir_txtfld = tk.Entry(self, textvariable=controller.shared_data["directory"], bd=2, cursor="hand2",
                                         relief=tk.GROOVE, font=controller.text_style)
        self.walletdir_txtfld.config(fg='grey')
        self.walletdir_txtfld.insert(0, "Wallet file")
        self.walletdir_txtfld.bind("<Button-1>", self.walletdir)
        self.walletdir_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Wallet file", self.walletdir_txtfld))
        self.walletdir_txtfld.bind("<FocusOut>",
                                   lambda event, message="Wallet password": handle_focus_out(event, "Wallet file",
                                                                                             self.walletdir_txtfld))
        self.walletdir_txtfld.place(x=310, y=235, width=452, height=35)

        icon_key = tk.Label(self, image=icon_key_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_key_logo
        icon_key.place(x=270, y=280)

        self.passwd_txtfld = tk.Entry(self, textvariable=controller.shared_data["password"], bd=2,
                                      relief=tk.GROOVE, font=controller.text_style)
        self.passwd_txtfld.config(fg='grey')
        self.passwd_txtfld.insert(0, "Wallet password")
        self.passwd_txtfld.bind("<FocusIn>",
                                lambda event,: handle_focus_in(event, "Wallet password", self.passwd_txtfld))
        self.passwd_txtfld.bind("<FocusOut>",
                                lambda event, message="Wallet password": handle_focus_out(event, "Wallet password",
                                                                                          self.passwd_txtfld))
        self.passwd_txtfld.place(x=310, y=280, width=452, height=35)

        if controller.operating_system != 'posix':
            # Start - WINDOWS
            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=self.read_wallet, cursor="hand2",
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.next_btn.place(x=630, y=330)
        else:
            # Next - POSIX
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=self.read_wallet, cursor="hand2",
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.next_btn.place(x=630, y=330)

    def walletdir(self, event):
        # Allow user to select a directory and store it in global var
        # called folder_path
        global folder_path
        home = os.path.expanduser('~')
        # filename = filedialog.askdirectory(initialdir=home)
        filename = filedialog.askopenfilename(filetypes=[("Wallet file", "*.dat")], initialdir=home)
        self.controller.shared_data["directory"].set(filename)

    def msgbox(self, title, messge):
        messagebox.showinfo(title, messge)

    def read_wallet(self):
        password = self.controller.shared_data["password"].get()
        directory = self.controller.shared_data["directory"].get()

        self.controller.shared_data["wallet_key_pairs"] = []

        w = False
        if os.path.isfile(f"{directory}"):
            w = walletlib.Walletdat.load(f"{directory}")

        if w:
            if password != "" and password != "Wallet password":
                w.parse(passphrase=str(password))
            else:
                w.parse()
            click.echo("Found {} keypairs and {} transactions".format(
                len(w.keypairs), len(w.txes)))

            if password != "" and password != "Wallet password" and len(w.keypairs) == 0:
                messagebox.showinfo("Error", f"Invalid password!")
                return

            if len(w.keypairs) > 0:
                all_keys = w.dump_keys()
                for keypair in all_keys:
                    if 'private_key' in keypair:
                        self.controller.shared_data["wallet_key_pairs"].append(
                            {'private_key': keypair['private_key'], 'address': keypair['public_key']})

            if len(self.controller.shared_data["wallet_key_pairs"]) == 0:
                messagebox.showinfo("Error", f"Invalid password!")
                return

        if directory != 'Wallet file' and len(self.controller.shared_data["wallet_key_pairs"]) == 0:
            messagebox.showinfo("Error", f"Wallet file not found!.")
            return

        self.controller.show_frame("SeedPhrase")


class SeedPhrase(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.wallet = Wallet()

        self.folder_path = tk.StringVar()
        self.entry_content = tk.StringVar()

        menu_items(self, controller, 2)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Seed Phrase ############
        self.step_title = tk.Label(self, text="Mobile Wallet", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 2", fg='#9e04c4', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=80)
        self.step_title.place(x=270, y=40)
        ######################################


        self.seed_pg01 = tk.Label(self,
                                  text="""If you did not have a mobile wallet click next to skip this step.""",
                                  font=controller.text_style, justify=tk.LEFT,
                                  wraplength=500, bg='#FFFFFF', fg='#E80000')
        self.seed_pg01.place(x=270, y=110)

        self.seed_pg02 = tk.Label(self, text="Please enter your 12 word long seed phrase that you got when you created your mobile wallet.",
                                  font=controller.text_style, justify=tk.LEFT,
                                  wraplength=500, bg='#FFFFFF')
        self.seed_pg02.place(x=270, y=140)

        self.seed_txtfld = tk.Entry(self, textvariable=controller.shared_data["seed-phrase"],
                                    bd=2, relief=tk.GROOVE, font=controller.text_style)
        self.seed_txtfld.config(fg='grey')
        self.seed_txtfld.insert(0, "Seed Phrase")
        self.seed_txtfld.bind("<FocusIn>",
                              lambda event,: handle_focus_in(event, "Seed Phrase", self.seed_txtfld))
        self.seed_txtfld.bind("<FocusOut>", lambda event, message="Seed Phrase": handle_focus_out(event, "Seed Phrase",
                                                                                                  self.seed_txtfld))
        self.seed_txtfld.place(x=270, y=285, width=492, height=35)

        if controller.operating_system != 'posix':
            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=self.check_seed, cursor="hand2",
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.next_btn.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.back_btn.place(x=270, y=330)
        else:
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=self.check_seed, cursor="hand2",
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.next_btn.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold, cursor="hand2",
                                   fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.back_btn.place(x=270, y=330)

    def check_seed(self):
        seed_phrase = self.controller.shared_data["seed-phrase"]

        self.controller.shared_data["key_pairs"] = self.controller.shared_data["wallet_key_pairs"]

        if seed_phrase.get() != "" and seed_phrase.get() != "Seed Phrase":
            mnemon = Mnemonic('english')
            # validate seed phrase
            if mnemon.check(seed_phrase.get()):
                seed = mnemon.to_seed(seed_phrase.get())

                private_key = library.seed_to_wif(seed)

                self.controller.shared_data["key_pairs"].append({'private_key': private_key})
            else:
                messagebox.showinfo("Error", f"Invalid seed phrase!")
                return

        if len(self.controller.shared_data["key_pairs"]) > 0:
            self.controller.show_frame("VerifyOwnership")
        else:
            messagebox.showinfo("Error", f"No accounts found. Please select wallet.dat file or enter your seed phrase.")
            self.controller.show_frame("WalletData")


class VerifyOwnership(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        icon_wallet_img = Image.open(resourcePath('icons_Substrate.jpg'))
        icon_wallet_img = icon_wallet_img.resize((30, 30), Image.Resampling.LANCZOS)
        icon_wallet_logo = ImageTk.PhotoImage(icon_wallet_img)

        menu_items(self, controller, 3)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Verify Ownership", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 3", fg='#9e04c4', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=80)
        self.step_title.place(x=270, y=40)
        ######################################

        self.verify_pg01 = tk.Label(self, text="""This step involves specifying the substrate address you created on the new blockchain. Each address associated in your wallet will be signed with the substrate address on the next step. This both proves that your substrate address 'owns' the Bitcoin Green addresses on the old blockchain, and in the submission to the airdrop will authorise the equivilent funds to be sent to your Substrate address on the new blockchain.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=520, bg='#FFFFFF')
        self.verify_pg01.place(x=270, y=110)

        self.verify_pg02 = tk.Label(self, text="""If you did not yet create a Substrate address refer to the
Airdrop announcement on how to create one.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=520, bg='#FFFFFF', fg='#E80000')
        self.verify_pg02.place(x=270, y=246)

        self.verify_pg03 = tk.Label(self, text="Airdrop Announcement", bg='#FFFFFF',
                                    fg='#850303', cursor="hand2", font=controller.text_style)
        self.verify_pg03.bind("<Button-1>",
                              lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/ann"))
        if sys.platform == "linux":
            self.verify_pg03.place(x=270, y=265)
        elif sys.platform == "darwin":
            self.verify_pg03.place(x=267, y=262)
        else:
            self.verify_pg03.place(x=270, y=264)

        self.substrate_txtfld = tk.Entry(self, textvariable=controller.shared_data["substrate-addr"],
                                         bd=2, relief=tk.GROOVE, font=controller.text_style)
        self.substrate_txtfld.config(fg='grey')
        self.substrate_txtfld.insert(0, "Substrate address")
        self.substrate_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Substrate address", self.substrate_txtfld))
        self.substrate_txtfld.bind("<FocusOut>", lambda event, message="Substrate address": handle_focus_out(event,
                                                                                                             "Substrate address",
                                                                                                             self.substrate_txtfld))
        self.substrate_txtfld.place(x=310, y=290, width=452, height=35)

        icon_key = tk.Label(self, image=icon_wallet_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_wallet_logo
        icon_key.place(x=270, y=293)

        if controller.operating_system != 'posix':
            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=self.verify_substrate_address,
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.next_btn.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=lambda: controller.show_frame("SeedPhrase"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.back_btn.place(x=270, y=330)
        else:
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold, cursor="hand2",
                                   fg='#FFFFFF', command=self.verify_substrate_address,
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.next_btn.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold, cursor="hand2",
                                   fg='#FFFFFF', command=lambda: controller.show_frame("SeedPhrase"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.back_btn.place(x=270, y=330)

    def verify_substrate_address(self):
        message = self.controller.shared_data["substrate-addr"].get()

        if message == 'Substrate address' or message == '':
            messagebox.showinfo("Error", "You must specify a valid substrate address.")
            return

        url = os.getenv('SERVER_API_URL') + '/validate-substrate-address'
        r = requests.post(url, json={'address': message})
        result = r.json()
        if result['status']:
            self.controller.show_frame("SubmitAirdrop")
        else:
            messagebox.showinfo("Error", "You must specify a valid substrate address.")


class SubmitAirdrop(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        menu_items(self, controller, 4)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        self.step_title = tk.Label(self, text="Sign and Submit", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 4", fg='#9e04c4', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=80)
        self.step_title.place(x=270, y=40)

        self.submit_pg01 = tk.Label(self,
                                    text="""When you are ready, press 'SIGN' to cryptographically sign each address with the specified substrate address to prove ownership.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.submit_pg01.place(x=270, y=100)

        self.submit_pg02 = tk.Label(self,
                                    text="""After clicking submit all found addresses will be checked even ones you never used. This process can take a while and the app might be unresponsive in the meantime.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.submit_pg02.place(x=270, y=190)

        if controller.operating_system != 'posix':
            self.submit_btn = tk.Button(self, text="SIGN", font=controller.text_style_bold,
                                        fg='#FFFFFF', command=self.submit2airdrop, cursor="hand2",
                                        width=14, pady=2, relief=tk.GROOVE, border=0,
                                        bg='#9e04c4', highlightbackground='#9e04c4')
            self.submit_btn.place(x=630, y=290)

            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=lambda: controller.show_frame("KYC"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.next_btn.place(x=630, y=330)

            self.next_btn_fake = tk.Button(self, text="NEXT", font=controller.text_style_bold, state=tk.DISABLED,
                                           fg='#FFFFFF', disabledforeground='#FFFFFF',
                                           height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                           bg='#7c7c7d', highlightbackground='#7c7c7d')
            self.next_btn_fake.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=lambda: controller.show_frame("VerifyOwnership"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#9e04c4', highlightbackground='#9e04c4')
            self.back_btn.place(x=270, y=330)
        else:
            self.submit_btn = Button(self, text='SIGN', font=controller.text_style_bold,
                                     fg='#FFFFFF', command=self.submit2airdrop,
                                     height=40, width=130, pady=4, cursor="hand2",
                                     activebackground=('#9e04c4', '#9e04c4'),
                                     activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.submit_btn.place(x=630, y=290)

            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=lambda: controller.show_frame("KYC"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'), cursor="hand2",
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.next_btn.place(x=630, y=330)

            self.next_btn_fake = Button(self, text='NEXT', font=controller.text_style_bold,
                                        fg='#FFFFFF',
                                        height=40, width=130, pady=4, state=tk.DISABLED,
                                        activebackground=('#9e04c4', '#9e04c4'),
                                        activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.next_btn_fake.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold, cursor="hand2",
                                   fg='#FFFFFF', command=lambda: controller.show_frame("VerifyOwnership"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#9e04c4', '#9e04c4'),
                                   activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.back_btn.place(x=270, y=330)

    def submit2airdrop(self):
        message = self.controller.shared_data["substrate-addr"].get()

        if message == 'Substrate address' or message == '':
            messagebox.showinfo("Error", "You must specify a substrate address")
            return

        output = {
            'old_addresses': [],
            'substrate_address': message
        }

        for keypair in self.controller.shared_data["key_pairs"]:
            output['old_addresses'].append(library.sign_message(keypair['private_key'], message))

        output['api_secret'] = os.getenv('SERVER_API_KEY')
        url = os.getenv('SERVER_API_URL') + '/claim-addresses'
        r = requests.post(url, json=output)
        result = r.json()
        if result['status']:
            messagebox.showinfo("Information",
                                f"Successfully signed {result['signed_addresses_count']} addresses. Click Next to continue.")

            self.next_btn_fake.place_forget()
        else:
            messagebox.showinfo("Error", f"Something went wrong. Please contact us.")


class KYC(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        address = self.controller.shared_data["substrate-addr"].get()

        menu_items(self, controller, 5)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        self.step_title = tk.Label(self, text="KYC", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step_title.place(x=270, y=40)

        self.finish_pg01 = tk.Label(self,
                                    text=f"""To finish your registration you have to go through the external Know your Customer Process. Make sure that the Substrate address matches the one you previously entered in this tool""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg01.place(x=270, y=90)

        if controller.operating_system != 'posix':
            self.kyc_btn = tk.Button(self, text="KYC Start", font=controller.text_style_bold, cursor="hand2",
                                     fg='#FFFFFF', command=self.kyc_start,
                                     height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                     highlightbackground='#9e04c4', bg='#9e04c4')
            self.kyc_btn.place(x=270, y=160)
        else:
            self.kyc_btn = Button(self, text='KYC Start', font=controller.text_style_bold, cursor="hand2",
                                  fg='#FFFFFF', command=self.kyc_start,
                                  height=40, width=130, pady=4,
                                  activebackground=('#9e04c4', '#9e04c4'),
                                  activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.kyc_btn.place(x=270, y=160)

    def kyc_start(self):
        address = self.controller.shared_data["substrate-addr"].get()
        url = os.getenv('SERVER_API_URL') + '/kyc/login'
        r = requests.post(url, json={'address': address})
        result = r.json()

        if result['status']:
            self.check_kyc()

            webbrowser.open_new(result['url'])
        else:
            messagebox.showinfo('message', 'Something went wrong. Please try again or contact us.')

    def check_kyc(self):
        address = self.controller.shared_data["substrate-addr"].get()
        url = os.getenv('SERVER_API_URL') + '/kyc/check'
        r = requests.post(url, json={'address': address})
        result = r.json()

        if result['status']:
            self.controller.show_frame("Finished")
        else:
            timer = threading.Timer(5, self.check_kyc)
            timer.start()


class Finished(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        address = self.controller.shared_data["substrate-addr"].get()

        menu_items(self, controller, 6)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        self.step_title = tk.Label(self, text="Finished", fg='#9e04c4', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step_title.place(x=270, y=40)

        self.finish_pg01 = tk.Label(self,
                                    text=f"""Congratulations, you have successfully signed your Bitcoin Green address(s) with your specified substrate address.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg01.place(x=270, y=80)

        self.whatnext = tk.Label(self, text="What's next?", fg='#9e04c4', bg='#FFFFFF', font=controller.title_font)
        self.whatnext.place(x=270, y=140)

        self.finish_pg02 = tk.Label(self,
                                    text=f"""Follow Bitgreen announcements to get updates on how to credit funds to your substrate address on the new blockchain using the file generated by the airdrop tool.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg02.place(x=270, y=180)

        self.finish_pg03 = tk.Label(self,
                                    text=f"""Currently there is no way to see your combined eligible balance. This will be added to the page later. In the meantime you can check your individual addresses here.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg03.place(x=270, y=250)

        self.finish_pg04 = tk.Label(self, text="here", bg='#FFFFFF',
                                    fg='#9e04c4', cursor="hand2", font=controller.text_style)
        self.finish_pg04.bind("<Button-1>",
                              lambda e: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/explorer"))
        if sys.platform == "linux":
            self.finish_pg04.place(x=596, y=288)
        elif sys.platform == "darwin":
            self.finish_pg04.place(x=682, y=265)
        else:
            self.finish_pg04.place(x=718, y=268)

        if controller.operating_system != 'posix':
            self.checker_btn = tk.Button(self, text="CHECK ADDRESS", font=controller.text_style_bold, cursor="hand2",
                                         fg='#FFFFFF', command=lambda: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/checker"),
                                         height=1, width=21, pady=4, relief=tk.GROOVE, border=0,
                                         highlightbackground='#9e04c4', bg='#9e04c4')
            self.checker_btn.place(x=260, y=330)

            self.close_btn = tk.Button(self, text="CLOSE", font=controller.text_style_bold, cursor="hand2",
                                       fg='#FFFFFF', command=lambda: controller.destroy(),
                                       height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                       highlightbackground='#9e04c4', bg='#9e04c4')
            self.close_btn.place(x=600, y=330)
        else:
            self.checker_btn = Button(self, text='CHECK ADDRESS', font=controller.text_style_bold, cursor="hand2",
                                      fg='#FFFFFF', command=lambda: webbrowser.open_new(os.getenv('SERVER_API_URL') + "/checker"),
                                      height=40, width=195, pady=4,
                                      activebackground=('#9e04c4', '#9e04c4'),
                                      activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.checker_btn.place(x=260, y=330)

            self.close_btn = Button(self, text='CLOSE', font=controller.text_style_bold, cursor="hand2",
                                    fg='#FFFFFF', command=lambda: controller.destroy(),
                                    height=40, width=130, pady=4,
                                    activebackground=('#9e04c4', '#9e04c4'),
                                    activeforeground='#FFFFFF', bg='#9e04c4', borderless=True)
            self.close_btn.place(x=630, y=330)


def on_closing():
    if messagebox.askokcancel('Quit', 'Are you sure you want to exit?'):
        window.destroy()
        exit()


if __name__ == '__main__':
    wallet = Wallet()
    window = AirdropApplication()
    window.protocol('WM_DELETE_WINDOW', on_closing)
    window.title('Bitgreen Airdrop Verifier')
    window.geometry("800x500+10+10")
    window.resizable(False, False)
    window.mainloop()
