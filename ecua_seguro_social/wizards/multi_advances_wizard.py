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

class multi_advance_wizard(osv.osv_memory):
    
    _name = "hr.multi.advance.wizard"
    
    _columns = {
                'name':fields.char('Description', size=255, help="%s will be replaced by name of employee"),
                'employee_ids':fields.many2many('hr.employee', 'wizard_employee_rel', 'employee_id', 'wizard_id', 'Employees'), 
                'line_ids':fields.one2many('hr.multi.advance.wizard.line', 'wizard_id', 'Lines', required=False),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')), 
                'period_id':fields.many2one('account.period', 'Period', help="Period to Pay"), 
                'journal_id':fields.many2one('account.journal', 'Journal', help="Journal of Payment"), 
                'date': fields.date('Date', help="Date of Voucher"),
                'option':fields.selection([
                    ('one_amount','One Amount'),
                    ('multi_amount','Multi Amount'),
                     ],    'Option', select=True,),
                    }
    
    _defaults = {  
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'option': 'multi_amount',
        'name': _('Advance to %s'),
        }
    
    def _check_amount(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for wizard in self.browse(cr, uid, ids, context):
            if wizard.amount <= 0:
                return False
        return True
    
    _constraints = [(_check_amount, _('Error: Amount must be bigger than zero'), ['amount']), ] 
    
    def get_option(self, cr, uid, ids, context=None):
        if not context:
            context={}
        line_obj = self.pool.get('hr.multi.advance.wizard.line')
        emp_obj = self.pool.get('hr.employee')
        obj_model = self.pool.get('ir.model.data')
        wizard = self.browse(cr, uid, ids[0], context)
        for employee in wizard.employee_ids:
            vals_line = {
                         'wizard_id': wizard.id,
                         'employee_id': employee.id,
                         'amount': wizard.amount,
                         'period_id': wizard.period_id.id,
                         'journal_id': wizard.journal_id.id,
                         'date': wizard.date,
                         'name' : wizard.name,
                         }
            line_obj.create(cr, uid, vals_line, context)
        if wizard.option == 'multi_amount':
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','hr_multi_advance_wizard_form_multi_amount_view')])
        elif wizard.option == 'one_amount':
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','hr_multi_advance_wizard_form_one_amount_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.multi.advance.wizard',
            'res_id': wizard.id,
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    def generate_vouchers(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        wf_service = netsvc.LocalService('workflow')
        adv_obj = self.pool.get('account.hr.advances')
        obj_model = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        list_ids = []
        for line in wizard.line_ids:
            vals_advance = {
                            'name': line.name,
                            'date': line.date,
                            'employee_id': line.employee_id.id,
                            'partner_id': line.employee_id.partner_id.id,
                            'journal_id': line.journal_id.id,
                            'amount_to_pay': line.amount,
                            'payment_policy': 'one_payment',
                            'date_policy': 'period',
                            'period_to_pay_id': line.period_id.id,
                            'type': 'out_advance',
                            }
            adv_id = adv_obj.create(cr, uid, vals_advance, context)
            wf_service.trg_validate(uid, 'account.hr.advances', adv_id, 'proforma_advance', cr)
            list_ids.append(adv_id)
        xml_id = 'action_supplier_advance'
        result = obj_model.get_object_reference(cr, uid, 'ecua_seguro_social', xml_id)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        advance_domain = eval(result['domain'])
        advance_domain.append(('id', 'in', list_ids))
        result['domain'] = advance_domain
        return result
multi_advance_wizard()

class multi_advance_wizard_line(osv.osv_memory):
    
    _name = "hr.multi.advance.wizard.line"
    
    _columns = {
                'name':fields.char('Name', size=64, required=False, readonly=False),
                'employee_id':fields.many2one('hr.employee', 'Employee', required=False),
                'wizard_id':fields.many2one('hr.multi.advance.wizard', 'Wizard', required=False),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')), 
                'period_id':fields.many2one('account.period', 'Period', required=False), 
                'journal_id':fields.many2one('account.journal', 'Journal', required=False), 
                'date': fields.date('Date'),
                    }
    
    def _check_amount(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for wizard in self.browse(cr, uid, ids, context):
            if wizard.amount <= 0:
                return False
        return True
    
    _constraints = [(_check_amount, _('Error: Amount must be bigger than zero'), ['amount']), ]
    
multi_advance_wizard_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: