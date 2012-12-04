# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2010  Christoher Ormaza, Ecuadorenlinea.net              #
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
from osv import fields,osv

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
                'journal_iva_id':fields.many2one('account.journal', 'IVA Journal'), 
                'journal_ir_id':fields.many2one('account.journal', 'IR Journal'), 
                }
res_company()