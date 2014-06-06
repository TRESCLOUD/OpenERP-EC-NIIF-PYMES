# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 TRESCLOUD Cia. Ltda. (<http://www.trescloud.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from report import report_sxw
from datetime import datetime,timedelta
from tools.translate import _
from tools import DEFAULT_SERVER_DATETIME_FORMAT
from trc_mod_python import date_time_zone

class Parser(report_sxw.rml_parse):
   
    _name = 'caja.reporte.parser'
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                'date_format': self._date_format,
        })
        self.context = context

    def _date_format(self, date):
        context = {}
        context.update({'tz': self.pool.get('res.users').browse(self.cr, self.uid, self.uid).context_tz or False})
        new_date = date_time_zone.offset_format_timestamp(date, "%Y-%m-%d %H:%M:%S", DEFAULT_SERVER_DATETIME_FORMAT, server_to_client=True, context=context)        
        return new_date

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
