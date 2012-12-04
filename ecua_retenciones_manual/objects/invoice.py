# -*- coding: UTF-8 -*- #
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

from osv import fields,osv
import time
from tools.translate import _
import netsvc

class account_invoice(osv.osv):
    
    _inherit = "account.invoice"
    _columns = {
                'retention_ids':fields.one2many('account.retention', 'invoice_id', 'Retention', states={'paid':[('readonly',True)]}),      
                'retention_line_ids':fields.one2many('account.retention.line', 'invoice_id', 'Retention Lines', states={'paid':[('readonly',True)]}),      
               }

    def action_date_assign(self, cr, uid, ids, *args):
        ret_line_obj = self.pool.get('account.retention.line')
        date=False
        res = super(account_invoice, self).action_date_assign(cr, uid, ids, args)
        for inv in self.browse(cr, uid, ids):
            if inv.type=='in_invoice':
                if inv.retention_line_ids:
                    if not inv.date_invoice:
                        date = time.strftime('%Y-%m-%d')
                    else:
                        date = inv.date_invoice
                    for ret_line in inv.retention_line_ids:
                        ret_line_obj.write(cr, uid, ret_line.id, {'creation_date':date})
        return res

    def action_number(self, cr, uid, ids, context=None):
        context = {}
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids):
            if inv.type in ('in_invoice'):
               if (inv['retention_ids']):
                   wf_service.trg_validate(uid, 'account.retention', inv['retention_ids'][0]['id'], 'approve_signal', cr)
        return super(account_invoice, self).action_number(cr, uid, ids, context)
    

    def button_reset_taxes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('account.invoice.tax')
        for id in ids:
            #if not self.pool.get('account.invoice').browse(cr, uid, id, context).invoice_line:
            #    raise osv.except_osv(_('Invalid action !'), _('You must enter at least one invoice line'))
            cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
            partner = self.browse(cr, uid, id, context=ctx).partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})
            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
                ait_obj.create(cr, uid, taxe)
        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
        
        inv_obj = self.pool.get('account.invoice')
        tax_obj = self.pool.get('account.invoice.tax')
        ret_obj = self.pool.get('account.retention')
        ret_line= self.pool.get('account.retention.line')
        seq_obj = self.pool.get('ir.sequence')
        invoice = inv_obj.browse(cr, uid, ids, context)
            
        for inv in invoice:
            cr.execute("DELETE FROM account_retention_line WHERE invoice_id=%s", (inv.id,))
            if (inv['type'] in ('in_invoice','in_refund')):
                if not (inv['retention_ids']):
                    #crear retencion
                    vals_aut=self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'withholding')
                    user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
                    vals_ret={
                              'creation_date': inv['date_invoice'],
                              'transaction_type':'automatic',
                              'invoice_id':inv['id'],
                              'authorization_purchase':vals_aut['authorization'],
                              }
                    ret_id = ret_obj.create(cr, uid, vals_ret, context)
                    
                    #creamos las lineas de retenciones
                    contador_impuestos = 0
                    for tax_line in inv.tax_line:
                        fiscalyear_id = None
                        if not inv['period_id']:
                            period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',time.strftime('%Y-%m-%d')),('date_stop','>=',time.strftime('%Y-%m-%d')),])
                            if period_ids:
                                fiscalyear_id= self.pool.get('account.period').browse(cr, uid, [period_ids[0]], context)[0]['fiscalyear_id']['id']
                        else:
                            fiscalyear_id = inv['period_id']['fiscalyear_id']['id']
                        if (tax_line['tax_amount']< 0):
                            contador_impuestos = contador_impuestos + 1
                            porcentaje= (float(tax_line['tax_amount']/tax_line['base']))*(-100)
                            tax_id = tax_line['tax_code_id']['id']
                            if tax_line['type_ec'] == 'renta':
                                tax_id = tax_line['base_code_id']['id']                            
                            vals_ret_line = {'tax_base':tax_line['base'] ,
                                             'fiscalyear_id':fiscalyear_id,
                                             'retention_id':ret_id,
                                             'description': tax_line['type_ec'],
                                             'tax_id': tax_id
                                             }
                            ret_line_id = ret_line.create(cr, uid, vals_ret_line, context)
                        elif tax_line['tax_amount'] == 0 and tax_line['type_ec'] == 'renta':
                            vals_ret_line = {'tax_base':tax_line.base,
                                             'fiscalyear_id':fiscalyear_id,
                                             'invoice_without_retention_id': inv.id,
                                             'description': tax_line.type_ec,
                                             'tax_id': tax_line.base_code_id.id,
                                             'creation_date_invoice': inv.date_invoice,
                                             }
                            ret_line_id = ret_line.create(cr, uid, vals_ret_line, context)
                    if(contador_impuestos<=0):
                        ret_obj.unlink(cr, uid, [ret_id], context)
                else:
                    ret_actual = ret_obj.read(cr, uid, inv['retention_ids'][0]['id'], context)
                    # actualizar retencion
            
                    cr.execute("DELETE FROM account_retention_line WHERE retention_id=%s", (ret_actual['id'],))                    
                        #actualizamos las lineas de retenciones
                    contador_impuestos = 0
                    
                    for tax_line in inv.tax_line:
                        fiscalyear_id = None
                        if not inv['period_id']:
                            period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',time.strftime('%Y-%m-%d')),('date_stop','>=',time.strftime('%Y-%m-%d')),])
                            if period_ids:
                                fiscalyear_id= self.pool.get('account.period').browse(cr, uid, [period_ids[0]], context)[0]['fiscalyear_id']['id']
                        else:
                            fiscalyear_id = inv['period_id']['fiscalyear_id']['id']
                        if (tax_line['tax_amount']< 0):
                            contador_impuestos = contador_impuestos + 1
                            porcentaje= (float(tax_line['tax_amount']/tax_line['base']))*(-100)
                            tax_id = tax_line['tax_code_id']['id']
                            if tax_line['type_ec'] == 'renta':
                                tax_id = tax_line['base_code_id']['id']
                            vals_ret_line = {'tax_base':tax_line['base'] ,
                                                 'fiscalyear_id':fiscalyear_id,
                                                 'retention_id':ret_actual['id'],
                                                 'description': tax_line['type_ec'],
                                                 'tax_id': tax_id
                                                 }
                            ret_line_id = ret_line.create(cr, uid, vals_ret_line, context)
                        elif tax_line['tax_amount'] == 0 and tax_line['type_ec'] == 'renta':
                            vals_ret_line = {'tax_base':tax_line['base'] ,
                                             'fiscalyear_id':fiscalyear_id,
                                             'invoice_without_retention_id': inv.id,
                                             'description': tax_line['type_ec'],
                                             'tax_id': tax_line['base_code_id']['id'],
                                             'creation_date_invoice': inv.date_invoice,
                                             }
                            ret_line_id = ret_line.create(cr, uid, vals_ret_line, context)
                    if(contador_impuestos<=0):
                        ret_obj.unlink(cr, uid, [ret_actual['id']], context)
                                
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
    
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'retention_ids':[],
            'retention_line_ids':[],

        })

        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def action_cancel(self, cr, uid, ids, *args):
        ret_line_obj = self.pool.get('account.retention.line')
        context={}
        wf_service = netsvc.LocalService("workflow")
        invoices = self.pool.get('account.invoice').browse(cr, uid, ids, context)
        for inv in invoices:
            if inv.retention_ids:
                retencion = inv.retention_ids[0]
                if retencion.state == 'approved':
                    wf_service.trg_validate(uid, 'account.retention', retencion.id, 'canceled_signal', cr)
                self.pool.get('account.retention').unlink(cr, uid, [retencion.id, ], context={'invoice':True})
                   #TODO: Se debe verificar que la retencion que tiene la factura este aprobada
            if inv.retention_line_ids:
                for ret_line in inv.retention_line_ids:
                    ret_line_obj.unlink(cr, uid, [ret_line.id])
        return super(account_invoice, self).action_cancel(cr, uid, ids, context)
account_invoice()

