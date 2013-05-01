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

from time import strftime
import time

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class res_company(osv.osv):
    
    _inherit  = 'res.company' 

    _columns = {
                'default_working_hours_id':fields.many2one('resource.calendar', 'Default Working Schedule'),
                'default_struct_id': fields.many2one('hr.payroll.structure', 'Default Salary Structure'),
                'default_salary_journal_id': fields.many2one('account.journal', 'Default Salary Journal'),
                'default_account_debit_id': fields.many2one('account.account', 'Default Debit Account Employee', domain=[('type','=','receivable')]),
                'default_account_credit_id': fields.many2one('account.account', 'Default Credit Account Employee', domain=[('type','=','payable')]),
                'rule_funds_accumulated_id':fields.many2one('hr.salary.rule', 'Regla Fondos de Reserva Acumulados', required=False),
                'rule_funds_paid_id':fields.many2one('hr.salary.rule', 'Regla Fondos de Reserva Pagados', required=False),
                'year_vacation_accumulated_id':fields.many2one('account.fiscalyear', 'Año del que pagar Vacaciones Acumuladas', required=False),  
                    }
    
res_company()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: