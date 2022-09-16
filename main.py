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
import bip32utils
import click
import requests
from dotenv import load_dotenv

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


class SwapApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.operating_system = os.name

        if self.operating_system != 'posix':
            # Windows font specifications
            self.title_font = tkfont.Font(family='Calibri light', size=24, weight="normal")
            self.title_font_step = tkfont.Font(family='Calibri light', size=11, weight="bold")
            self.text_style = tkfont.Font(family='Calibri light', size=11, weight="normal")
            self.text_style_bold = tkfont.Font(family='Calibri Light', size=11, weight="bold")
        else:
            # Mac OS font specifications
            self.title_font = tkfont.Font(family='Calibri light', size=24, weight="normal")
            self.title_font_step = tkfont.Font(family='Calibri light', size=12, weight="bold")
            self.text_style = tkfont.Font(family='Calibri light', size=12, weight="normal")
            self.text_style_bold = tkfont.Font(family='Calibri Light', size=12, weight="bold")

        self.shared_data = {
            "key_pairs": [],
            "wallet_key_pairs": [],
            "directory": tk.StringVar(),
            "password": tk.StringVar(),
            "substrate-addr": tk.StringVar(),
            "seed-phrase": tk.StringVar(),
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
        for F in (StartPage, WalletData, SeedPhrase, VerifyOwnership, SubmitSwap, Finished):
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

        # Swap logo
        swap_logo_img = Image.open(resourcePath('icons_BitGreen Swap.jpg'))
        swap_logo_img = swap_logo_img.resize((200, 200), Image.Resampling.LANCZOS)
        swap_logo = ImageTk.PhotoImage(swap_logo_img)

        # Call .jpg image into PhotoImage
        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.Resampling.LANCZOS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        swap_logo_lbl = tk.Label(self, image=swap_logo, borderwidth=0, highlightthickness=0)
        swap_logo_lbl.image = swap_logo
        swap_logo_lbl.pack(side="top", fill="y", anchor=tk.SW, padx=50, pady=45)

        if controller.operating_system != 'posix':
            # Start - WINDOWS
            self.start_btn = tk.Button(self, text="START", font=controller.text_style_bold,
                                       fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                       height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                       bg='#00A519', highlightbackground='#00A519')
            self.start_btn.place(x=85, y=275)
        else:
            # Start - POSIX
            self.start_btn = Button(self, text='START', font=controller.text_style_bold,
                                    fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                    height=40, width=130, pady=4,
                                    activebackground=('#00A519', '#00A519'),
                                    activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.start_btn.place(x=85, y=275)

        self.startpage_pg01 = tk.Label(self, text="""This tool is designed to make it easy for you to identify all addresses that exist in your current BitGreen wallet, and to prove your ownership of those addresses to submit to the swap process.

Subsequently you will receive the equivalent funds to your preferred Substrate address on the new blockchain.""",
                                       font=controller.text_style, justify=tk.LEFT,
                                       wraplength=480, bg='#FFFFFF')
        self.startpage_pg01.place(x=285, y=15, )

        self.startpage_pg02 = tk.Label(self,
                                       text="""Note the snapshot date for address balances is block XXX (or around 4th May 2021).To receive funds from the swap on the new chain, you must have had a balance at this snapshot date.""",
                                       font=controller.text_style_bold, justify=tk.LEFT,
                                       wraplength=480, bg='#FFFFFF', fg='#E80000')
        self.startpage_pg02.place(x=285, y=165, )

        self.before_you_begin = tk.Label(self, text="Before you begin", fg='#00A519', bg='#FFFFFF',
                                         font=controller.title_font)
        self.before_you_begin.place(x=285, y=250)

        if controller.operating_system != 'posix':
            self.startpage_pg03 = tk.Label(self, text="Please ensure that you already have a substrate address for "
                                                      "the new chain.", font=controller.text_style, justify=tk.LEFT,
                                           wraplength=500, bg='#FFFFFF')
            self.startpage_pg03.place(x=285, y=295)
        else:
            self.startpage_pg03 = tk.Label(self, text="Please ensure that you already have a substrate address for "
                                                      "the new chain.", font=controller.text_style, justify=tk.LEFT,
                                           wraplength=500, bg='#FFFFFF')
            self.startpage_pg03.place(x=285, y=295)


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

    wallet_data_lbl = tk.Label(self, text="Wallet data", bg='#FFFFFF', font=controller.text_style)
    wallet_data_lbl.place(x=90, y=45)
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

    seed_phrase_lbl = tk.Label(self, text="Seed Phrase", bg='#FFFFFF', font=controller.text_style)
    seed_phrase_lbl.place(x=90, y=110)
    if active_step == 2:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 2:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=110)

    verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='#FFFFFF', font=controller.text_style)
    verify_ownership_lbl.place(x=90, y=175)
    if active_step == 3:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 3:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=175)

    submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='#FFFFFF', font=controller.text_style)
    submit_to_swap_lbl.place(x=90, y=240)
    if active_step == 4:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 4:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=240)

    finished_lbl = tk.Label(self, text="Finished", bg='#FFFFFF', font=controller.text_style)
    finished_lbl.place(x=90, y=305)
    if active_step == 5:
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
    elif active_step > 5:
        dot = tk.Label(self, image=tick_logo, borderwidth=0, highlightthickness=0)
        dot.image = tick_logo
    else:
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
    dot.place(x=40, y=305)


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
        self.step_title = tk.Label(self, text="BitGreen wallet data", fg='#00A519', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 1", fg='#00A519', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.walletdata_pg01 = tk.Label(self,
                                        text="""Select the directory where your BitGreen wallet data is located. If you have encrypted your wallet, enter the password to unlock it on the next step. If you only had a mobile wallet, skip this step.""",
                                        font=controller.text_style, justify=tk.LEFT,
                                        wraplength=500, bg='#FFFFFF')
        self.walletdata_pg01.place(x=270, y=110)

        icon_folder = tk.Label(self, image=icon_folder_logo, borderwidth=0, highlightthickness=0)
        icon_folder.image = icon_folder_logo
        icon_folder.place(x=270, y=200)

        self.walletdir_txtfld = tk.Entry(self, textvariable=controller.shared_data["directory"], bd=2,
                                         relief=tk.GROOVE, font=controller.text_style)
        self.walletdir_txtfld.config(fg='grey')
        self.walletdir_txtfld.insert(0, "Wallet file")
        self.walletdir_txtfld.bind("<Button-1>", self.walletdir)
        self.walletdir_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Wallet file", self.walletdir_txtfld))
        self.walletdir_txtfld.bind("<FocusOut>",
                                   lambda event, message="Wallet password": handle_focus_out(event, "Wallet file",
                                                                                             self.walletdir_txtfld))
        self.walletdir_txtfld.place(x=310, y=200, width=452, height=35)

        icon_key = tk.Label(self, image=icon_key_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_key_logo
        icon_key.place(x=270, y=245)

        self.passwd_txtfld = tk.Entry(self, textvariable=controller.shared_data["password"], bd=2,
                                      relief=tk.GROOVE, font=controller.text_style)
        self.passwd_txtfld.config(fg='grey')
        self.passwd_txtfld.insert(0, "Wallet password")
        self.passwd_txtfld.bind("<FocusIn>",
                                lambda event,: handle_focus_in(event, "Wallet password", self.passwd_txtfld))
        self.passwd_txtfld.bind("<FocusOut>",
                                lambda event, message="Wallet password": handle_focus_out(event, "Wallet password",
                                                                                          self.passwd_txtfld))
        self.passwd_txtfld.place(x=310, y=245, width=452, height=35)

        if controller.operating_system != 'posix':
            # Start - WINDOWS
            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=self.read_wallet,
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.next_btn.place(x=630, y=330)
        else:
            # Next - POSIX
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=self.read_wallet,
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
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
        self.step_title = tk.Label(self, text="Seed Phrase", fg='#00A519', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 2", fg='#00A519', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.seed_pg01 = tk.Label(self, text="If you have wallet seed phrase, enter it here.",
                                  font=controller.text_style, justify=tk.LEFT,
                                  wraplength=500, bg='#FFFFFF')
        self.seed_pg01.place(x=270, y=110)

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
                                      fg='#FFFFFF', command=self.check_seed,
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.next_btn.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.back_btn.place(x=270, y=330)
        else:
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=self.check_seed,
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.next_btn.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=lambda: controller.show_frame("WalletData"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.back_btn.place(x=270, y=330)

    def check_seed(self):
        seed_phrase = self.controller.shared_data["seed-phrase"]

        self.controller.shared_data["key_pairs"] = self.controller.shared_data["wallet_key_pairs"]

        if seed_phrase.get() != "" and seed_phrase.get() != "Seed Phrase":
            mnemon = Mnemonic('english')
            # validate seed phrase
            if mnemon.check(seed_phrase.get()):
                seed = mnemon.to_seed(seed_phrase.get())

                root_key = bip32utils.BIP32Key.fromEntropy(seed)
                address = root_key.Address()
                private_key = root_key.WalletImportFormat()

                self.controller.shared_data["key_pairs"].append({'private_key': private_key, 'address': address})
                click.echo(private_key)
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
        self.step_title = tk.Label(self, text="Verify Ownership", fg='#00A519', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 3", fg='#00A519', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.verify_pg01 = tk.Label(self, text="""This step involves specifying the substrate address you created on the new blockchain. Each address associated in your wallet will be signed with the substrate address on the next step.
        
This both proves that your substrate address 'owns' the BITG addresses on the old blockchain, and in the submission to the swap will authorise the equivilent funds to be sent to your Substrate address on the new blockchain.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.verify_pg01.place(x=270, y=110)

        self.substrate_txtfld = tk.Entry(self, textvariable=controller.shared_data["substrate-addr"],
                                         bd=2, relief=tk.GROOVE, font=controller.text_style)
        self.substrate_txtfld.config(fg='grey')
        self.substrate_txtfld.insert(0, "Substrate address")
        self.substrate_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Substrate address", self.substrate_txtfld))
        self.substrate_txtfld.bind("<FocusOut>", lambda event, message="Substrate address": handle_focus_out(event,
                                                                                                             "Substrate address",
                                                                                                             self.substrate_txtfld))
        self.substrate_txtfld.place(x=310, y=285, width=452, height=35)

        icon_key = tk.Label(self, image=icon_wallet_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_wallet_logo
        icon_key.place(x=270, y=286)

        if controller.operating_system != 'posix':
            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=self.verify_substrate_address,
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.next_btn.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=lambda: controller.show_frame("SeedPhrase"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.back_btn.place(x=270, y=330)
        else:
            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=self.verify_substrate_address,
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.next_btn.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=lambda: controller.show_frame("SeedPhrase"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.back_btn.place(x=270, y=330)

    def verify_substrate_address(self):
        message = self.controller.shared_data["substrate-addr"].get()

        if message == 'Substrate address' or message == '':
            messagebox.showinfo("Error", "You must specify a valid substrate address.")
            return

        self.controller.show_frame("SubmitSwap")


class SubmitSwap(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        menu_items(self, controller, 4)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Submit to swap", fg='#00A519', bg='#FFFFFF', font=controller.title_font)
        self.step = tk.Label(self, text="STEP 4", fg='#00A519', bg='#FFFFFF', font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.submitswap_pg01 = tk.Label(self,
                                        text="""When you are ready, press 'SIGN' to cryptographically sign each address with the specified substrate address to prove ownership.""",
                                        font=controller.text_style, justify=tk.LEFT,
                                        wraplength=500, bg='#FFFFFF')
        self.submitswap_pg01.place(x=270, y=100)

        self.submitswap_pg02 = tk.Label(self,
                                        text="""This will sign new substrate address with each keypair provided.""",
                                        font=controller.text_style, justify=tk.LEFT,
                                        wraplength=500, bg='#FFFFFF')
        self.submitswap_pg02.place(x=270, y=220)

        if controller.operating_system != 'posix':
            self.submit_btn = tk.Button(self, text="SIGN", font=controller.text_style_bold,
                                        fg='#FFFFFF', command=self.submit2swap,
                                        width=8, pady=2, relief=tk.GROOVE, border=0,
                                        bg='#00A519', highlightbackground='#00A519')
            self.submit_btn.place(x=630, y=290)

            self.next_btn = tk.Button(self, text="NEXT", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=lambda: controller.show_frame("Finished"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519', state=tk.DISABLED)
            self.next_btn.place(x=630, y=330)

            self.back_btn = tk.Button(self, text="BACK", font=controller.text_style_bold,
                                      fg='#FFFFFF', command=lambda: controller.show_frame("VerifyOwnership"),
                                      height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                      bg='#00A519', highlightbackground='#00A519')
            self.back_btn.place(x=270, y=330)
        else:
            self.submit_btn = Button(self, text='SIGN', font=controller.text_style_bold,
                                     fg='#FFFFFF', command=self.submit2swap,
                                     height=40, width=130, pady=4,
                                     activebackground=('#00A519', '#00A519'),
                                     activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.submit_btn.place(x=630, y=290)

            self.next_btn = Button(self, text='NEXT', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=lambda: controller.show_frame("Finished"),
                                   height=40, width=130, pady=4,
                                   disabledforeground='#FFFFFF', disabledbackground='#BFBFBF',
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True, state=tk.DISABLED)
            self.next_btn.place(x=630, y=330)

            self.back_btn = Button(self, text='BACK', font=controller.text_style_bold,
                                   fg='#FFFFFF', command=lambda: controller.show_frame("VerifyOwnership"),
                                   height=40, width=130, pady=4,
                                   activebackground=('#00A519', '#00A519'),
                                   activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.back_btn.place(x=270, y=330)

    def submit2swap(self):
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
            self.next_btn["state"] = tk.NORMAL
            messagebox.showinfo("Information", f"Successfully signed {result['signed_addresses_count']} addresses. Click Next to continue.")
        else:
            messagebox.showinfo("Error", f"Something went wrong. Please contact us.")


class Finished(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        address = self.controller.shared_data["substrate-addr"].get()

        menu_items(self, controller, 5)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Finished", fg='#00A519', bg='#FFFFFF',
                                   font=controller.title_font)
        self.step_title.place(x=270, y=40)
        ######################################

        self.finish_pg01 = tk.Label(self,
                                    text=f"""Congratulations, you have successfully signed your BITG address(s) with your specified substrate address.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg01.place(x=270, y=90)

        self.whatnext = tk.Label(self, text="What's next?", fg='#00A519', bg='#FFFFFF', font=controller.title_font)
        self.whatnext.place(x=270, y=180)

        self.finish_pg02 = tk.Label(self,
                                    text=f"""Follow BitGreen announcements to get updates on how to credit funds to your substrate address on the new blockchain using the file generated by the swap tool.""",
                                    font=controller.text_style, justify=tk.LEFT,
                                    wraplength=500, bg='#FFFFFF')
        self.finish_pg02.place(x=270, y=230)

        if controller.operating_system != 'posix':
            self.close_btn = tk.Button(self, text="CLOSE", font=controller.text_style_bold,
                                       fg='#FFFFFF', command=lambda: controller.destroy(),
                                       height=1, width=14, pady=4, relief=tk.GROOVE, border=0,
                                       highlightbackground='#00A519', bg='#00A519')
            self.close_btn.place(x=600, y=330)
        else:
            self.close_btn = Button(self, text='CLOSE', font=controller.text_style_bold,
                                    fg='#FFFFFF', command=lambda: controller.destroy(),
                                    height=40, width=130, pady=4,
                                    activebackground=('#00A519', '#00A519'),
                                    activeforeground='#FFFFFF', bg='#00A519', borderless=True)
            self.close_btn.place(x=630, y=330)


def on_closing():
    if messagebox.askokcancel('Quit', 'Are you sure you want to exit?'):
        window.destroy()
        exit()


if __name__ == '__main__':
    wallet = Wallet()
    window = SwapApplication()
    window.protocol('WM_DELETE_WINDOW', on_closing)
    window.title('BitGreen Swap Tool')
    window.geometry("800x500+10+10")
    window.resizable(False, False)
    window.mainloop()
