#########################################################################
# Copyright (C) 2012  Christopher Ormaza, Ecuadorenlinea.net            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "Voucher Improvements",
    "version" : "1.01",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Personalization",
    "depends" : ['base',
                 'account_voucher',
                 'ecua_facturas_manual',
                 'ecua_notas_credito_manual',
                 'ecua_liquidacion_compras',
                 'report_aeroo_ooo',
                 ],
    "description": """Some Improvements in Vouchers
    Voucher Statement with relation of invoice
    """,
    "init_xml": ['data/init.xml',],
    "update_xml": [
                   'report/voucher_report.xml',
                   'views/payment_mode_view.xml',
                   'views/voucher_view.xml',
    ],
    "installable": True,
    "active": False,
}