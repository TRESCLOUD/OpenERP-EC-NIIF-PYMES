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

class wizard_payslip(osv.osv_memory):

    _name = 'wizard.payslip'

    def act_cancel(self, cr, uid, ids, context):
        return {'type':'ir.actions.act_window_close'}

    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        ids = self.pool.get('account.period').find(cr, uid, context=context)
        return ids[0] and ids[0] or False    

    _columns = {
        'date': fields.date('Date', required=True, help="Effective date for posting, If you left in blank the system use today as the date"),
        'period_id': fields.many2one('account.period',string='Period', required=True,),
        'journal_id': fields.many2one('account.journal',string='Journal', required=True, domain=[('type','in',('cash', 'bank'))]),
        'note': fields.text('Notes'),
        }

    _defaults = {
        'date': time.strftime('%Y-%m-%d'),
        'period_id': _get_period,
        }

    def create_voucher(self, cr, uid, ids, context={}):
        active_id = context.get('active_id', False)
        wiz = self.browse(cr, uid , ids, context)[0]
        payslip_obj = self.pool.get('hr.payslip')
        payslip = payslip_obj.browse(cr, uid, active_id, context)
        voucher_obj = self.pool.get('account.voucher')
        company = payslip.company_id
        vals_voucher = {
                        'type':'payment',
                        'payslip_id':payslip.id,
                        'amount': payslip.payslip_net,
                        'partner_id': payslip.employee_id.partner_id.id,
                        'period_id': wiz.period_id.id,
                        'journal_id': wiz.journal_id.id,
                        'account_id': wiz.journal_id.default_debit_account_id.id,
                        'company_id' : company.id,
                        'currency_id': company.currency_id.id,
                        'name':payslip.name,
                        'date':wiz.date,
                        }
        
        voucher_id = voucher_obj.create(cr, uid, vals_voucher, context)
        data = voucher_obj.onchange_partner_id(cr, uid, [voucher_id,], payslip.employee_id.partner_id.id, wiz.journal_id.id, payslip.payslip_net, company.currency_id.id, 'payment', wiz.date, context)
        values_voucher = {
                        'account_id' : data['value'].get('account_id', False),
                        'currency_id' : data['value'].get('currency_id', False),
                        'pre_line' : data['value'].get('pre_line', False),
                        'writeoff_amount' : data['value'].get('writeoff_amount', False),
                        'line_ids' : [],
                        'line_dr_ids' : [],
                        'line_cr_ids' : [],
                        }
#        for line_ids in data['value'].get('line_ids',[]):
#            values_voucher['line_ids'].append((0,0,line_ids))
        for line_dr_ids in data['value'].get('line_dr_ids',[]):
            values_voucher['line_dr_ids'].append((0,0,line_dr_ids))
        for line_cr_ids in data['value'].get('line_cr_ids',[]):
            values_voucher['line_cr_ids'].append((0,0,line_cr_ids))
            
        voucher_obj.write(cr, uid, [voucher_id,], values_voucher, context)

        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_payslip_payment_employee_form')])
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        
        return {
            'name': _('Payment of Employee'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.voucher',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': [voucher_id],
            'context': context,
        }
        return {}


wizard_payslip()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: