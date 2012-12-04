# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Christopher Ormaza A (<http://www.ecuadorenlinea.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
        "name" : "Liquidación de Compras",
        "version" : "1.19",
        "author" : "Ecuadorenlinea.net",
        "website" : "http://www.ecuadorenlinea.net",
        "category" : "Ecuadorian Legislation",
        "description": """  """,
        "depends" : ['base', 'report_aeroo_ooo',  'account', 'account_voucher', 'sale', 'ecua_autorizaciones_sri', 'ecua_facturas_manual',
                     'ecua_retenciones_manual'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'data/data.xml',
                        'report/liquidacion_reporte.xml',
                        'security/ir.model.access.csv',
                        'views/liquidacion_compra.xml',
                        'views/account_journal_view.xml',
                        'views/shop_view.xml',
                        ],
        "installable": True
}