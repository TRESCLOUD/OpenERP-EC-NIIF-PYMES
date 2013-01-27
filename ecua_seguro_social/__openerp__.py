#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2012-2013 Pablo Vizhnay
#    (<http://www.geoinformatica.org>). All Rights Reserved
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

{
        "name" : "Ecuadorian Human Resources",
        "version" : "1.21",
        "author" : "Pablo Vizhnay - Geoinformatica",
        "website" : "http://www.geoinformatica.org",
        "category" : "Base/Partners",
        "description": """Human Resources for Ecuadorian localisation""",
        "depends" : ['base',
                     'account',
                     'account_voucher',
                     'hr',
                     'hr_payroll',
                     'hr_payroll_account',
                     'hr_contract',
                     'hr_expense',
                     #modulo que controla la asistencia de los colaboradores
                     'hr_holidays',
                     'hr_attendance',
                     'resource',
                     #agregadas dependencias de aeroo reports
                     'report_aeroo',
                     'report_aeroo_ooo',
                     #AGregadas dependencias de contabilidad ecuatoriana
                     'ecua_states',
                     ],
        "init_xml" : [
                        #'data/data_init.xml',
         ],
        "demo_xml" : [
                      #'data/data_init.xml',
                      ],
        "update_xml" : [
                        'data/data_init.xml',
                        'data/salary_estructure.xml',
                        'data/education_area.xml',
                        'data/calendar.xml',
                        'data/company_configuration.xml',
                        'report/report_hr_advances.xml',
                        'report/report_payslip_details.xml',
                        'report/report_payslip_details_group.xml',
                        'report/nomina_general_report.xml',
                        'wizards/payroll_statement_view.xml',
                        'wizards/hr_payroll_payslips_by_employees.xml',
                        'wizards/hr_payroll_contribution_register_report.xml',
                        'wizards/payment_wizard.xml',
                        'views/company_view.xml',
                        'views/employee_view.xml',
                        'views/family_burden_view.xml',
                        'views/holiday_view.xml',
                        'views/education_level_view.xml',
                        'views/contract_view.xml',
                        'views/extra_input_output_view.xml',
                        'views/payslip_line_view.xml',
                        'views/contract_view.xml',
                        'views/payroll_view.xml',
                        'views/calendar_view.xml',
                        'views/voucher_view.xml',
                        'views/advances_view.xml',
                        'workflows/payroll_workflow.xml',
                        'workflows/advances_workflow.xml',
                        'wizards/multi_advances_wizard_view.xml',
                        'security/hr_security.xml',
                        'security/ir.model.access.csv',
                        ],
        "installable": True
}
