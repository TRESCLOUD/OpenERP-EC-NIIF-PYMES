#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
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
    "name" : "Ecuadorian SRI Authorization",
    "version" : "1.39",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Ecuadorian Regulations",
    "depends" : ['base',
                 'account',
                 'sale',
                 'ecua_verifica_ruc_cedula',
                 'account_accountant',
                 'stock',
                 'point_of_sale',
                 'account_voucher', 
                 #'account_accountant',
                # 'ecua_invoice_type',
                 ],
    "description": """
    SRI is the regulator of the tax laws in Ecuador, 
    the agency issued permits for the printing of 
    bills for each company and each agency stated,
    this is a generic authorization for all documents in Ecuador
    """,
    "init_xml": [],
    "update_xml": [ 
                    'security/groups.xml',
                    'security/ir.model.access.csv',
                    'data/data.xml',
                    'data/shop.xml',
                    'views/authorizacion_wizard.xml',
                    'views/authorization_view.xml',
                    'views/company_view.xml',
                    'views/document_type_view.xml',
                    'views/partner_view.xml',
                    #'views/picking_view.xml',
                    'views/sale_order_view.xml',
                    'views/shop_view.xml',
                    'views/user_view.xml',
                    #'views/voucher_view.xml',
    ],
    "installable": True,
    "active": False,
}
