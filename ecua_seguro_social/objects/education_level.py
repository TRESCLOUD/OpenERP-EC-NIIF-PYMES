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

class hr_education_area(osv.osv):
        _name = 'hr.education.area'
        _columns = {
                    'name':fields.char('Name', size=255, ), 
                        } 
hr_education_area()

class hr_education_level(osv.osv):
    _name="hr.education.level"
    _columns = {
                    'title':fields.char('Title', size=255, ),
                    'country_id':fields.many2one('res.country', 'Country', required=False),
                    'institution':fields.char('Institution', size=255, ),
                    'start_date': fields.date('Start Date'),  
                    'end_date': fields.date('End Date'),
                    'at_present':fields.boolean('At present?',), 
                    'level':fields.selection([
                        ('primary','Primary education'),
                        ('secondary','Secondary education'),
                        ('higher','Higher education'),
                        ('bachelor',"Bachelor's"),
                        ('master',"Master's"),
                        ('phd',"Ph.D."),
                         ],    'Education Level', select=True, ),
                    'status':fields.selection([
                        ('graduated','Graduated'),
                        ('ongoing','Ongoing'),
                        ('abandoned','Abandoned'),
                        ],    'State', select=True,),
                    'education_area_id':fields.many2one('hr.education.area', 'Education Area', ),
                    'employee_id':fields.many2one('hr.employee', 'Employee',), 
                    }
    
    _rec_name="title"
    
hr_education_level()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
