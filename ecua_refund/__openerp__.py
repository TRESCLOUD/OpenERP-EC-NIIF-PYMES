#########################################################################
# Copyright (C) 2013  Patricio Rangles, Trescloud Cia. Ltda.            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "Ecuadorian SRI Refund",
    "version" : "1.0",
    "author" : "Trescloud Cia. Ltda.",
    "website" : "http://www.trescloud.com/",
    "category" : "Ecuadorian SRI Personalization",
    "depends" : ['base',
                 'account_voucher',
                 ],
    "description": """ This module add improvements in account voucher used to register spends, 
    this help in the process of SRI refund
    
    Author:
    Patricio Rangles
    """,
    "init_xml": [],
    "update_xml": [
            'views/voucher_view.xml',
                    ],
    "installable": True,
    "active": False,
}