#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 Carlos Lopez(celm1990@outlook.com) - Ecuadorenlinea.net 
#    Copyright (C) 2011-2012 Christopher Ormaza - Ecuadorenlinea.net 
#    (<http://www.ecuadorenlinea.net>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

import netsvc
from osv import fields, osv
import tools
from tools.translate import _
import decimal_precision as dp

from tools.safe_eval import safe_eval as eval

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class res_partner_bank(osv.osv):
    
    def _bank_type_get(self, cr, uid, context=None):
        bank_type_obj = self.pool.get('res.partner.bank.type')

        result = []
        type_ids = bank_type_obj.search(cr, uid, [])
        bank_types = bank_type_obj.browse(cr, uid, type_ids, context=context)
        for bank_type in bank_types:
            if bank_type.code not in ('iban','bank'):
                result.append((bank_type.code, bank_type.name))
        return result
    
    '''
    Open ERP Model
    '''
    _inherit = 'res.partner.bank'
#    
    _columns = {
                'state': fields.selection(_bank_type_get, 'Bank Type', required=True,
                                          change_default=True),
                }
    
    
    def _check_acc_number(self, cr, uid, ids, context=None): 
        if not context:
            context={}
        this=self.browse(cr,uid, ids[0], context)
        try:
            aux=int(this.acc_number)
            return True
        except:
            return False
        #TODO : check condition and return boolean accordingly
    _constraints = [(_check_acc_number, _('Error: Ingrese solo numeros en la cuenta'), ['acc_number']), ] 
res_partner_bank()

class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
                'employee':fields.boolean('Employee?', required=False), 
                    }
res_partner()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: