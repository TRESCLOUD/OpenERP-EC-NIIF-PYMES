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

from osv import fields, osv
from tools import config
from tools.translate import _

class resource_calendar_interval(osv.osv):
    _name = 'resource.calendar.interval'
    _columns = {
                'name':fields.char('Description', size=64, required=True),
                'code':fields.char('Code', size=64, required=True),
                'hour_from' : fields.float('Work from', size=8, required=True, help="Working time will start from"),
                'hour_to' : fields.float("Work to", size=8, required=True, help="Working time will end at"),
                #'calendar_ids':fields.many2one('resource.calendar', 'Resource Calendar'),
                'calendar_ids':fields.many2many('resource.calendar', 'resource_calendar_interval_rel', 'interval_id', 'calendar_id', 'Hours Interval'), 
                
                    } 
resource_calendar_interval()

class resource_calendar(osv.osv):
    _inherit = 'resource.calendar'
    _columns = {
                'calendar_inverval_ids':fields.many2many('resource.calendar.interval', 'resource_calendar_interval_rel', 'calendar_id', 'interval_id', 'Hours Interval'), 
                #'calendar_inverval_ids':fields.one2many('resource.calendar.interval', 'calendar_id', 'Hours Intervals', ),
                    }
    
    def working_hours_on_day(self, cr, uid, resource_calendar_id, day, context=None):
        """
        @param resource_calendar_id: resource.calendar browse record
        @param day: datetime object
        @return: returns the working hours (as float) men should work on the given day if is in the attendance_ids of the resource_calendar_id (i.e if that day is a working day), returns 0.0 otherwise
        """
        res = 0.0
        for working_day in resource_calendar_id.attendance_ids:
            if (int(working_day.dayofweek) + 1) == day.isoweekday():
                res += working_day.hour_to - working_day.hour_from
        return res
resource_calendar()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: