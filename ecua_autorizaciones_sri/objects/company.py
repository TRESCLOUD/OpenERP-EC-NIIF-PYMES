# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2010  Christopher Ormaza, Ecuadorenlinea.net            #
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
from osv import osv, fields
import re

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
                'authotization_ids':fields.one2many('sri.authorization', 'company_id', 'SRI Authorizations', required=False),
                'generate_automatic':fields.boolean('Generate Automatic Document', required=False),
                'shop_ids':fields.one2many('sale.shop', 'company_id', 'Shops', required=False),
                }
    
    _defaults = {
                 'generate_automatic': lambda *a: False,
                 }

res_company()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: