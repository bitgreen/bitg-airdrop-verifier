import sys
import json
import uuid
import os.path
from sys import exit
from tkinter import ttk
from utils import rpc_module
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk

try:
    import tkinter as tk                # python 3
    from tkinter import font as tkfont  # python 3
except ImportError:
    import Tkinter as tk                # python 2
    import tkFont as tkfont             # python 2

rpc = rpc_module.Rpc()


class Signer:
    def __init__(self):
        self.address_list = {}

    def get_addresses(self):
        for addr in rpc.listaddressgroupings():
            if len(addr) > 1:
                for addr in addr:
                    self.address_list.update({addr[0]: ''})
            else:
                self.address_list.update({addr[0][0]: ''})

    def private_keys(self):
        # iterate through each public key and dump the private key that corresponds
        # update dictionary 'address_list' with the private key to be later used for
        # signing a message proving ownership of address
        for key, value in self.address_list.items():
            self.address_list.update({key: rpc.dumpprivkey(key)})

    def signmessage(self, message):
        for key, value in self.address_list.items():
            self.address_list.update({key: rpc.signmessagewithprivkey(value, message)})


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
                messagebox.showinfo('message', 'Wallet is locked, please unlock using passphrase')
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

        self.title_font = tkfont.Font(family='Calibri light', size=24, weight="normal")
        self.title_font_step = tkfont.Font(family='Calibri light', size=11, weight="bold")
        self.EntryFont = tkfont.Font(family='Calibri light', size=11, weight="bold")
        self.text_style = tkfont.Font(family='Calibri light', size=11, weight="normal")
        self.text_style_bold = tkfont.Font(family='Calibri Light', size=11, weight="bold")

        self.shared_data = {
            "directory": tk.StringVar(),
            "password": tk.StringVar(),
            "substrate-addr": tk.StringVar()
        }

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
        for F in (StartPage, WalletData, EnableTool, VerifyOwnership, SubmitSwap, Finished):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.configure(bg='white')
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
        swap_logo_img = swap_logo_img.resize((200, 200), Image.ANTIALIAS)
        swap_logo = ImageTk.PhotoImage(swap_logo_img)

        # Call .jpg image into PhotoImage
        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        swap_logo_lbl = tk.Label(self, image=swap_logo, borderwidth=0, highlightthickness=0)
        swap_logo_lbl.image = swap_logo
        swap_logo_lbl.pack(side="top", fill="y", anchor=tk.SW, padx=50, pady=45)

        # Start
        self.start_btn = tk.Button(self, text="START",
                                   font=controller.text_style_bold,
                                   fg='white',
                                   command=lambda: controller.show_frame("WalletData"),
                                   width=14,
                                   height=1,
                                   pady=4,
                                   relief=tk.GROOVE,
                                   border=0,
                                   bg='#00A519')
        self.start_btn.place(x=85, y=275)

        self.startpage_pg01 = tk.Label(self, text="""This tool is designed to make it easy for you to identify all addresses 
that exist in your current BitGreen wallet, and to prove your ownership 
of those addresses to submit to the swap process.

Subsequently you will receive the equivalent funds to your preferred 
Substrate address on the new blockchain.""",
                                       font=controller.text_style,
                                       justify=tk.LEFT,
                                       wraplength=500,
                                       bg='white')
        self.startpage_pg01.place(x=285, y=15, )

        self.startpage_pg02 = tk.Label(self, text="""Note the snapshot date for address balances is block XXX 
(or around 21st March 2021).To receive funds from the swap on 
the new chain, you must have had a balance at this snapshot date.""",
                                       font=controller.text_style_bold,
                                       justify=tk.LEFT,
                                       wraplength=500,
                                       bg='white',
                                       fg='#E80000')
        self.startpage_pg02.place(x=285, y=140, )

        self.before_you_begin = tk.Label(self, text="Before you begin", fg='#00A519', bg='white',
                                         font=controller.title_font)
        self.before_you_begin.place(x=285, y=220)

        self.startpage_pg03 = tk.Label(self, text=u"""Please ensure that:
        
            Your BitGreen desktop wallet is open
    
            You already have a substrate address for the new chain
""",
                                       font=controller.text_style,
                                       justify=tk.LEFT,
                                       wraplength=500,
                                       bg='white')
        self.startpage_pg03.place(x=285, y=265, )

        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=285, y=298)

        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=285, y=334)


