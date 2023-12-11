from odoo import models


class PosSession(models.Model):
    """Load models and fields"""
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        """Loading the EFRIS authentication fields into POS from
         res.company model"""
        result = super()._loader_params_res_company()
        result['search_params']['fields'].extend(
            ["efris_enable", "login_tin", "login_password",
             "device_no", "api_url", "tax_payer_id", "legal_name",
             "business_name", "business_place", "branch_id",
             "branch_code", "branch_name", "credit_max",
             "is_authenticated"])

        return result
