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

from report import report_sxw
from lxml import etree

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context)
        nomina_obj = self.pool.get('hr.payslip.run')
        ids = context['active_id']
        nomina = nomina_obj.browse(cr, uid, ids, context)
        lineas_nomina = nomina.slip_ids
        ingresos = []
        egresos = []
        lineas_roles = []
        for rol in lineas_nomina:
            for linea in rol.line_ids:
                lineas_roles.append(linea)
        for line in lineas_roles:
            if line.salary_rule_id:
                if line.salary_rule_id.category_id.type == 'input' and line.salary_rule_id.category_id.code != 'CONT':
                    ingresos.append(line)
                if line.salary_rule_id.category_id.type == 'output' and line.salary_rule_id.category_id.code != 'CONT':
                    egresos.append(line)
            if line.extra_i_o_id:
                if line.extra_i_o_id.category_id.type == 'input' and line.extra_i_o_id.category_id.code != 'CONT':
                    ingresos.append(line)
                if line.extra_i_o_id.category_id.type == 'output' and line.extra_i_o_id.category_id.code != 'CONT':
                    egresos.append(line)
        self.localcontext.update({
            'nomina': nomina,
            'lineas_nomina': lineas_nomina,
            'ingresos': ingresos,
            'egresos':egresos,            
        })
