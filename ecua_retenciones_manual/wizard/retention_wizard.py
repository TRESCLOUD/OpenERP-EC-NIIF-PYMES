# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Ecuadorenlinea.net                                #
#            (Christopher Ormaza)                                       #
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

from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time
import netsvc
import re
from lxml import etree

class retention_wizard(osv.osv_memory):
    
    def _check_number(self, cr, uid, ids):
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        for obj in self.browse(cr, uid, ids):
            ref = obj['number']
            if obj['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True

    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic

    def _get_shop(self, cr, uid, context=None):
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        shop_id = None
        if curr_user:
            if not curr_user.shop_ids:
                if uid != 1:
                    raise osv.except_osv('Error!', _("Your User doesn't have shops assigned"))
            for shop in curr_user.shop_ids:
                shop_id = shop.id
                break
            if curr_user.printer_default_id and curr_user.printer_default_id.shop_id:
                printer_id = curr_user.printer_default_id.shop_id.id
        return shop_id
    
    def _get_printer(self, cr, uid, context=None):
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        printer_id = None
        if curr_user:
            if not curr_user.shop_ids:
                if uid != 1:
                    raise osv.except_osv('Error!', _("Your User doesn't have shops assigned"))
            for shop in curr_user.shop_ids:
                printer_id = shop.printer_point_ids[0].id
                break
            if curr_user.printer_default_id:
                printer_id = curr_user.printer_default_id.id
        return printer_id

    _name = 'account.retention.wizard'
    _columns = {
                'partner_id':fields.many2one('res.partner', 'Partner', ),
                'number':fields.char('Number', size=17,),
                'automatic_number':fields.char('Number', size=17, readonly=True),
                'creation_date': fields.date('Creation Date'),
                'authorization':fields.char('Autorización', size=10, required=False, readonly=True),
                'authorization_purchase':fields.many2one('sri.authorization', 'Authorization', required=False),
                'authorization_purchase_helper':fields.many2one('sri.authorization', 'Authorization', required=False),
                'authorization_sale':fields.char('Authorization', size=10, help='This Number is necesary for SRI reports'),
                'authorization_sale_id':fields.many2one('sri.authorization.supplier', 'Authorization', ),
                'shop_id':fields.many2one('sale.shop', 'Shop'),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point',),
                'invoice_id': fields.many2one('account.invoice', 'Number of Invoice', readonly=True),
                'automatic':fields.boolean('Automatic', required=True),
                'type':fields.selection([
                                    ('automatic', 'Automatic'),
                                    ('manual', 'Manual'),
                                    ], 'type', required=True, readonly=True),
                'lines_ids': fields.one2many('account.retention.wizard.line', 'wizard_id', 'Retention line'),
                'description':fields.char(u'Concepto de Retencion', size=255, required=False, readonly=False), 
                }
    _constraints = [(_check_number, _('The number is incorrect, it must be like 001-00X-000XXXXXX, X is a number'), ['number'])]

    def onchange_number_purchase(self, cr , uid, ids, number, printer_id, date, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        warning = {}
        auth_obj = self.pool.get('sri.authorization')
        doc_obj = self.pool.get('sri.type.document')
        if not date:
            date = time.strftime('%Y-%m-%d')
        if number and printer_id:
            auth_data = auth_obj.check_if_seq_exist(cr, uid, 'withholding', number, printer_id, date, context)
            authorization = auth_data and auth_obj.browse(cr, uid, auth_data['authorization'], context) or None
            if authorization and auth_data['document_type_id']:
                value['authorization'] = authorization.number
                value['authorization_purchase'] = authorization.id
                value['number'] = doc_obj.complete_number(cr, uid, auth_data['document_type_id'], number)
        return {'value': value, 'domain': domain,'warning': warning }
    
    def onchange_number(self, cr, uid, number, partner_id=None, date=None, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        warning = {}
        auth_supplier_obj = self.pool.get('sri.authorization.supplier')
        if not date:
            date = time.strftime('%Y-%m-%d')
        if number:
            auth_data = auth_supplier_obj.get_supplier_authorizations(cr, uid, number, "withhold", partner_id, date)
            if not auth_data.get('auth_ids', []):
                warning = {
                           'title': _(u'Advertencia!!!'),
                           'message':auth_data.get('message',''),
                           }
                return {'value': values, 'domain':domain, 'warning': warning}
            if auth_data.get('multi_auth', False):
                values = {
                         'number' : ""
                         }
                warning = {
                           'title': _(u'Advertencia!!!'),
                           'message':auth_data.get('message',''),
                           }
                return {'value': values, 'domain':domain, 'warning': warning}
            else:
                auth_id = auth_data.get('auth_ids', []) and auth_data.get('auth_ids', [])[0] or None
                if auth_id:
                    values = {
                             'number' : auth_data.get('res_number', ''),
                             'authorization_sale': auth_id,
                             }            
        return {'value': value, 'domain': domain,'warning': warning }

    def onchange_authorization_supplier(self, cr, uid, ids, authorization, number, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if authorization and not number:
            auth = self.pool.get('sri.authorization.supplier').browse(cr, uid, authorization, context)
            number = auth and auth.agency + "-" + auth.printer_point+"-"
            value['number'] = number or ''
        return {'value': value, 'domain': domain }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        values = {}
        res = []
        doc_obj = self.pool.get('sri.type.document')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for invoice in self.pool.get(context['active_model']).browse(cr , uid, context['active_ids']):
            date_invoice = invoice.date_invoice or time.strftime('%Y-%m-%d')
            values = {
                     'partner_id': invoice.partner_id.id,
                     'invoice_id': invoice.id,
                     'creation_date': date_invoice,
                     'shop_id':self._get_shop(cr, uid, context),
                     'printer_id':self._get_printer(cr, uid, context),
                    }
            if invoice.type == 'out_invoice':
                values['type'] = 'manual'
            if invoice.type in ('in_invoice'):
                for ret in invoice.retention_ids:
                    for line in ret.retention_line_ids:
                        values_lines = {'fiscalyear_id':line.fiscalyear_id.id,
                                  'description': line.description,
                                  'tax_id': line.tax_id.id,
                                  'tax_base': line.tax_base,
                                  'retention_percentage': line.retention_percentage
                                  }
                        res.append(values_lines)
                    printer_id = self._get_printer(cr, uid, context)
                    shop_id = self._get_shop(cr, uid, context)
                    auth_line_id = doc_obj.search(cr, uid, [('name','=','withholding'), ('printer_id','=',printer_id), ('shop_id','=',shop_id)])
                    if not auth_line_id:
                        raise osv.except_osv(_('Error!'), _('No existe autorización para generar retenciones'))
                    auth = doc_obj.browse(cr, uid, auth_line_id[0], context) or None
                    auth_number = auth.sri_authorization_id.number
                    auth_id = auth.sri_authorization_id.id
                    if ret.number_purchase and ret.authorization_purchase:
                        auth_id = ret.authorization_purchase.id
                        auth_number = ret.authorization_purchase.number
                    number_retention = ret.number_purchase or doc_obj.get_next_value_secuence(cr, uid, 'withholding', False, user.company_id.id ,self._get_shop(cr, uid, context), self._get_printer(cr, uid, context), 'account.retention', 'number_purchase', context) 
                    values.update({
                             'number': number_retention,
                             'creation_date': ret.creation_date or date_invoice,
                             'type': 'automatic',
                             'description': ret.description,
                             'authorization': auth_number,
                             'authorization_purchase': auth_id,
                             'lines_ids': res,
                            })
        return values
    
    def onchange_data(self, cr, uid, ids, automatic, shop_id=None, printer_id=None, context=None):
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj = self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual', False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id, ], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if printer_id:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','withholding'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True),])
                if auth_line_id:
                    values['authorization_purchase'] = doc_obj.browse(cr, uid, auth_line_id[0], context).sri_authorization_id.id
                    if automatic:
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'withholding', False, company_id, curr_shop.id, printer_id, 'account.retention', 'number_purchase', context)
                        values['number'] = values['automatic_number']
                        values['creation_date'] = time.strftime('%Y-%m-%d')
                else:
                    values['authorization_purchase'] = None
                    values['automatic'] = False
                    values['creation_date'] = None
        return {'value': values, 'domain':{'shop_id':[('id', 'in', shop_ids)]}}
  

    def onchange_aut_sale(self, cr, uid, ids, authorization_sale_id , context=None):
        
        doc_obj=self.pool.get('sri.authorization.supplier')
        values = {}

        if context is None:
            context = {}
        
        if authorization_sale_id is None:
            return True

        authorization = doc_obj.browse(cr, uid, authorization_sale_id, context)
        
        values['number'] = authorization.agency + "-" + authorization.printer_point + "-"

        return {'value': values}
 
    
    def create_retention(self, cr, uid, ids, context=None):
        if not context:
	       context = {}
        retention_obj = self.pool.get('account.retention')
        retention_line_obj = self.pool.get('account.retention.line')
        auth_s_obj = self.pool.get('sri.authorization.supplier')
        
        ret_vals = {}
        ret_line_vals = {}
        objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_ids'])[0]
        for retention in self.browse(cr, uid, ids, context):
            if not retention.number:
                raise osv.except_osv(_('Error!'), _('Number to be entered to approve the retention'))
            if not retention.creation_date:
                raise osv.except_osv(_('Error!'), _('Date to be entered to approve the retention'))
            if not retention.authorization_sale_id:
                raise osv.except_osv(_('Error!'), _('Authorization to be entered to approve the retention'))
            if not retention.lines_ids:
                raise osv.except_osv(_('Error!'), _('must enter at least one tax to approve the retention'))
            number = None
            auth_id = None
            if retention.authorization_sale_id:
                auth_s_obj.check_number_document(cr, uid, retention.number, retention.authorization_sale_id, retention.creation_date, 'account.retention', 'number', _('Withholding') ,context)
                number = retention.authorization_sale_id.number
                auth_id = retention.authorization_sale_id.id
            ret_vals = {
                 'number_sale':retention.number,
                 'creation_date': retention.creation_date,
                 'transaction_type': 'manual',
                 'authorization_sale': number,
                 'authorization_sale_id': auth_id,
                 'invoice_id': retention.invoice_id.id,
                 'description': retention.description,
                 'period_id': objs.period_id.id
                 }
            retention_id = retention_obj.create(cr, uid, ret_vals, context)
            for line in retention.lines_ids:
                ret_line_vals = {
                     'retention_id':retention_id,
                     'fiscalyear_id':line.fiscalyear_id.id,
                     'description': line.description,
                     'tax_base': line.tax_base,
                     'retention_percentage_manual': line.retention_percentage,
                     }
                retention_line_obj.create(cr, uid, ret_line_vals, context)
        return retention_id
    
    def approve_now(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        retention = self.create_retention(cr, uid, ids, context)
        wf_service.trg_validate(uid, 'account.retention', retention, 'approve_signal', cr)
        return {'type': 'ir.actions.act_window_close'}
    
    def approve_late(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        invoice = self.pool.get(context['active_model']).browse(cr , uid, context['active_id'])
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.type == 'manual':
                retention = self.create_retention(cr, uid, ids, context)
            if obj.type == 'automatic':
                if not obj.creation_date:
                    raise osv.except_osv(_('Error!'), _('Date to be entered to approve the retention'))
                if not obj.automatic:
                    if not obj.number:
                        raise osv.except_osv(_('Error!'), _('number to be entered to approve the retention'))
#                 auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'withholding', user.company_id.id, obj.shop_id.id, obj.number, obj.shop_id.id, context)
#                 if not auth['authorization']:
#                     raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                self.pool.get('account.retention').write(cr, uid, [invoice.retention_ids[0].id, ], {'number_purchase':obj.number}, context)
                self.pool.get('account.retention').write(cr, uid, [invoice.retention_ids[0].id, ], {'creation_date': obj.creation_date, 'authorization_purchase': obj.authorization_purchase.id, 'shop_id':obj.shop_id.id, 'printer_id':obj.printer_id.id}, context)
        return {'type': 'ir.actions.act_window_close'}
    
    def button_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

retention_wizard()

class retention_wizard_line(osv.osv_memory):
    _name = "account.retention.wizard.line"
    
    _columns = {
            'wizard_id': fields.many2one('account.retention.wizard', 'wizard'),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
            'description': fields.selection([('iva', 'IVA'), ('renta', 'RENTA'), ], 'Impuesto'),
            'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account')),
            'retention_percentage': fields.float('Percentaje Value', digits_compute=dp.get_precision('Account')),
            'total_withholding': fields.float('Total Withholding', digits_compute=dp.get_precision('Account')), 
            'tax_id':fields.many2one('account.tax.code', 'Tax Code'),
            }
    
    def onchange_base(self, cr, uid, ids, base, percentage, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if base and percentage:
            value['total_withholding'] = base * (percentage/100)
        else:
            value['total_withholding'] = 0
        return {'value': value, 'domain': domain }
    
retention_wizard_line()
