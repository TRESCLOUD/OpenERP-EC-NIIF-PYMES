##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import time
from datetime import date
from osv import fields,osv
from tools import DEFAULT_SERVER_DATETIME_FORMAT
from trc_mod_python import date_time_zone

class caja_reporte(osv.osv_memory):
    
    _name = 'caja.reporte'

    def _date_format(self, cr, uid, context = None, date=False):
        context = {}
        context.update({'tz': self.pool.get('res.users').browse(cr, uid, uid).context_tz or False})
        if not date:
            date = time.strftime('%Y-%m-%d %H:%M:%S')
        new_date = date_time_zone.offset_format_timestamp(date, "%Y-%m-%d %H:%M:%S", DEFAULT_SERVER_DATETIME_FORMAT, server_to_client=True, context=context)        
        return new_date

    def is_today(self, date_compare, reference):
        """
        This function checks if a giving date falls in the actual date (now)
        """
        
        if not date_compare:
            return False

        return date_compare == reference[0:10]
    
    def onchange_date_user_id(self, cr, uid, ids, date, user_id, context=None):
        #this function make the calculate of every field needed
        # and return the changes to the view
        
        if not context:
            context={}
            
        #asign the value into variable
        context['date_new'] = date
        context['user_id_new'] = user_id
        
        value = {}
        
        value['ovsf_ids'] = self._Ordenes_venta_sin_facturar(cr, uid, context = context)
        value['fsc_ids'] = self._facturas_sin_cancelar(cr, uid, context = context)
        value['cobros_efectivo_cheque'] = self._cobros_efectivo_cheque(cr, uid, context = context)
        value['facturas_emitidas'] = self._facturas_emitidas(cr, uid, context = context)
        value['ordenes_venta_emitidas'] = self._ordenes_venta_emitidas(cr, uid, context = context)
        value['cobros_efec_cheq_consolidado'] = self._cobros_efectivo_cheque_consolidado(cr, uid, context = context)
        
        #asigno la fecha que se ha modificado
        value['date_format'] = self._date_format(cr, uid, context=context, date=date)
        
        return {'value': value}

    def _Ordenes_venta_sin_facturar(self, cr, uid, context = None):
        # the Idea is search in sale.order all rows from this user (id) and
        # load the field. 
        
        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']
            
        #resource to return
        res = []
        
        #This dict is for easy work whit repeats names
        res_dic = {}
        
        sale_orden_obj = self.pool.get('sale.order')
        
        #order by name (represent the number of order of sale)
        list_ids = sale_orden_obj.search(cr, uid, [('state','!=','progress'),
                                                   '&',('state','!=','cancel'),
                                                   ('user_id','=',user_id_to_use),],
                                         order='name')
         
        for orden_sin_factura in sale_orden_obj.browse(cr, uid, list_ids):
        
            #Verify the date
            if self.is_today(orden_sin_factura.date_order, referencia):
                
                temp = {
                    'name': orden_sin_factura.partner_id.name,
                    'sale_number': orden_sin_factura.name,
                    'reference': orden_sin_factura.client_order_ref,
                    'total': orden_sin_factura.amount_total,
                }
        
                res.append(temp)    
 
        return res
    
    def _facturas_sin_cancelar(self, cr, uid, context = None):
        # the Idea is search in account.invoice all rows from this user (id) and
        # load the field. 
        
        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']

        #resource to return
        res = []
        
        #This dict is for easy work whit repeats names
        res_dic = {}
        
        account_invoice_obj = self.pool.get('account.invoice')
        sale_order_obj = self.pool.get('sale.order')
        
        # order by invoice_number
        list_ids = account_invoice_obj.search(cr, uid, [('reconciled','=',False),
                                                        ('state','!=','cancel'),
                                                        ('type','=','out_invoice'),
                                                        ('user_id','=',user_id_to_use),],
                                              order='invoice_number')
         
        for factura_sin_cancelar in account_invoice_obj.browse(cr, uid, list_ids):
        
            #Verify the date
            if self.is_today(factura_sin_cancelar.date_invoice, referencia):
                
                # Add the price list of first sale order related to the invoice
                # in case exist (sale.order.invoice.rel)
                cr.execute('select order_id from sale_order_invoice_rel where invoice_id = ' + str(factura_sin_cancelar.id) + ';')
                sale_orders = cr.fetchall()
                #sale_orders = self.pool.get('sale.order.invoice.rel').search(cr, uid, [('invoice_id','=',factura_sin_cancelar.id)])

                price_list = ''
                
                if len(sale_orders) > 0:
                    price_list = sale_order_obj.browse(cr, uid, sale_orders[0][0]).pricelist_id.name
                
                temp = {
                    'name': factura_sin_cancelar.partner_id.name,
                    'invoice_number': factura_sin_cancelar.invoice_number,
                    'reference': factura_sin_cancelar.name, 
                    'total': factura_sin_cancelar.amount_total,
                    'price_list': price_list,
                }

                res.append(temp)    

        return res

        
    def _cobros_efectivo_cheque(self, cr, uid, context = None):
        # the Idea is search in account.vouchert all rows from this user (id) and
        # load the fields grouping by journal and "Efectivo" and/or "Cheques". 

        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']
        
        #resource to return
        res = []
        
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')

        # first search the account_voucher in state posted, type receip and created by user_id
        voucher_list = voucher_obj.search(cr, uid, [('state','=','posted'),
                                                    ('type','=','receipt'),
                                                    ('create_uid','=',user_id_to_use),],)
                                          #order='journal_id')
        
        voucher_list = tuple(voucher_list)

        # each one contain voucher_lines, search the lines (Could filter using cr or dr type)
        voucher_line_list = voucher_line_obj.search(cr, uid, [('voucher_id','in',voucher_list),],
                                                        order='name')
                                                        
        for lineas in voucher_line_obj.browse(cr, uid, voucher_line_list):
        
            #Verify the date
            if self.is_today(lineas.voucher_id.date, referencia):
                
                temp = {
                    'partner': lineas.partner_id.name,
                    'name': lineas.voucher_id.journal_id.name,
                    'factura': lineas.name,
                    'importe': lineas.amount,
                    'saldo': lineas.amount_original - lineas.amount,
                    'reference': lineas.voucher_id.reference,
                    'memoria': lineas.voucher_id.name,
                 }
                
                res.append(temp)    

        #Order by journal_id
        def __cmpTexto(x, y):
            if x['name'] < y['name']:
                return -1
            elif x['name'] == y['name']:
                return 0
            else:
                return 1
              
        cmp = lambda x,y: __cmpTexto(x, y)
        
        res.sort(cmp)
 
        return res


    def _facturas_emitidas(self, cr, uid, context = None):
        # the Idea is search in account.invoice all rows from this user (id) and
        # load the field, in this case present a list of emiting invoice showing
        # the actual state 

        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']
        
        #resource to return
        res = []
        
        #This dict is for easy work whit repeats names
        res_dic = {}
        
        object_obj = self.pool.get('account.invoice')
        
        list_ids = object_obj.search(cr, uid, [('state','!=','draft'),
                                               ('type','=','out_invoice'),
                                               ('user_id','=',user_id_to_use),],
                                     order='invoice_number,name,state')
         
        #Need a internal id for every client id (name can be the same twice)
        i = 0 
        
        for element in object_obj.browse(cr, uid, list_ids):
        
            #Verify the date
            if self.is_today(element.date_invoice, referencia):
                
                res_dic[i] = {
                    'name': element.partner_id.name,
                    'number': element.invoice_number,
                    'reference': element.name, 
                    'total': element.amount_total,
                    'estado': element.state,
                }
                
                i = i + 1
                
        for elem in res_dic:
            res.append(res_dic[elem])    
 
        return res



    def _ordenes_venta_emitidas(self, cr, uid, context = None):
        # the Idea is search in sale.order all rows from this user (id) and
        # load the field, in this case present a list of emiting sale oreder showing
        # the actual state 

        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']
        
        #resource to return
        res = []
        
        #This dict is for easy work whit repeats names
        res_dic = {}
        
        object_obj = self.pool.get('sale.order')
        
        list_ids = object_obj.search(cr, uid, [('state','!=','draft'),
                                               ('user_id','=',user_id_to_use),],
                                     order='name,state')
         
        #Need a internal id for every client id (name can be the same twice)
        i = 0 
        
        for element in object_obj.browse(cr, uid, list_ids):
        
            #Verify the date
            if self.is_today(element.date_order, referencia):
                
                res_dic[i] = {
                    'name': element.partner_id.name,
                    'reference': element.client_order_ref,
                    'number': element.name,
                    'total': element.amount_total,
                    'tarifa': element.pricelist_id.name,
                    'estado': element.state,
                }
                
                i = i + 1
                
        for elem in res_dic:
            res.append(res_dic[elem])    
 
        return res


    def _cobros_efectivo_cheque_consolidado(self, cr, uid, context = None):
        # the Idea is search in account.vouchert all rows from this user (id) and
        # load the fields grouping by journal and "Efectivo" and/or "Cheques".
        
        user_id_to_use = uid
        referencia = time.strftime('%Y-%m-%d %H:%M:%S')
            
        if 'user_id_new' in context:
            user_id_to_use = context['user_id_new']

        if 'date_new' in context:
            referencia = context['date_new']

        #resource to return
        res = []
        
        #This dict is for easy work whit repeats names
        res_dic = {}
        
        object_obj = self.pool.get('account.voucher')
        
        list_ids = object_obj.search(cr, uid, [('state','=','posted'),
                                               ('create_uid','=',user_id_to_use),],
                                     order='create_uid')
                                                        
        for lineas in object_obj.browse(cr, uid, list_ids):
        
            #Verify the date
            if self.is_today(lineas.date, referencia):
                
                #Group by consumer and sum
                if lineas.journal_id.name in res_dic:

                    temp = res_dic[lineas.journal_id.name]
                    
                    res_dic[lineas.journal_id.name] = {
                        'name': lineas.journal_id.name,
                        'number': temp['number'] + 1,
                        'total': temp['total'] + lineas.amount,
                     }
                    
                #first element
                else:
                    res_dic[lineas.journal_id.name] = {
                        'name': lineas.journal_id.name,
                        'number': 1,
                        'total': lineas.amount,
                        #'tipo': 'cec',
                    }
        
        for elem in res_dic:
            res.append(res_dic[elem])
 
        return res


    _columns = {
        'date_format': fields.char('fecha formato', size=19, required=False),      
        'date': fields.datetime('fecha', required=True),
        'user_id': fields.many2one('res.users', 'Usuario', required=True),
        'shop_id': fields.many2one('sale.shop', 'Tienda', required=True),
        'ovsf_ids': fields.one2many('caja.ordenes.sin.factura', 'caja_id', 'Ordenes de Venta sin facturar', readonly=True),# required=False, domain=[('tipo','=','ov')]),
        'fsc_ids': fields.one2many('caja.factura.sin.pago', 'caja_id', 'Facturas sin cobrar', readonly=True),# required=False, domain=[('tipo','=','fc')]),
        'cobros_efectivo_cheque': fields.one2many('caja.diarios.pagos', 'caja_id', 'Cobros en Efectivo y Cheque', readonly=True),# required=False, domain=[('tipo','=','cec')]),
        #
        'facturas_emitidas': fields.one2many('caja.facturas.emitidas', 'caja_id', 'Facturas Emitidas', readonly=True),# required=False, domain=[('tipo','=','cec')]),
        'ordenes_venta_emitidas': fields.one2many('caja.ordenes.venta.emitidas', 'caja_id', 'Notas de Venta Emitidas', readonly=True),# required=False, domain=[('tipo','=','cec')]),
        'cobros_efec_cheq_consolidado': fields.one2many('caja.diarios.pagos.consolidado', 'caja_id', 'Cobros en Efectivo y Cheque Consolidado', readonly=True),# required=False, domain=[('tipo','=','cec')]),
        
#        'tarjetas_ids': fields.one2many('caja.ordenes.facturas', 'caja_id', 'Cobros Tarjetas', required=False, domain=[('tipo','=','ct')]),
#        'bancos_ids': fields.one2many('caja.ordenes.facturas', 'caja_id', 'Cobros Bancos', required=False, domain=[('tipo','=','cb')]),
#        'retenciones_ids': fields.one2many('caja.ordenes.facturas', 'caja_id', 'Cobros Retenciones', required=False, domain=[('tipo','=','cr')]),
                }
    
    _defaults = { 
        'date_format': _date_format,
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': lambda s, cr, uid, c: uid,
        'ovsf_ids': _Ordenes_venta_sin_facturar,
        'fsc_ids': _facturas_sin_cancelar,
        'cobros_efectivo_cheque': _cobros_efectivo_cheque,
        'facturas_emitidas': _facturas_emitidas,
        'ordenes_venta_emitidas': _ordenes_venta_emitidas,
        'cobros_efec_cheq_consolidado': _cobros_efectivo_cheque_consolidado,
#        'tarjetas_ids': _tarjetas_ids,  
#        'bancos_ids': _bancos_ids,
#        'retenciones_ids': _retenciones_ids,
                 }

#    def imprimir(self, cr, uid, ids, context=None):
#        
#        if context is None:
#            context = {}
#        
#        data = {}
#        data['model'] = 'account.invoice'
#        data['ids'] = context.get('active_ids', False)
#        
#        return {
#               'type': 'ir.actions.report.xml',
#               'report_name': 'caja_reporte',    # the 'Service Name' from the report
#               'datas' : data,
#               'context': context,
#           }

    def imprimir(self, cr, uid, ids, context=None):
        
        # create the data for the report, only when the system print the report
        # use the ids to instance this object and complete the info for the search
        self.write(cr, uid, ids, {'date_format':context['date_format']})
        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'caja_reporte',    # the 'Service Name' from the report
            'datas' : {
                    'model' : 'caja.reporte',    # Report Model
                    'res_ids' : ids
                    }
               }

caja_reporte()

class caja_ordenes_sin_factura(osv.osv_memory):

    _name = 'caja.ordenes.sin.factura'
   
    _columns = {
        'name': fields.char('Cliente', size=256, required=False, readonly=False),
        'sale_number': fields.char('Orden de Venta', size=256, required=False, readonly=False),
        'reference': fields.char('Referencia', size=256, required=False, readonly=False),
        'total': fields.float('Total', digits=(2,5)),
        'caja_id':fields.many2one('caja.reporte', 'Reporte Caja', required=False),

                }

caja_ordenes_sin_factura()

class caja_facturas_sin_pago(osv.osv_memory):

    _name = 'caja.factura.sin.pago'
   
    _columns = {
        'name': fields.char('Cliente', size=256, required=False, readonly=False),
        'invoice_number': fields.char('Facturas', size=256, required=False, readonly=False),
        'reference': fields.char('Descripcion', size=256, required=False, readonly=False),
        'total': fields.float('Total', digits=(2,5)),
        'caja_id': fields.many2one('caja.reporte', 'Reporte Caja', required=False),
        'price_list': fields.char('Lista de Precios', size=256, required=False, readonly=False),
                }

caja_facturas_sin_pago()

class caja_diarios_pagos(osv.osv_memory):

    _name = 'caja.diarios.pagos'
   
    _columns = {
        'partner': fields.char('Cliente', size=256, required=False, readonly=False),
        'name': fields.char('Diario', size=256, required=False, readonly=False),
        'factura': fields.char('Numero de Factura', size=256, required=False, readonly=False),
        'importe': fields.float('Importe', digits=(2,5)),
        'saldo': fields.float('Saldo', digits=(2,5)),
        'caja_id':fields.many2one('caja.reporte', 'Reporte Caja', required=False),
        'reference': fields.char('Referencia', size=256, required=False, readonly=False),
        'memoria': fields.char('Memoria', size=256, required=False, readonly=False),
                }

