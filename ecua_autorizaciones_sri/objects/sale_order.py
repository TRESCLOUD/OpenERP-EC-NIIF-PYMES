# -*- coding: UTF-8 -*- #
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Ecuadorenlinea.net (http://www.ecuadorenlinea.net>). 
#    All Rights Reserved
#    
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
from dateutil.relativedelta import relativedelta
from lxml import etree
from osv import fields, osv
from tools import config
from tools.translate import _

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
                    }
    
    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        if not context:
            context = {}
        v = {}
        d={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        printer_id = None
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            for printer in shop.printer_point_ids:
                printer_id = printer.id
                break
            d['printer_id'] = [('shop_id.id','=',shop.id)]
            v['project_id'] = shop.project_id.id
            v['printer_id'] = printer_id
            if shop.pricelist_id.id:
                v['pricelist_id'] = shop.pricelist_id.id
        return {'value': v, 'domain':d}

    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        values = super(sale_order, self).default_get(cr, uid, fields_list, context)
        shop_id = None
        printer_id = None
        if user.printer_default_id:
            shop_id = user.printer_default_id.shop_id.id
            printer_id = user.printer_default_id.id
        if not shop_id:
            for shop in user.shop_ids:
                shop_id = shop.id
                for printer in shop.printer_point_ids:
                    printer_id = printer.id
                    continue
                continue
        if not shop_id or not printer_id:
            raise osv.except_osv('Error!', _("Your User doesn't have shops assigned to make sales order"))
        values.update({
                       'shop_id':shop_id,
                       'printer_id': printer_id,
                       })
        return values

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        shop_obj = self.pool.get('sale.shop')
        shop_ids = [shop.id for shop in user.shop_ids]
        domain_shop = [('id','in', shop_ids)]
        res = super(sale_order, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form' and uid != 1:
            for field in res['fields']:
                if field == 'shop_id':
                    doc = etree.XML(res['arch'])
                    nodes = doc.xpath("//field[@name='shop_id']")
                    for node in nodes:
                        node.set('widget', "selection")
                        node.set('domain', str(domain_shop))
                    res['arch'] = etree.tostring(doc)
                    shop_selection = shop_obj._name_search(cr, uid, '', [('id', 'in', shop_ids)], context=context, limit=None, name_get_uid=uid)
                    res['fields']['shop_id']['selection'] = shop_selection
        return res           

sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: