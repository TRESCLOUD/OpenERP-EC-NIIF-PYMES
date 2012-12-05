#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
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
import netsvc
from datetime import date, datetime, timedelta
import decimal_precision as dp

import tools
from osv import fields, osv
from tools import config
from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher' 
    _columns = {
            'payslip_id':fields.many2one('hr.payslip', 'Payslip', required=False, readonly=True, states={'draft':[('readonly',False)]}), 
            'extra_i_o_ids':fields.one2many('hr.extra.input.output', 'voucher_id', 'Extra Payments Outputs', required=False), 
                    }
account_voucher()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: