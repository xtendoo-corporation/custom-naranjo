from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    x_last_payment_date = fields.Date(string='Último Pago', help='Fecha del último pago registrado')
