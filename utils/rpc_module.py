import socket
import json, requests
from os.path import expanduser

HOMEPATH = expanduser("~")

class Rpc:
    def __init__(self):
        self.recipients = {}

        self.rpc_host = '127.0.0.1'
        self.rpc_port = '8331'
        self.rpc_user = 'SignWithSubstrate'
        self.rpc_pass = 'SignWithSubstrate'
        self.serverURL = 'http://' + self.rpc_host + ':' + self.rpc_port
        self.headers = {'content-type': 'application/json'}

    def isRpcRunning(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', 8331))
            return True
        except:
            return False

    def getinfo(self):
        payload = json.dumps({"method": "getblockchaininfo", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def listaddressgroupings(self):
        payload = json.dumps({"method": "listaddressgroupings", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def dumpprivkey(self, address):
        payload = json.dumps({"method": "dumpprivkey", "params": [address], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def signmessagewithprivkey(self, privkey, message):
        payload = json.dumps({"method": "signmessagewithprivkey", "params": [privkey, message], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def verifymessage(self, address, signature, message):
        payload = json.dumps({"method": "verifymessage", "params": [address, signature, message], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def isWalletlocked(self):
        payload = json.dumps({"method": "getwalletinfo", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def getaddrinfo(self, address):
        payload = json.dumps({"method": "getaddressinfo", "params": [address], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def walletpassphrase(self, passwd, timeout):
        payload = json.dumps({"method": "walletpassphrase", "params": [passwd, timeout], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                 auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']