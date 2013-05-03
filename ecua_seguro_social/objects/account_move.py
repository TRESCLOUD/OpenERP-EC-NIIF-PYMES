
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Lopez Mite(celm1990@outlook.com)                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                 
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class account_move(osv.osv):

    _inherit = 'account.move' 
    def name_get(self, cursor, user, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        res = []
        data_move = self.pool.get('account.move').browse(cursor, user, ids, context=context)
        for move in data_move:
            if move.state=='draft':
                name = '* %s/%s' % (move.id, move.ref or '') 
            else:
                name = '%s/%s' % (move.name, move.ref or '') 
            res.append((move.id, name))
        return res
account_move()