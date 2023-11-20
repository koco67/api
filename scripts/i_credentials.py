# -*- coding: utf-8 -*-

# 18.06.2021
# Python 3.8
# Windows 10


from abc import ABC, abstractmethod


class ICredentials(ABC):
    '''Interface für verschiedene Arten von Credentials'''
    # bzgl Klassendiagramm: warum diese Aufteilung auf Attribute und Methoden?
    # hier jetzt einfach alles erstmal als properties implementiert
    # (gibt es einen eleganteren Weg um "abstrakte Attribute" zu erstellen?

    @property
    @abstractmethod
    def serviceName(self):
        pass

    @property
    @abstractmethod
    def username(self):
        pass

    @property
    @abstractmethod
    def password(self):
        pass

    @abstractmethod
    def url(self):
        pass

    @property
    @abstractmethod
    def port(self):
        pass