class WalletData(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.wallet = Wallet()

        self.folder_path = tk.StringVar()
        self.entry_content = tk.StringVar()

        # Call .jpg image into PhotoImage
        icon_folder_img = Image.open(resourcePath('icons_Folder.jpg'))
        icon_folder_img = icon_folder_img.resize((30, 30), Image.ANTIALIAS)
        icon_folder_logo = ImageTk.PhotoImage(icon_folder_img)

        # Call .jpg image into PhotoImage
        icon_key_img = Image.open(resourcePath('icons_Key.jpg'))
        icon_key_img = icon_key_img.resize((30, 30), Image.ANTIALIAS)
        icon_key_logo = ImageTk.PhotoImage(icon_key_img)

        # Step(s) status - Wallet data ######
        active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
        active_dot_img = active_dot_img.resize((30, 30), Image.ANTIALIAS)
        active_dot_logo = ImageTk.PhotoImage(active_dot_img)

        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        # Active - Wallet Data
        wallet_data_lbl = tk.Label(self, text="Wallet data", bg='white', font=controller.text_style)
        wallet_data_lbl.place(x=90, y=45)
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
        dot.place(x=40, y=45)

        # Inactive
        enable_this_tool_lbl = tk.Label(self, text="Enable this tool", bg='white', font=controller.text_style)
        enable_this_tool_lbl.place(x=90, y=110)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=110)

        # Inactive
        verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='white', font=controller.text_style)
        verify_ownership_lbl.place(x=90, y=175)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=175)

        # Inactive
        submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='white', font=controller.text_style)
        submit_to_swap_lbl.place(x=90, y=240)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=240)

        # Inactive
        finished_lbl = tk.Label(self, text="Finished", bg='white', font=controller.text_style)
        finished_lbl.place(x=90, y=305)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=305)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Wallet Data ############
        self.step_title = tk.Label(self, text="BitGreen wallet data", fg='#00A519', bg='white',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 1", fg='#00A519', bg='white',
                             font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.walletdata_pg01 = tk.Label(self,
                                        text="""Select the directory where your BitGreen wallet data is located, and if you have encrypted your wallet, enter the password.""",
                                        font=controller.text_style,
                                        justify=tk.LEFT,
                                        wraplength=500,
                                        bg='white')
        self.walletdata_pg01.place(x=270, y=110)

        icon_folder = tk.Label(self, image=icon_folder_logo, borderwidth=0, highlightthickness=0)
        icon_folder.image = icon_folder_logo
        icon_folder.place(x=270, y=170)

        self.walletdir_txtfld = tk.Entry(self, textvariable=controller.shared_data["directory"], bd=2, relief=tk.GROOVE,
                                         font=controller.text_style)
        self.walletdir_txtfld.config(fg='grey')
        self.walletdir_txtfld.insert(0, "Directory")
        self.walletdir_txtfld.bind("<Button-1>", self.walletdir)
        self.walletdir_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Directory", self.walletdir_txtfld))
        self.walletdir_txtfld.bind("<FocusOut>",
                                   lambda event, message="Wallet password": handle_focus_out(event, "Directory",
                                                                                             self.walletdir_txtfld))
        self.walletdir_txtfld.place(x=310, y=170, width=380, height=35)

        icon_key = tk.Label(self, image=icon_key_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_key_logo
        icon_key.place(x=270, y=215)

        self.passwd_txtfld = tk.Entry(self, textvariable=controller.shared_data["password"], bd=2, relief=tk.GROOVE,
                                      font=controller.text_style)
        self.passwd_txtfld.config(fg='grey')
        self.passwd_txtfld.insert(0, "Wallet password")
        self.passwd_txtfld.bind("<FocusIn>",
                                lambda event,: handle_focus_in(event, "Wallet password", self.passwd_txtfld))
        self.passwd_txtfld.bind("<FocusOut>",
                                lambda event, message="Wallet password": handle_focus_out(event, "Wallet password",
                                                                                          self.passwd_txtfld))
        self.passwd_txtfld.place(x=310, y=215, width=270, height=35)

        self.next_btn = tk.Button(self, text="NEXT",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("EnableTool"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.next_btn.place(x=630, y=340)

    def walletdir(self, event):
        # Allow user to select a directory and store it in global var
        # called folder_path
        global folder_path
        filename = filedialog.askdirectory()
        self.controller.shared_data["directory"].set(filename)

    def msgbox(self, title, messge):
        messagebox.showinfo(title, messge)


class EnableTool(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Step(s) status - Wallet data ######
        active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
        active_dot_img = active_dot_img.resize((30, 30), Image.ANTIALIAS)
        active_dot_logo = ImageTk.PhotoImage(active_dot_img)

        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        # Inactive
        wallet_data_lbl = tk.Label(self, text="Wallet data", bg='white', font=controller.text_style)
        wallet_data_lbl.place(x=90, y=45)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=45)

        # Active - # Enable this tool
        enable_this_tool_lbl = tk.Label(self, text="Enable this tool", bg='white', font=controller.text_style)
        enable_this_tool_lbl.place(x=90, y=110)
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
        dot.place(x=40, y=110)

        # Inactive
        verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='white', font=controller.text_style)
        verify_ownership_lbl.place(x=90, y=175)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=175)

        # Inactive
        submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='white', font=controller.text_style)
        submit_to_swap_lbl.place(x=90, y=240)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=240)

        # Inactive
        finished_lbl = tk.Label(self, text="Finished", bg='white', font=controller.text_style)
        finished_lbl.place(x=90, y=305)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=305)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Enable this tool ############
        self.step_title = tk.Label(self, text="Enable this tool", fg='#00A519', bg='white',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 2", fg='#00A519', bg='white',
                             font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.walletdata_pg01 = tk.Label(self, text="""It is requires to update the bitgreen.conf file in your BitGreen wallet's data folder so that this tool is able to communicate with your wallet.
        
Click 'CREATE CONFIG' before pressing 'Enable' to complete this action.""",
                                        font=controller.text_style,
                                        justify=tk.LEFT,
                                        wraplength=500,
                                        bg='white')
        self.walletdata_pg01.place(x=270, y=110)

        self.create_config_btn = tk.Button(self, text="CREATE CONFIG",
                                           font=controller.text_style_bold,
                                           fg='white',
                                           command=self.create_config,
                                           width=14,
                                           pady=2,
                                           relief=tk.GROOVE,
                                           border=0,
                                           bg='#00A519')
        self.create_config_btn.place(x=270, y=200)

        self.enable_btn = tk.Button(self, text="ENABLE",
                                    font=controller.text_style_bold,
                                    fg='white',
                                    command=self.enable_rpc,
                                    width=8,
                                    pady=2,
                                    relief=tk.GROOVE,
                                    border=0,
                                    bg='#00A519')
        self.enable_btn.place(x=410, y=200)

        self.next_btn = tk.Button(self, text="NEXT",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("VerifyOwnership"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.next_btn.place(x=630, y=340)

        self.back_btn = tk.Button(self, text="BACK",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("WalletData"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.back_btn.place(x=270, y=340)

    def create_config(self):
        directory = self.controller.shared_data["directory"].get()

        if directory == 'Directory' or directory == '':
            messagebox.showinfo("Error", "You must specify the block directory.")
            return

        # check if a config already exists; rename if it does.
        if os.path.isfile(f"{directory}/bitgreen.conf"):
            os.rename(f"{directory}/bitgreen.conf", f"{directory}/bitgreen-{uuid.uuid4().hex[:6]}.conf")

        if os.path.isfile(f"{directory}/wallet.dat"):
            with open(f"{directory}/bitgreen.conf", "w") as conf:
                conf.write("""server=1
rpcbind=127.0.0.1
rpcport=8331
rpcuser=SignWithSubstrate
rpcpassword=SignWithSubstrate""")
                messagebox.showinfo("Information",
                                    "Bitgreen.conf created!\n\nRestart your wallet if opened already.\nIf not, open your BitGreen wallet before clicking 'ENABLE'.")
        else:
            messagebox.showinfo("Error", "Please check you have specified the correct block directory")

    def enable_rpc(self):
        passwd = self.controller.shared_data["password"].get()

        if not rpc.isRpcRunning():
            messagebox.showinfo("Error",
                                "Unable to connect via RPC 127.0.0.1:8331\nMake sure your wallet has been restarted or open")
            return

        if wallet.unlock(passwd):
            messagebox.showinfo("Information", "Wallet unlocked for 15 minutes")


class VerifyOwnership(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Step(s) status - Wallet data ######
        active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
        active_dot_img = active_dot_img.resize((30, 30), Image.ANTIALIAS)
        active_dot_logo = ImageTk.PhotoImage(active_dot_img)

        icon_wallet_img = Image.open(resourcePath('icons_Folder.jpg'))
        icon_wallet_img = icon_wallet_img.resize((30, 30), Image.ANTIALIAS)
        icon_wallet_logo = ImageTk.PhotoImage(icon_wallet_img)

        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        # Inactive
        wallet_data_lbl = tk.Label(self, text="Wallet data", bg='white', font=controller.text_style)
        wallet_data_lbl.place(x=90, y=45)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=45)

        # Inactive
        enable_this_tool_lbl = tk.Label(self, text="Enable this tool", bg='white', font=controller.text_style)
        enable_this_tool_lbl.place(x=90, y=110)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=110)

        # Active - Verify Ownership
        verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='white', font=controller.text_style)
        verify_ownership_lbl.place(x=90, y=175)
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
        dot.place(x=40, y=175)

        # Inactive
        submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='white', font=controller.text_style)
        submit_to_swap_lbl.place(x=90, y=240)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=240)

        # Inactive
        finished_lbl = tk.Label(self, text="Finished", bg='white', font=controller.text_style)
        finished_lbl.place(x=90, y=305)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=305)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Verify Ownership", fg='#00A519', bg='white',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 3", fg='#00A519', bg='white',
                             font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.verify_pg01 = tk.Label(self, text="""This step involves signing a message for each BITG address found,
associating it with your preferred Substrate address on the new chain.
        
This both proves that your Substrate address 'owns' the BITG addresses on the old chain, and in the submission on the next step will authorise the equivalent funds to be sent to your Substrate address on the new chain by generating a .json file containing all addresses, signatures and Substrate address signed with. 

Enter your preferred Substrate address below.""",
                                    font=controller.text_style,
                                    justify=tk.LEFT,
                                    wraplength=500,
                                    bg='white')
        self.verify_pg01.place(x=270, y=110)

        self.substrate_txtfld = tk.Entry(self, textvariable=controller.shared_data["substrate-addr"], bd=2,
                                         relief=tk.GROOVE, font=controller.text_style)
        self.substrate_txtfld.config(fg='grey')
        self.substrate_txtfld.insert(0, "Substrate address")
        self.substrate_txtfld.bind("<FocusIn>",
                                   lambda event,: handle_focus_in(event, "Substrate address", self.substrate_txtfld))
        self.substrate_txtfld.bind("<FocusOut>", lambda event, message="Substrate address": handle_focus_out(event,
                                                                                                             "Substrate address",
                                                                                                             self.substrate_txtfld))
        self.substrate_txtfld.place(x=310, y=290, width=380, height=35)

        icon_key = tk.Label(self, image=icon_wallet_logo, borderwidth=0, highlightthickness=0)
        icon_key.image = icon_wallet_logo
        icon_key.place(x=270, y=290)

        self.next_btn = tk.Button(self, text="NEXT",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("SubmitSwap"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.next_btn.place(x=630, y=340)

        self.back_btn = tk.Button(self, text="BACK",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("EnableTool"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.back_btn.place(x=270, y=340)


class SubmitSwap(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Step(s) status - Wallet data ######
        active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
        active_dot_img = active_dot_img.resize((30, 30), Image.ANTIALIAS)
        active_dot_logo = ImageTk.PhotoImage(active_dot_img)

        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        # Inactive
        wallet_data_lbl = tk.Label(self, text="Wallet data", bg='white', font=controller.text_style)
        wallet_data_lbl.place(x=90, y=45)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=45)

        # Inactive
        enable_this_tool_lbl = tk.Label(self, text="Enable this tool", bg='white', font=controller.text_style)
        enable_this_tool_lbl.place(x=90, y=110)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=110)

        # Inactive
        verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='white', font=controller.text_style)
        verify_ownership_lbl.place(x=90, y=175)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=175)

        # Active - Submit to swap
        submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='white', font=controller.text_style)
        submit_to_swap_lbl.place(x=90, y=240)
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
        dot.place(x=40, y=240)

        # Inactive
        finished_lbl = tk.Label(self, text="Finished", bg='white', font=controller.text_style)
        finished_lbl.place(x=90, y=305)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=305)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Submit to swap", fg='#00A519', bg='white',
                                   font=controller.title_font)
        self.step = tk.Label(self, text="STEP 4", fg='#00A519', bg='white',
                             font=controller.title_font_step)
        self.step.place(x=270, y=75)
        self.step_title.place(x=270, y=40)
        ######################################

        self.submitswap_pg01 = tk.Label(self, text="""To the right is the total BITG addresses found, each signed with their private key to prove ownership, using a message stating your provided Substrate address.

Click 'Submit' to proceed and submit this information to the swap process""",
                                        font=controller.text_style,
                                        justify=tk.LEFT,
                                        wraplength=205,
                                        bg='white')
        self.submitswap_pg01.place(x=270, y=100)

        self.scrollbar = tk.Scrollbar(self)
        self.t = tk.Text(self, height=18, width=70, yscrollcommand=self.scrollbar.set, font=("Helvetica", 6),
                         borderwidth=1,
                         relief="solid", wrap=tk.NONE)
        self.scrollbar.config(command=self.t.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.t.place(x=480, y=100)

        self.submit_btn = tk.Button(self, text="SUBMIT",
                                    font=controller.text_style_bold,
                                    fg='white',
                                    command=self.submit2swap,
                                    width=8,
                                    pady=2,
                                    relief=tk.GROOVE,
                                    border=0,
                                    bg='#00A519')
        self.submit_btn.place(x=480, y=290)

        self.next_btn = tk.Button(self, text="NEXT",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("Finished"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.next_btn.place(x=630, y=340)

        self.back_btn = tk.Button(self, text="BACK",
                                  font=controller.text_style_bold,
                                  fg='white',
                                  command=lambda: controller.show_frame("VerifyOwnership"),
                                  width=14,
                                  height=1,
                                  pady=4,
                                  relief=tk.GROOVE,
                                  border=0,
                                  bg='#00A519')
        self.back_btn.place(x=270, y=340)

    def signAddresses(self, message):
        directory = self.controller.shared_data["directory"].get()

        if not rpc.isRpcRunning():
            print("rpc isn't running")
            return

        if directory == 'Directory' or directory == '':
            messagebox.showinfo("Error", "You must specify the block directory.")
            return

        if os.path.isfile(f"{directory}/wallet.dat"):
            signer = Signer()

            # gather list of addresses associated with wallet
            signer.get_addresses()

            # using get_addresses, dump the private key to each public key and update dictionary 'address_list'
            signer.private_keys()

            # sign with message
            signer.signmessage(message)

            output = {'addresses': signer.address_list,
                      'substrate-address': message}

            self.t.configure(state="normal")
            self.t.delete(1.0, tk.END)
            self.t.insert(tk.END, json.dumps(output, indent=4))
            self.t.configure(state="disabled")

            with open(f"{directory}\substrate-signed.json", "w") as outfile:
                json.dump(output, outfile, indent=4)
            messagebox.showinfo("Information", f"substrate-signed.json created in {directory}")
        else:
            messagebox.showinfo("Error", "Please check you have specified the correct block directory")

    def submit2swap(self):
        message = self.controller.shared_data["substrate-addr"].get()

        if message == 'Substrate address' or message == '':
            messagebox.showinfo("Error", "You must specify a substrate address")
            return

        self.signAddresses(message)


class Finished(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Step(s) status - Wallet data ######
        active_dot_img = Image.open(resourcePath('icons_Dot Current.jpg'))
        active_dot_img = active_dot_img.resize((30, 30), Image.ANTIALIAS)
        active_dot_logo = ImageTk.PhotoImage(active_dot_img)

        dot_img = Image.open(resourcePath('icons_Dot.jpg'))
        dot_img = dot_img.resize((30, 30), Image.ANTIALIAS)
        dot_logo = ImageTk.PhotoImage(dot_img)

        # Inactive
        wallet_data_lbl = tk.Label(self, text="Wallet data", bg='white', font=controller.text_style)
        wallet_data_lbl.place(x=90, y=45)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=45)

        # Inactive
        enable_this_tool_lbl = tk.Label(self, text="Enable this tool", bg='white', font=controller.text_style)
        enable_this_tool_lbl.place(x=90, y=110)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=110)

        # Inactive
        verify_ownership_lbl = tk.Label(self, text="Verify ownership", bg='white', font=controller.text_style)
        verify_ownership_lbl.place(x=90, y=175)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=175)

        # Inactive
        submit_to_swap_lbl = tk.Label(self, text="Submit to swap", bg='white', font=controller.text_style)
        submit_to_swap_lbl.place(x=90, y=240)
        dot = tk.Label(self, image=dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = dot_logo
        dot.place(x=40, y=240)

        # Active - Finished
        finished_lbl = tk.Label(self, text="Finished", bg='white', font=controller.text_style)
        finished_lbl.place(x=90, y=305)
        dot = tk.Label(self, image=active_dot_logo, borderwidth=0, highlightthickness=0)
        dot.image = active_dot_logo
        dot.place(x=40, y=305)

        ## Separate ###############
        separator = ttk.Separator(self, orient='vertical')
        separator.place(relx=0.3, rely=0.1, relwidth=0, relheight=0.8)
        ###########################

        ## BitGreen - Verify Ownership ############
        self.step_title = tk.Label(self, text="Finished", fg='#00A519', bg='white',
                                   font=controller.title_font)
        self.step_title.place(x=270, y=40)
        ######################################

        self.close_btn = tk.Button(self, text="CLOSE",
                                   font=controller.text_style_bold,
                                   fg='white',
                                   command=lambda: controller.destroy(),
                                   width=14,
                                   height=1,
                                   pady=4,
                                   relief=tk.GROOVE,
                                   border=0,
                                   bg='#00A519')
        self.close_btn.place(x=600, y=340)


def on_closing():
    if messagebox.askokcancel('Quit', 'Are you sure you want to exit?'):
        window.destroy()
        exit()


if __name__ == '__main__':
    wallet = Wallet()
    window = SwapApplication()
    window.protocol('WM_DELETE_WINDOW', on_closing)
    window.iconbitmap(resourcePath('favicon.ico'))
    window.title('BitGreen Swap Tool')
    window.geometry("800x500+10+10")
    window.resizable(False, False)
    window.mainloop()
