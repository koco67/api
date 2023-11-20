# -*- coding: utf-8 -*-

# 18.06.2021
# Python 3.8
# Windows 10


import logging
import traceback


'''Configurate logfile'''
#ggf. überflüssig
logging.basicConfig(filename='error.log',
                    level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')
