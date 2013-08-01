# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Yumbillo                                                                         
# Copyright (C) 2013  TRESCLOUD CIA. LTDA.                                  
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
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  
########################################################################

{
        "name" : "Countries",
        "author" :  "TRESCLOUD CIA. LTDA.",
        "maintainer": 'TRESCLOUD CIA. LTDA.',
        "website" : "http://www.trescloud.com",        
        'complexity': "easy",
        "description": """Módulo que agrega a cada pais un código asignado por la legislación ecuatoriana e indica si tiene un convenio de doble tributación.
                          Observación: Hay que ejecutar mediante base de datos el script que se encuentra en data/country_code_script.sql""",
        "category" : "Ecuadorian Legislation",   
        "version" : "1.0",
        "depends" : ['base',],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : ['ecua_countries_view.xml',
                         ],
        "installable": True
}