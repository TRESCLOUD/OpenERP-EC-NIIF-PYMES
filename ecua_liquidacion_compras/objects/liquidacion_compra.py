# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Christopher Ormaza A (<http://www.ecuadorenlinea.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _
import time
import re
from lxml import etree

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _check_number_liquidacion(self,cr,uid,ids):
        cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
        for invoice in self.browse(cr, uid, ids):
            ref = invoice['number_liquidation']
            if invoice['number_liquidation']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
            
    def _get_liquidation_type(self,cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('liquidation', False)

    def onchange_number_liquidation(self, cr, uid, ids, number, automatic, company, shop=None, printer_id=None, context=None):
        result = {}
        if context is None:
            context = {}
        if shop==None:
            shop = self.pool.get('sale.shop').search(cr, uid,[])[0]
        if not number:
            return {'value': {'number_liquidation': ''}}
        if not automatic:
            auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'liquidation', company, shop, number, printer_id, context)
            if not auth['authorization']:
                raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check!'))
            result['authorization_liquidation'] = auth['authorization']
        res_final = {'value':result}
        return res_final

    def onchange_data_liquidation(self, cr, uid, ids, automatic, company_id=None, shop_id=None, type=None, liquidation=False, printer_id=None, date=None, context=None):
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'in_invoice' and liquidation:
                    values['journal_id'] = curr_shop.liquidation_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','liquidation'),('printer_id','=',printer_id),('shop_id','=',curr_shop.id),('state','=',True), ('automatic','!=', manual)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['authorization_liquidation'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'liquidation', False, company_id, curr_shop.id, printer_id, 'account.invoice', 'number_liquidation', context)
                                values['number_liquidation'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                            else:
                                values['number_liquidation'] = curr_shop.number + "-" + printer_obj.browse(cr, uid, printer_id, context).number + "-"
                        else:
                            values['authorization'] = None
                            values['authorization_liquidation'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return {'value': values, 'domain':{'shop_id':[('id','in', shop_ids)]}}

    def action_number(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids, context):
            context['automatic'] = invoice.automatic
            if invoice.type=='in_invoice' and invoice.liquidation:
                if not invoice.authorization_liquidation:
                    raise osv.except_osv(_('Invalid action!'), _('Not exist authorization for the document, please check'))
                if not invoice.automatic:
                    if not invoice.number_liquidation:
                        raise osv.except_osv(_('Invalid action!'), _('Not exist number for the document, please check'))
                    shop = invoice.shop_id.id
                    auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'liquidation', invoice.company_id.id, shop, invoice.number_liquidation, invoice.printer_id.id, context)
                    if not auth['authorization']:
                        raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                    doc_id = document_obj.search(cr, uid, [('name','=','liquidation'),('printer_id','=',invoice.printer_id.id),('shop_id','=',invoice.shop_id.id),('sri_authorization_id','=',invoice.authorization_liquidation.id)])
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [invoice.id], {'invoice_number': invoice.number_liquidation, 'flag': True, 'authorization':invoice.authorization_liquidation.number}, context)
                else:
                    if not invoice.number_liquidation:
                        b = True
                        vals_aut = self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'invoice', invoice.company_id.id, invoice.shop_id.id, invoice.printer_id.id)
                        while b :
                            number_out = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
                            if not self.pool.get('account.invoice').search(cr, uid, [('type','=','in_invoice'),('invoice_number','=',number_out), ('automatic','=',True),('id','not in',tuple(ids))],):
                                b=False
                    else:
                        number_out = invoice.number_liquidation
                    doc_id = document_obj.search(cr, uid, [('name','=','liquidation'),('printer_id','=',invoice.printer_id.id),('shop_id','=',invoice.shop_id.id),('sri_authorization_id','=',invoice.authorization_liquidation.id)])                            
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [invoice.id], {'invoice_number': number_out,'number_liquidation': number_out,'automatic_number': number_out, 'flag': True, 'authorization':invoice.authorization_liquidation.number}, context)
        result = super(account_invoice, self).action_number(cr, uid, ids, context)
        self.write(cr, uid, ids, {'internal_number': False,}, context)
        return result

    def action_cancel_draft(self, cr, uid, ids, *args):
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids):
            if invoice.type=='in_invoice' and invoice.liquidation:
                if invoice.flag:
                    for doc in invoice.authorization_liquidation.type_document_ids:
                        if doc.name=='liquidation':
                            document_obj.rest_document(cr, uid, [doc.id,])
                    self.write(cr, uid, [invoice.id], {'flag': False}, context=None)
            return super(account_invoice, self).action_cancel_draft(cr, uid, ids)

    def action_date_assign(self, cr, uid, ids, *args):
        auth_obj = self.pool.get('sri.authorization')
        date=False
        res = super(account_invoice, self).action_date_assign(cr, uid, ids, args)
        for inv in self.browse(cr, uid, ids):
            if inv.type=='in_invoice' and inv.liquidation:
                if not inv.date_invoice:
                    date = time.strftime('%Y-%m-%d')
                else:
                    date = inv.date_invoice
                if not auth_obj.check_date_document(cr, uid, date, inv.authorization_liquidation.start_date, inv.authorization_liquidation.expiration_date):
                   raise osv.except_osv(_('Invalid action!'), _('The date entered is not valid for the authorization')) 
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}
        type = context.get('type', 'out_invoice')
        if view_type == 'form':
            for field in res['fields']:
                if user.company_id.generate_automatic:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number_liquidation':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number_liquidation']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                else:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number_liquidation':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number_liquidation']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)

        type = context.get('journal_type', 'sale')
        liquidation = context.get('liquidation', False)
        for field in res['fields']:
            if field == 'journal_id':
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', type),('liquidation','=',liquidation)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select

        return res

    def create(self, cr, uid, vals, context=None):
        auth_obj = self.pool.get('sri.authorization')
        if not context:
            context = {}
        if vals.get('number_liquidation', False):
            if context.get('type', False) == 'in' and context.get('liquidation', False):
                vals['automatic_number'] = vals.get('number_liquidation', False)
                if vals.get('authorization_liquidation', False):
                    vals['authorization'] = auth_obj.browse(cr, uid, vals['authorization_liquidation'], context).number
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res

    def copy(self, cr, uid, id, default={}, context=None):
        inv_obj = self.pool.get('account.invoice')
        doc_obj=self.pool.get('sri.type.document')
        original_liquidation = inv_obj.browse(cr, uid, id, context)
        new_number = False
        autorization_number = False
        authorization_id = False
        if original_liquidation:
            if original_liquidation.shop_id:
                if original_liquidation.printer_id:
                    if original_liquidation.company_id:
                        if original_liquidation.type == "in_invoice" and original_liquidation.liquidation:
                            new_number = doc_obj.get_next_value_secuence(cr, uid, 'liquidation', False, original_liquidation.company_id.id, original_liquidation.shop_id.id, original_liquidation.printer_id.id, 'account.invoice', 'number_liquidation', context)
                            authorization_id = original_liquidation.authorization_liquidation.id
                            autorization_number = original_liquidation.authorization_liquidation.number
        if context is None:
            context = {}
        default.update({
            'authorization_liquidation': authorization_id,
            'authorization': autorization_number,
            'number_liquidation':new_number,
            'automatic_number':new_number,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)

    def button_reset_taxes(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context):
            if inv.type == "in_invoice" and inv.liquidation:
                vals = {'automatic_number':inv.number_liquidation}
                if inv.authorization_liquidation:
                    vals['authorization'] = inv.authorization_liquidation.number
                self.write(cr, uid, [inv.id], vals)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
    
    _columns = {
                'number_liquidation':fields.char('Number', size=17, required=False, readonly=True, states={'draft':[('readonly', False)]}),
                'liquidation':fields.boolean('Liquidation'),
                'authorization_liquidation':fields.many2one('sri.authorization', 'Authorization', required=False),
    }
    
    _defaults = {
                 'liquidation':_get_liquidation_type
                 }
    
    _constraints = [(_check_number_liquidacion, _('The number of Liquidation is incorrect, it must be like 001-00X-000XXXXXX, X is a number'),['number_liquidacion'])]
    
    _sql_constraints = [('number_liquidacion_uniq','unique(number_liquidacion, shop_id, printer_id, company_id)', _('There is another Liquidation of Purchases with this number, please check'))]
    
    def default_get(self, cr, uid, fields_list, context=None):
        """
        Returns default values for fields
        @param fields_list: list of fields, for which default values are required to be read
        @param context: context arguments, like lang, time zone

        @return: Returns a dict that contains default values for fields
        """
        if context is None:
            context = {}
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = super(account_invoice, self).default_get(cr, uid, fields_list, context=context)
        if not values:
            values={}
        shop_id = values.get('shop_id', False)
        printer_id = values.get('printer_id', False)
        company_id = values.get('company_id', False)
        automatic = values.get('automatic', False)
        liquidation = values.get('liquidation', False)
        type = values.get('type', False)
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'in_invoice' and liquidation and ('number_liquidation', 'automatic_number') in fields_list:
                    values['journal_id'] = curr_shop.sales_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','liquidation'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['authorization_liquidation'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'liquidation', False, company_id, curr_shop.id, printer_id, 'account.invoice', 'number_liquidation', context)
                                values['number_liquidation'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                        else:
                            values['authorization'] = None
                            values['authorization_liquidation'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return values

account_invoice()