caja_diarios_pagos()

class caja_facturas_emitidas(osv.osv_memory):

    _name = 'caja.facturas.emitidas'
   
    _columns = {
        'name': fields.char('Cliente', size=256, required=False, readonly=False),
        'number': fields.char('Numero de Factura', size=32, required=False, readonly=False),
        'reference': fields.char('Descripcion', size=256, required=False, readonly=False),
        'total': fields.float('Total', digits=(2,5)),
        'estado': fields.char('Estado', size=32, required=False, readonly=False),
        'caja_id':fields.many2one('caja.reporte', 'Reporte Caja', required=False),
                }

caja_facturas_emitidas()

class caja_ordenes_venta_emitidas(osv.osv_memory):

    _name = 'caja.ordenes.venta.emitidas'
   
    _columns = {
        'name': fields.char('Cliente', size=256, required=False, readonly=False),
        'number': fields.char('Numero de Orden de Venta', size=32, required=False, readonly=False),
        'reference': fields.char('Referencia', size=256, required=False, readonly=False),
        'total': fields.float('Total', digits=(2,5)),
        'estado': fields.char('Estado', size=32, required=False, readonly=False),
        'tarifa': fields.char('Tarifa', size=256, required=False, readonly=False),
        'caja_id':fields.many2one('caja.reporte', 'Reporte Caja', required=False),
                }

caja_ordenes_venta_emitidas()

class caja_diarios_pagos_consolidado(osv.osv_memory):

    _name = 'caja.diarios.pagos.consolidado'
   
    _columns = {
        'name': fields.char('Cliente', size=256, required=False, readonly=False),
        'number': fields.integer('Numero'),
        'total': fields.float('Total', digits=(2,5)),
        'caja_id':fields.many2one('caja.reporte', 'Reporte Caja', required=False),
                }

caja_diarios_pagos_consolidado()

