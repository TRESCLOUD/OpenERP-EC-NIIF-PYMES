# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Patricio Rangles                                                                           
# Copyright (C) 2013  TRESCLOUD Cia Ltda.                                 
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

from osv import osv, fields
from tools.translate import _
#from datetime import datetime
import time

class account_invoice(osv.osv):
    """
    Clase que permite crear un pedido de compra a partir de una facturade compra,
    esto con el objetivo de realizar el reembolso de la misma

    El codigo facilita la creacion de ordenes de venta a partir de
    una factura en estado "open" o "paid". Esto esta pensado para ayudar a
    la creacion de facturas para reembolso de gastos permitido por el SRI.
    
    Esta version inicial Permite crear la orden de venta en base a la
    informacion, posibles mejoras son:
    
    - Crear wizard para seleccionar el cliente y la cuenta analitica si se
    desea
    - Filtrado de impuestos de retencion no necesarios
    - Escoger varias facturas y crear las respectivas ordenes de venta de un
    solo click
    - Mostrar un mensaje de informacion al terminar el proceso
    - Mejorar la ubicacion del boton en la vista de la factura
    """
    _inherit = "account.invoice"

    def create_sale_order_from_invoice(self, cr, uid, ids, context=None):
        
        invoice = self.browse(cr, uid, ids[0])
        invoice_lines = invoice.invoice_line 

        obj_sale_order = self.pool.get('sale.order')
        obj_sale_order_line=self.pool.get('sale.order.line')
        partner = self.pool.get('res.partner').browse(cr, uid, 1) # preterminamos la compañia como partner
        address = partner.address[0]
        fecha = invoice.date_invoice

        if not fecha:
            #se setea la fecha actual
            fecha = time.strftime('YYYY-MM-DD')

        sale_id = obj_sale_order.create(cr, uid, {
            'name': "RUC:" + partner.ref + " #:" + invoice.invoice_number_in,
            #'origin': invoice.invoice_number_in,
            'client_order_ref': invoice.partner_id.name,
            'date_order': fecha,
            #'shop_id': 1, # predeterminamos la primera tienda
            #'printer_id': 1, # predeterminamos el primer punto de impresion
            'partner_id': partner.id,
            'partner_order_id': address.id, 
            'partner_invoice_id': address.id, 
            'partner_shipping_id': address.id,
            'pricelist_id': 1, # predeterminamos la primera lista 
            'company_id': invoice.company_id.id,
            'user_id': invoice.user_id.id, 
                })

        for line in invoice_lines:
            
            descripcion = "REEMBOLSO 100% DE GASTO RUC: " + partner.ref + "; FACTURA No. " + invoice.invoice_number_in + "; NETO: " + str(invoice.total_con_impuestos - invoice.total_iva) + ", IVA 0%:" + str(invoice.amount_total - invoice.total_con_impuestos) + ", IVA 12%:" + str(invoice.total_iva)            

            sale_line = obj_sale_order_line.create(cr, uid, {
                    'order_id':sale_id,
                    'name': descripcion, #line.name,
                    'origin': line.invoice_id.name,
                    'price_unit': line.price_unit,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uos_id.id or 1,
                    'discount': line.discount,
                    'product_id': line.product_id.id or False,
                    'tax_id': [(6, 0, [x.id for x in line.invoice_line_tax_id])], 
                    #'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                    'notes': line.note,
                    #'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                })

        return True

account_invoice()
