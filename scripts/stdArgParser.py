from argparse import ArgumentParser


def getStandardArgParser():
    parser = ArgumentParser()
    parser.add_argument("-ou", "--oracleuser", dest="oracleUser", default=None,
                        help="username for Oracle")
    parser.add_argument("-op", "--oraclepassword", dest="oraclePassword", default=None,
                        help="password for Oracle")
    parser.add_argument("-s", "--savecredentials",
                        action="store_true", dest="saveCredentials", default=False,
                        help="store given credentials on Windows/Linux Keyring")
    parser.add_argument("-d", "--defaultuser",
                        action="store_true", dest="setDefaultUser", default=False,
                        help="set given user as default User (can only be used together with --saveCredentials)")
    return parser
