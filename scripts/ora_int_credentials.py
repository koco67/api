# -*- coding: utf-8 -*-

# 18.06.2021
# Python 3.8
# Windows 10


from i_credentials import ICredentials


class OraIntCredentials(ICredentials):

    def __init__(self, username_attr, password_attr):
        self.username_attr = username_attr
        self.password_attr = password_attr
        self.serviceName_attr = 'FZJA.FZJ.DE'
        self.url_attr = 'ORASRV.ZAM.KFA-JUELICH.DE'
        self.port_attr = 1521
        self.clientDirectory_attr = \
            r'C:\Inst\Datenbanken\gtiprofiaccess\instantclient_19_3'

        # C:\Inst\Datenbanken\gtiprofiaccess\instantclient_19_3
        # C:\Users\zimmermannm\Documents\Programme\instantclient_19_3

    def username(self):
        return self.username_attr

    def password(self):
        return self.password_attr

    def serviceName(self):
        return self.serviceName_attr

    def url(self):
        return self.url_attr

    def port(self):
        return self.port_attr

    def clientDirectory(self):
        return self.clientDirectory_attr


def main():
    pass


if __name__ == "__main__":
    main()
